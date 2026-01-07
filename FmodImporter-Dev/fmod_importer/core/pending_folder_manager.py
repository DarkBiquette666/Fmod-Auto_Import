"""Pending folder management for FMOD project.

Manages folders that are staged but not yet committed to XML files.
Provides transaction-like semantics for folder creation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple

from .xml_writer import write_pretty_xml


class PendingFolderManager:
    """Manages pending (uncommitted) event, asset, bank, and bus folders."""

    def __init__(self):
        """Initialize the pending folder manager."""
        self._pending_event_folders = {}
        self._pending_asset_folders = {}
        self._pending_banks = {}
        self._pending_buses = {}

    def add_event_folder(self, folder_id: str, folder_data: Dict):
        """Add an event folder to the pending list."""
        self._pending_event_folders[folder_id] = folder_data

    def add_asset_folder(self, asset_id: str, folder_data: Dict):
        """Add an asset folder to the pending list."""
        self._pending_asset_folders[asset_id] = folder_data

    def add_bank(self, bank_id: str, bank_data: Dict):
        """Add a bank or bank folder to the pending list."""
        self._pending_banks[bank_id] = bank_data

    def add_bus(self, bus_id: str, bus_data: Dict):
        """Add a bus to the pending list."""
        self._pending_buses[bus_id] = bus_data

    def commit_all(self, event_folders_dict: Dict, asset_folders_dict: Dict,
                   banks_dict: Dict, buses_dict: Dict,
                   workspace: Dict, metadata_path: Path) -> Tuple[int, int, int, int]:
        """
        Commit all pending items to XML files.

        Args:
            event_folders_dict: Dictionary of committed event folders
            asset_folders_dict: Dictionary of committed asset folders
            banks_dict: Dictionary of committed banks
            buses_dict: Dictionary of committed buses
            workspace: Workspace dictionary
            metadata_path: Path to Metadata directory

        Returns:
            Tuple of committed counts: (events, assets, banks, buses)
        """
        counts = {'event': 0, 'asset': 0, 'bank': 0, 'bus': 0}
        committed_ids = {'event': [], 'asset': [], 'bank': [], 'bus': []}

        try:
            # Phase 1: Event Folders (Topological Sort)
            counts['event'] = self._commit_hierarchical(
                self._pending_event_folders, event_folders_dict, committed_ids['event'],
                workspace.get('masterEventFolder'), metadata_path / "EventFolder",
                "EventFolder", "folder"
            )

            # Phase 2: Asset Folders (Simple)
            for asset_id, folder_data in self._pending_asset_folders.items():
                root = ET.Element('objects', serializationModel="Studio.02.02.00")
                obj = ET.SubElement(root, 'object', {'class': 'EncodableAsset', 'id': asset_id})
                
                prop = ET.SubElement(obj, 'property', name='assetPath')
                ET.SubElement(prop, 'value').text = folder_data['path']
                
                rel = ET.SubElement(obj, 'relationship', name='masterAssetFolder')
                ET.SubElement(rel, 'destination').text = folder_data['master_folder']

                asset_file = metadata_path / "Asset" / f"{asset_id}.xml"
                asset_file.parent.mkdir(exist_ok=True)
                write_pretty_xml(root, asset_file)

                folder_data['xml_path'] = asset_file
                asset_folders_dict[asset_id] = folder_data
                committed_ids['asset'].append(asset_id)
                counts['asset'] += 1

            # Phase 3: Banks (Topological Sort)
            # Banks can be folders or banks. Master bank folder is root.
            counts['bank'] = self._commit_banks(
                self._pending_banks, banks_dict, committed_ids['bank'],
                workspace.get('masterBankFolder'), metadata_path
            )

            # Phase 4: Buses (Topological Sort)
            # Master bus (parent=None) is root.
            counts['bus'] = self._commit_buses(
                self._pending_buses, buses_dict, committed_ids['bus'],
                metadata_path
            )

            # Clear all pending
            self.clear_all()

            return (counts['event'], counts['asset'], counts['bank'], counts['bus'])

        except Exception as e:
            # Rollback logic would go here (complex to implement fully safely)
            # For now, we rely on the fact that file writes are atomic enough
            # and incomplete XMLs are better than no XMLs if we crash mid-way.
            raise RuntimeError(f"Failed to commit pending items: {e}")

    def _commit_hierarchical(self, pending_items: Dict, committed_dict: Dict, 
                           committed_list: list, master_id: str, 
                           folder_path: Path, class_name: str, 
                           parent_rel_name: str) -> int:
        """Helper for committing hierarchical items (Events, Folders)."""
        count = 0
        items = list(pending_items.items())
        
        while items:
            made_progress = False
            remaining = []

            for item_id, data in items:
                parent_id = data.get('parent')
                
                # Parent is committed if:
                # 1. It's in the committed dictionary
                # 2. It's in the list of items just committed in this batch
                # 3. It's the master/root ID
                # 4. It's None (for items that can be at root level, like Master Bus)
                is_ready = (parent_id is None or
                           parent_id in committed_dict or 
                           parent_id in committed_list or 
                           parent_id == master_id)

                if is_ready:
                    # Create XML
                    root = ET.Element('objects', serializationModel="Studio.02.02.00")
                    obj = ET.SubElement(root, 'object', {'class': class_name, 'id': item_id})

                    prop = ET.SubElement(obj, 'property', name='name')
                    ET.SubElement(prop, 'value').text = data['name']

                    if parent_id:
                        rel = ET.SubElement(obj, 'relationship', name=parent_rel_name)
                        ET.SubElement(rel, 'destination').text = parent_id

                    out_file = folder_path / f"{item_id}.xml"
                    out_file.parent.mkdir(exist_ok=True)
                    write_pretty_xml(root, out_file)

                    data['path'] = out_file
                    committed_dict[item_id] = data
                    committed_list.append(item_id)
                    count += 1
                    made_progress = True
                else:
                    remaining.append((item_id, data))

            if not made_progress and remaining:
                # Check if we are waiting for pending parents that are in 'remaining'
                # If a remaining item has a parent that is ALSO in remaining, we are not deadlocked yet, just out of order.
                # But topological sort above iterates until progress stops.
                # If progress stops and items remain, it means their parents are missing or circular.
                orphans = [f"{d['name']} (parent: {d.get('parent')})" for i, d in remaining]
                raise ValueError(f"Cannot commit {class_name} items with missing parents: {orphans}")

            items = remaining
            
        return count

    def _commit_banks(self, pending_banks: Dict, committed_dict: Dict, 
                     committed_list: list, master_id: str, metadata_path: Path) -> int:
        """Special commit logic for Banks (Mixed types: BankFolder vs Bank)."""
        count = 0
        items = list(pending_banks.items())
        
        while items:
            made_progress = False
            remaining = []

            for item_id, data in items:
                parent_id = data.get('parent')
                is_ready = (parent_id in committed_dict or 
                           parent_id in committed_list or 
                           parent_id == master_id)

                if is_ready:
                    is_folder = data.get('type') == 'folder'
                    class_name = 'BankFolder' if is_folder else 'Bank'
                    sub_dir = "BankFolder" if is_folder else "Bank"
                    
                    root = ET.Element('objects', serializationModel="Studio.02.02.00")
                    obj = ET.SubElement(root, 'object', {'class': class_name, 'id': item_id})

                    prop = ET.SubElement(obj, 'property', name='name')
                    ET.SubElement(prop, 'value').text = data['name']

                    if parent_id:
                        rel = ET.SubElement(obj, 'relationship', name='folder')
                        ET.SubElement(rel, 'destination').text = parent_id

                    out_file = metadata_path / sub_dir / f"{item_id}.xml"
                    out_file.parent.mkdir(exist_ok=True)
                    write_pretty_xml(root, out_file)

                    data['path'] = out_file
                    committed_dict[item_id] = data
                    committed_list.append(item_id)
                    count += 1
                    made_progress = True
                else:
                    remaining.append((item_id, data))
            
            if not made_progress and remaining:
                raise ValueError(f"Cannot commit Banks with missing parents: {remaining}")
            items = remaining

        return count

    def _commit_buses(self, pending_buses: Dict, committed_dict: Dict, 
                     committed_list: list, metadata_path: Path) -> int:
        """Special commit logic for Buses (Complex XML structure)."""
        count = 0
        items = list(pending_buses.items())
        
        while items:
            made_progress = False
            remaining = []

            for item_id, data in items:
                parent_id = data.get('parent')
                # Master bus has parent=None
                is_ready = (parent_id is None or 
                           parent_id in committed_dict or 
                           parent_id in committed_list)

                if is_ready:
                    # Use BusManager-like XML construction but inline here to avoid circular dep
                    # or re-implement simple version since we just need the file written
                    
                    root = ET.Element('objects', serializationModel="Studio.02.02.00")
                    obj = ET.SubElement(root, 'object', {'class': 'MixerGroup', 'id': item_id})

                    prop = ET.SubElement(obj, 'property', name='name')
                    ET.SubElement(prop, 'value').text = data['name']

                    # Essential components UUIDs
                    effect_chain_id = "{" + str(uuid.uuid4()) + "}"
                    panner_id = "{" + str(uuid.uuid4()) + "}"
                    fader_id = "{" + str(uuid.uuid4()) + "}"

                    # Relationships
                    rel = ET.SubElement(obj, 'relationship', name='effectChain')
                    ET.SubElement(rel, 'destination').text = effect_chain_id
                    
                    rel = ET.SubElement(obj, 'relationship', name='panner')
                    ET.SubElement(rel, 'destination').text = panner_id
                    
                    if parent_id:
                        rel = ET.SubElement(obj, 'relationship', name='output')
                        ET.SubElement(rel, 'destination').text = parent_id

                    # Sub-objects
                    ec_obj = ET.SubElement(root, 'object', {'class': 'MixerBusEffectChain', 'id': effect_chain_id})
                    rel = ET.SubElement(ec_obj, 'relationship', name='effects')
                    ET.SubElement(rel, 'destination').text = fader_id
                    
                    ET.SubElement(root, 'object', {'class': 'MixerBusPanner', 'id': panner_id})
                    ET.SubElement(root, 'object', {'class': 'MixerBusFader', 'id': fader_id})

                    out_file = metadata_path / "Group" / f"{item_id}.xml"
                    out_file.parent.mkdir(exist_ok=True)
                    write_pretty_xml(root, out_file)

                    data['path'] = out_file
                    committed_dict[item_id] = data
                    committed_list.append(item_id)
                    count += 1
                    made_progress = True
                else:
                    remaining.append((item_id, data))

            if not made_progress and remaining:
                raise ValueError(f"Cannot commit Buses with missing parents: {remaining}")
            items = remaining

        return count

    def clear_all(self) -> int:
        """Clear all pending items without committing."""
        count = (len(self._pending_event_folders) + 
                 len(self._pending_asset_folders) +
                 len(self._pending_banks) +
                 len(self._pending_buses))
        
        self._pending_event_folders.clear()
        self._pending_asset_folders.clear()
        self._pending_banks.clear()
        self._pending_buses.clear()
        return count

    def is_pending(self, item_id: str) -> bool:
        """Check if an item is pending."""
        return (item_id in self._pending_event_folders or
                item_id in self._pending_asset_folders or
                item_id in self._pending_banks or
                item_id in self._pending_buses)

    def get_all_event_folders(self, committed: Dict) -> Dict:
        return {**committed, **self._pending_event_folders}

    def get_all_asset_folders(self, committed: Dict) -> Dict:
        return {**committed, **self._pending_asset_folders}

    def get_all_banks(self, committed: Dict) -> Dict:
        """Get all banks (committed + pending)."""
        return {**committed, **self._pending_banks}

    def get_all_buses(self, committed: Dict) -> Dict:
        """Get all buses (committed + pending)."""
        return {**committed, **self._pending_buses}

