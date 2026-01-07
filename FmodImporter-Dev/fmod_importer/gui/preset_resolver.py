"""
Preset Reference Resolver Module
Handles smart UUID resolution for FMOD project references (folders, banks, buses, assets).
"""

from typing import Optional, Tuple


class PresetResolver:
    """
    Helper class for resolving FMOD references when loading presets.

    Implements 3-step resolution strategy:
    1. Try UUID match (exact match in current project)
    2. Try path/name match (find by path even if UUID changed)
    3. Create missing resource using stored path/name

    This allows presets to work across different FMOD projects by:
    - Using UUIDs when they match (most reliable)
    - Falling back to paths when UUIDs differ
    - Auto-creating missing resources to avoid user errors
    """

    def __init__(self, project):
        """
        Initialize resolver with FMOD project instance.

        Args:
            project: FMODProject instance with loaded XML data
        """
        self.project = project

    # ==================== FOLDER RESOLUTION ====================

    def resolve_folder_reference(self, ref: dict) -> Optional[str]:
        """Resolve folder reference (UUID + path)."""
        if not self.project:
            return None

        folder_id = ref.get('id', '')
        folder_path = ref.get('path', '')

        # Check committed AND pending folders
        all_folders = self.project.get_all_event_folders()

        # Step 1: Try UUID match
        if folder_id and folder_id in all_folders:
            return folder_id

        # Step 2: Try path match
        if folder_path:
            existing_id = self.find_folder_by_path(folder_path)
            if existing_id:
                return existing_id

            # Step 3: Create hierarchy (Pending only)
            try:
                new_id = self.create_folder_hierarchy(folder_path)
                return new_id
            except Exception as e:
                print(f"Failed to create folder hierarchy '{folder_path}': {e}")
                return None

        return None

    def find_folder_by_path(self, path: str) -> Optional[str]:
        """Search all (committed+pending) folders for matching path."""
        if not self.project or not path:
            return None

        all_folders = self.project.get_all_event_folders()
        
        # We need to build paths using the pending-aware logic
        # But get_folder_path() already handles pending folders
        for folder_id in all_folders:
            folder_path = self.get_folder_path(folder_id)
            if folder_path == path:
                return folder_id

        return None

    def create_folder_hierarchy(self, full_path: str) -> str:
        """Create nested folder structure (Pending)."""
        if not self.project:
            raise ValueError("No project loaded")

        parts = full_path.split('/')
        parts = [p for p in parts if p]

        master_id = self.project.workspace.get('masterEventFolder')
        current_parent = master_id
        
        # Get all folders (including those just created in previous loop iterations)
        # Note: We re-fetch inside loop or update local cache?
        # get_all_event_folders returns a copy, so we need to be careful.
        # However, create_event_folder updates the pending manager immediately.

        for part in parts:
            # Re-fetch all folders to include just-created ones
            all_folders = self.project.get_all_event_folders()
            
            # Find child with this name
            child_id = None
            for folder_id, folder_data in all_folders.items():
                if (folder_data.get('parent') == current_parent and
                    folder_data.get('name') == part):
                    child_id = folder_id
                    break

            # Create if not found
            if not child_id:
                # Use commit=False (Pending)
                child_id = self.project.create_event_folder(part, current_parent, commit=False)
                print(f"Created pending folder: {part}")

            current_parent = child_id

        return current_parent

    # ==================== BANK RESOLUTION ====================

    def resolve_bank_reference(self, ref: dict) -> Optional[str]:
        """Resolve bank reference (try UUID → name match → create pending)."""
        if not self.project:
            return None

        bank_id = ref.get('id', '')
        bank_name = ref.get('name', '')
        
        all_banks = self.project.get_all_banks()

        # Step 1: Try UUID match
        if bank_id and bank_id in all_banks:
            return bank_id

        # Step 2: Try name match
        if bank_name:
            for bid, bdata in all_banks.items():
                if bdata.get('name') == bank_name:
                    return bid

            # Step 3: Create bank (Pending)
            try:
                parent_id = ref.get('parent_id', '')
                # Try to create as Bank (not folder) by default for presets?
                # Usually presets store the Leaf bank.
                new_id = self.project.create_bank_instance(bank_name, parent_id or None, commit=False)
                print(f"Created pending bank: {bank_name}")
                return new_id
            except Exception as e:
                print(f"Failed to create bank '{bank_name}': {e}")
                return None

        return None

    # ==================== BUS RESOLUTION ====================

    def resolve_bus_reference(self, ref: dict) -> Optional[str]:
        """Resolve bus reference (try UUID → path match → create pending hierarchy)."""
        if not self.project:
            return None

        bus_id = ref.get('id', '')
        bus_path = ref.get('path', '')
        
        all_buses = self.project.get_all_buses()

        # Step 1: Try UUID match
        if bus_id and bus_id in all_buses:
            return bus_id

        # Step 2: Try path match
        if bus_path:
            for bid in all_buses:
                if self.get_bus_path(bid) == bus_path:
                    return bid

            # Step 3: Create bus hierarchy (simplified - just create leaf bus)
            try:
                parts = bus_path.split('/')
                bus_name = parts[-1] if parts else bus_path
                master_bus_id = self.project._get_master_bus_id()
                
                # Check if hierarchy exists? For now, just create at master.
                # Use commit=False
                new_id = self.project.create_bus(bus_name, master_bus_id, commit=False)
                print(f"Created pending bus: {bus_name}")
                return new_id
            except Exception as e:
                print(f"Failed to create bus '{bus_path}': {e}")
                return None

        return None

    # ==================== ASSET FOLDER RESOLUTION ====================

    def resolve_asset_folder_reference(self, ref: dict) -> Optional[str]:
        """Resolve asset folder reference (try UUID → path match → create pending)."""
        if not self.project:
            return None

        asset_id = ref.get('id', '')
        asset_path = ref.get('path', '')
        
        all_assets = self.project.get_all_asset_folders()

        # Step 1: Try UUID match
        if asset_id and asset_id in all_assets:
            return asset_id

        # Step 2: Try path match
        if asset_path:
            for aid, adata in all_assets.items():
                if adata.get('path') == asset_path:
                    return aid

            # Step 3: Create asset folder
            try:
                parts = asset_path.rstrip('/').split('/')
                folder_name = parts[-1] if parts else ''
                parent_path = '/'.join(parts[:-1]) + '/' if len(parts) > 1 else ''

                # Use commit=False
                new_id = self.project.create_asset_folder(folder_name, parent_path, commit=False)
                print(f"Created pending asset folder: {folder_name}")
                return new_id
            except Exception as e:
                print(f"Failed to create asset folder '{asset_path}': {e}")
                return None

        return None

    # ==================== PATH BUILDING HELPERS ====================

    def get_folder_path(self, folder_id: str) -> str:
        """Build full path from folder ID (checking committed and pending)."""
        if not self.project or not folder_id:
            return ""

        # Use helper from project that merges both lists
        all_folders = self.project.get_all_event_folders()

        path_parts = []
        current_id = folder_id
        master_id = self.project.workspace.get('masterEventFolder')

        while current_id and current_id in all_folders and current_id != master_id:
            folder_data = all_folders[current_id]
            path_parts.insert(0, folder_data.get('name', ''))
            current_id = folder_data.get('parent')

        return '/'.join(path_parts)

    def get_bus_path(self, bus_id: str) -> str:
        """Build full path from bus ID (checking committed and pending)."""
        if not self.project or not bus_id:
            return ""
            
        all_buses = self.project.get_all_buses()

        path_parts = []
        current_id = bus_id
        master_bus_id = self.project._get_master_bus_id()

        while current_id and current_id in all_buses:
            bus_data = all_buses[current_id]
            bus_name = bus_data.get('name', '')

            if current_id == master_bus_id:
                break

            path_parts.insert(0, bus_name)
            current_id = bus_data.get('parent')

        return "bus:/" + '/'.join(path_parts)

    def get_bank_name_and_parent(self, bank_id: str) -> Tuple[str, str]:
        """Get bank name and parent ID."""
        if not self.project or not bank_id:
            return ("", "")
            
        all_banks = self.project.get_all_banks()
        
        if bank_id not in all_banks:
            return ("", "")

        bank_data = all_banks[bank_id]
        return (bank_data.get('name', ''), bank_data.get('parent', ''))

    def get_bank_path(self, bank_id: str) -> str:
        """Build full path from bank ID."""
        if not self.project or not bank_id:
            return ""

        all_banks = self.project.get_all_banks()
        if bank_id not in all_banks:
            return ""

        path_parts = []
        current_id = bank_id
        master_bank_id = self.project.workspace.get('masterBankFolder')

        while current_id and current_id in all_banks:
            bank_data = all_banks[current_id]
            bank_name = bank_data.get('name', '')

            if current_id == master_bank_id:
                break

            path_parts.insert(0, bank_name)
            current_id = bank_data.get('parent')

        if not path_parts:
            return all_banks[bank_id].get('name', '')

        return '/'.join(path_parts)
