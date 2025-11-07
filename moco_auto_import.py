#!/usr/bin/env python3
"""
Moco Auto Import - FMOD Studio Asset Importer
A Python tool with GUI to intelligently import audio assets into FMOD Studio projects
"""

import os
import json
import uuid
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from xml.dom import minidom
import wave
import platform


class FMODProject:
    """Represents a FMOD Studio project and handles XML manipulation"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.metadata_path = self.project_path.parent / "Metadata"

        if not self.metadata_path.exists():
            raise ValueError(f"Metadata folder not found: {self.metadata_path}")

        self.workspace = self._load_workspace()
        self.event_folders = self._load_event_folders()
        self.banks = self._load_banks()
        self.buses = self._load_buses()
        self.asset_folders = self._load_asset_folders()

    def _load_workspace(self) -> Dict:
        """Load workspace.xml to get master folder references"""
        workspace_file = self.metadata_path / "Workspace.xml"
        if not workspace_file.exists():
            raise ValueError("Workspace.xml not found")

        tree = ET.parse(workspace_file)
        root = tree.getroot()

        workspace_obj = root.find(".//object[@class='Workspace']")
        if workspace_obj is None:
            raise ValueError("Workspace object not found")

        return {
            'id': workspace_obj.get('id'),
            'masterEventFolder': workspace_obj.find(".//relationship[@name='masterEventFolder']/destination").text,
            'masterBankFolder': workspace_obj.find(".//relationship[@name='masterBankFolder']/destination").text,
            'masterAssetFolder': workspace_obj.find(".//relationship[@name='masterAssetFolder']/destination").text
        }

    def _load_event_folders(self) -> Dict[str, Dict]:
        """Load all event folders from the EventFolder directory"""
        folders = {}
        event_folder_dir = self.metadata_path / "EventFolder"

        if not event_folder_dir.exists():
            return folders

        for xml_file in event_folder_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall(".//object"):
                folder_id = obj.get('id')
                name_elem = obj.find(".//property[@name='name']/value")
                name = name_elem.text if name_elem is not None else "Unnamed"

                # Get parent folder
                parent_rel = obj.find(".//relationship[@name='folder']/destination")
                parent_id = parent_rel.text if parent_rel is not None else None

                folders[folder_id] = {
                    'name': name,
                    'parent': parent_id,
                    'path': xml_file,
                    'items': []
                }

        return folders

    def get_events_in_folder(self, folder_id: str) -> List[Dict]:
        """Get all events in a specific folder (recursively)"""
        events = []
        event_dir = self.metadata_path / "Event"

        if not event_dir.exists():
            return events

        # Helper to check if folder_id is a parent/ancestor
        def is_in_folder_hierarchy(event_folder_id: str, target_folder_id: str) -> bool:
            if event_folder_id == target_folder_id:
                return True
            # Check if parent folder matches
            if event_folder_id in self.event_folders:
                parent_id = self.event_folders[event_folder_id].get('parent')
                if parent_id and parent_id != event_folder_id:
                    return is_in_folder_hierarchy(parent_id, target_folder_id)
            return False

        # Scan all event files
        for xml_file in event_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall(".//object[@class='Event']"):
                event_id = obj.get('id')
                name_elem = obj.find(".//property[@name='name']/value")
                event_name = name_elem.text if name_elem is not None else "Unnamed"

                # Get event's folder
                folder_rel = obj.find(".//relationship[@name='folder']/destination")
                event_folder_id = folder_rel.text if folder_rel is not None else None

                # Check if this event is in the target folder or its subfolders
                if event_folder_id and is_in_folder_hierarchy(event_folder_id, folder_id):
                    events.append({
                        'id': event_id,
                        'name': event_name,
                        'path': xml_file,
                        'folder_id': event_folder_id
                    })

        return events

    def _load_banks(self) -> Dict[str, Dict]:
        """Load all banks from the Bank directory"""
        banks = {}
        bank_dir = self.metadata_path / "Bank"

        if not bank_dir.exists():
            return banks

        for xml_file in bank_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Look for both MasterBank and Bank classes
            for obj in root.findall(".//object"):
                obj_class = obj.get('class')
                if obj_class in ['MasterBank', 'Bank']:
                    bank_id = obj.get('id')
                    name_elem = obj.find(".//property[@name='name']/value")
                    name = name_elem.text if name_elem is not None else "Unnamed"

                    # Get parent relationship if exists
                    parent_rel = obj.find(".//relationship[@name='folder']/destination")
                    parent_id = parent_rel.text if parent_rel is not None else None

                    banks[bank_id] = {
                        'name': name,
                        'path': xml_file,
                        'parent': parent_id
                    }

        return banks

    def _load_buses(self) -> Dict[str, Dict]:
        """Load all mixer buses from Master.xml and Group directory"""
        buses = {}

        # Load master bus from Master.xml
        master_file = self.metadata_path / "Master.xml"
        if master_file.exists():
            tree = ET.parse(master_file)
            root = tree.getroot()

            for obj in root.findall(".//object"):
                obj_class = obj.get('class')
                if obj_class == 'MixerMaster':
                    bus_id = obj.get('id')
                    name_elem = obj.find(".//property[@name='name']/value")
                    name = name_elem.text if name_elem is not None else "Master Bus"

                    buses[bus_id] = {
                        'name': name,
                        'path': master_file,
                        'parent': None  # Master has no parent
                    }

        # Load other buses from Group directory
        group_dir = self.metadata_path / "Group"
        if group_dir.exists():
            for xml_file in group_dir.glob("*.xml"):
                tree = ET.parse(xml_file)
                root = tree.getroot()

                for obj in root.findall(".//object"):
                    obj_class = obj.get('class')
                    if obj_class == 'MixerGroup':
                        bus_id = obj.get('id')
                        name_elem = obj.find(".//property[@name='name']/value")
                        name = name_elem.text if name_elem is not None else "Unnamed"

                        # Get parent relationship (output)
                        parent_rel = obj.find(".//relationship[@name='output']/destination")
                        parent_id = parent_rel.text if parent_rel is not None else None

                        buses[bus_id] = {
                            'name': name,
                            'path': xml_file,
                            'parent': parent_id
                        }

        return buses

    def _get_master_bus_id(self) -> Optional[str]:
        """Get the master bus ID"""
        for bus_id, bus_info in self.buses.items():
            if bus_info['parent'] is None:  # Master bus has no parent
                return bus_id
        return None

    def _load_asset_folders(self) -> Dict[str, Dict]:
        """Load all asset folders from the Asset directory"""
        asset_folders = {}
        asset_dir = self.metadata_path / "Asset"

        if not asset_dir.exists():
            return asset_folders

        for xml_file in asset_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall(".//object[@class='EncodableAsset']"):
                asset_id = obj.get('id')
                path_elem = obj.find(".//property[@name='assetPath']/value")
                asset_path = path_elem.text if path_elem is not None else ""

                master_folder_rel = obj.find(".//relationship[@name='masterAssetFolder']/destination")
                master_folder_id = master_folder_rel.text if master_folder_rel is not None else None

                asset_folders[asset_id] = {
                    'path': asset_path,
                    'xml_path': xml_file,
                    'master_folder': master_folder_id
                }

        return asset_folders

    def get_folder_hierarchy(self) -> List[Tuple[str, str, int]]:
        """Get event folders as a hierarchical list (name, id, depth)"""
        def build_hierarchy(folder_id: str, depth: int = 0) -> List[Tuple[str, str, int]]:
            result = []
            if folder_id in self.event_folders:
                folder = self.event_folders[folder_id]
                result.append((folder['name'], folder_id, depth))

                # Find children
                for fid, fdata in self.event_folders.items():
                    if fdata['parent'] == folder_id:
                        result.extend(build_hierarchy(fid, depth + 1))

            return result

        master_id = self.workspace['masterEventFolder']
        return build_hierarchy(master_id)

    def create_event_folder(self, name: str, parent_id: str) -> str:
        """Create a new event folder"""
        folder_id = "{" + str(uuid.uuid4()) + "}"

        # Create XML
        root = ET.Element('objects', serializationModel="Studio.02.02.00")
        obj = ET.SubElement(root, 'object', {'class': 'EventFolder', 'id': folder_id})

        # Add name property
        prop = ET.SubElement(obj, 'property', name='name')
        value = ET.SubElement(prop, 'value')
        value.text = name

        # Add parent relationship
        rel = ET.SubElement(obj, 'relationship', name='folder')
        dest = ET.SubElement(rel, 'destination')
        dest.text = parent_id

        # Write to file
        folder_file = self.metadata_path / "EventFolder" / f"{folder_id}.xml"
        self._write_pretty_xml(root, folder_file)

        # Update internal structure
        self.event_folders[folder_id] = {
            'name': name,
            'parent': parent_id,
            'path': folder_file,
            'items': []
        }

        return folder_id

    def create_bank(self, name: str, parent_id: str = None) -> str:
        """Create a new bank folder (BankFolder object)"""
        bank_id = "{" + str(uuid.uuid4()) + "}"

        # Create XML
        root = ET.Element('objects', serializationModel="Studio.02.02.00")
        obj = ET.SubElement(root, 'object', {'class': 'BankFolder', 'id': bank_id})

        # Add name property
        prop = ET.SubElement(obj, 'property', name='name')
        value = ET.SubElement(prop, 'value')
        value.text = name

        # Add parent relationship if exists
        if parent_id:
            rel = ET.SubElement(obj, 'relationship', name='folder')
            dest = ET.SubElement(rel, 'destination')
            dest.text = parent_id

        # Ensure BankFolder directory exists
        bank_folder_dir = self.metadata_path / "BankFolder"
        bank_folder_dir.mkdir(exist_ok=True)

        # Write to file in BankFolder directory
        bank_file = bank_folder_dir / f"{bank_id}.xml"
        self._write_pretty_xml(root, bank_file)

        # Update internal structure
        self.banks[bank_id] = {
            'name': name,
            'path': bank_file,
            'parent': parent_id
        }

        return bank_id

    def delete_bank(self, bank_id: str):
        """Delete a bank"""
        if bank_id in self.banks:
            bank_path = self.banks[bank_id]['path']
            if bank_path.exists():
                bank_path.unlink()
            del self.banks[bank_id]

    def create_bus(self, name: str, parent_id: str = None) -> str:
        """Create a new bus (MixerGroup)"""
        bus_id = "{" + str(uuid.uuid4()) + "}"

        # Create XML structure for MixerGroup
        root = ET.Element('objects', serializationModel="Studio.02.02.00")
        obj = ET.SubElement(root, 'object', {'class': 'MixerGroup', 'id': bus_id})

        # Add name property
        prop = ET.SubElement(obj, 'property', name='name')
        value = ET.SubElement(prop, 'value')
        value.text = name

        # Add effectChain
        effect_chain_id = "{" + str(uuid.uuid4()) + "}"
        rel_effect = ET.SubElement(obj, 'relationship', name='effectChain')
        dest_effect = ET.SubElement(rel_effect, 'destination')
        dest_effect.text = effect_chain_id

        # Add panner
        panner_id = "{" + str(uuid.uuid4()) + "}"
        rel_panner = ET.SubElement(obj, 'relationship', name='panner')
        dest_panner = ET.SubElement(rel_panner, 'destination')
        dest_panner.text = panner_id

        # Add output (parent relationship)
        # If no parent specified, route to Master Bus
        if not parent_id:
            # Get master bus from Mixer.xml
            parent_id = self._get_master_bus_id()

        if parent_id:
            rel_output = ET.SubElement(obj, 'relationship', name='output')
            dest_output = ET.SubElement(rel_output, 'destination')
            dest_output.text = parent_id

        # Add effect chain object
        effect_chain_obj = ET.SubElement(root, 'object', {'class': 'MixerBusEffectChain', 'id': effect_chain_id})
        fader_id = "{" + str(uuid.uuid4()) + "}"
        rel_effects = ET.SubElement(effect_chain_obj, 'relationship', name='effects')
        dest_fader = ET.SubElement(rel_effects, 'destination')
        dest_fader.text = fader_id

        # Add panner object
        ET.SubElement(root, 'object', {'class': 'MixerBusPanner', 'id': panner_id})

        # Add fader object
        ET.SubElement(root, 'object', {'class': 'MixerBusFader', 'id': fader_id})

        # Ensure Group folder exists
        group_folder = self.metadata_path / "Group"
        group_folder.mkdir(exist_ok=True)

        # Write to file
        bus_file = group_folder / f"{bus_id}.xml"
        self._write_pretty_xml(root, bus_file)

        # Update internal structure
        self.buses[bus_id] = {
            'name': name,
            'path': bus_file,
            'parent': parent_id
        }

        return bus_id

    def delete_bus(self, bus_id: str):
        """Delete a bus"""
        if bus_id in self.buses:
            bus_path = self.buses[bus_id]['path']
            if bus_path.exists():
                bus_path.unlink()
            del self.buses[bus_id]

    def delete_folder(self, folder_id: str):
        """Delete an event folder"""
        if folder_id in self.event_folders:
            folder_path = self.event_folders[folder_id]['path']
            if folder_path.exists():
                folder_path.unlink()
            del self.event_folders[folder_id]

    def _write_pretty_xml(self, element: ET.Element, filepath: Path):
        """Write XML with proper formatting"""
        xml_str = ET.tostring(element, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='\t', encoding='UTF-8')

        with open(filepath, 'wb') as f:
            f.write(pretty_xml)

    def copy_event_from_template(self, template_event_id: str, new_name: str,
                                  dest_folder_id: str, bank_id: str, bus_id: str,
                                  audio_files: List[str], audio_asset_folder: str) -> str:
        """
        Copy an event from template and assign audio files to it

        Args:
            template_event_id: ID of the template event to copy
            new_name: New name for the event
            dest_folder_id: Destination folder ID
            bank_id: Bank ID to assign
            bus_id: Bus ID to assign
            audio_files: List of audio file paths to assign
            audio_asset_folder: Folder where audio assets should be placed

        Returns:
            New event ID
        """
        import shutil

        # Find template event
        template_event_path = self.metadata_path / "Event" / f"{template_event_id}.xml"
        if not template_event_path.exists():
            raise ValueError(f"Template event {template_event_id} not found")

        # Parse template XML
        template_tree = ET.parse(template_event_path)
        template_root = template_tree.getroot()

        # Create new event ID
        new_event_id = "{" + str(uuid.uuid4()) + "}"

        # Deep copy the entire XML structure
        new_root = ET.Element('objects', serializationModel="Studio.02.02.00")

        # Map old IDs to new IDs
        id_map = {}

        # First pass: collect all IDs and create new ones
        for obj in template_root.findall(".//object"):
            old_id = obj.get('id')
            new_id = "{" + str(uuid.uuid4()) + "}"
            id_map[old_id] = new_id

        # Override the event ID with our chosen ID
        event_obj = template_root.find(".//object[@class='Event']")
        if event_obj is not None:
            id_map[event_obj.get('id')] = new_event_id

        # Second pass: copy objects and update references
        for obj in template_root.findall(".//object"):
            old_id = obj.get('id')
            new_obj = ET.SubElement(new_root, 'object')
            new_obj.set('class', obj.get('class'))
            new_obj.set('id', id_map[old_id])

            # Copy properties
            for prop in obj.findall('property'):
                new_prop = ET.SubElement(new_obj, 'property')
                new_prop.set('name', prop.get('name'))
                value_elem = prop.find('value')
                if value_elem is not None:
                    new_value = ET.SubElement(new_prop, 'value')
                    # Special case: replace event name
                    if obj.get('class') == 'Event' and prop.get('name') == 'name':
                        new_value.text = new_name
                    else:
                        new_value.text = value_elem.text

            # Copy relationships and update destinations
            for rel in obj.findall('relationship'):
                new_rel = ET.SubElement(new_obj, 'relationship')
                new_rel.set('name', rel.get('name'))

                # Special cases for relationships we want to override
                if obj.get('class') == 'Event':
                    if rel.get('name') == 'folder':
                        # Change to destination folder
                        dest = ET.SubElement(new_rel, 'destination')
                        dest.text = dest_folder_id
                        continue
                    elif rel.get('name') == 'banks':
                        # Change to selected bank
                        dest = ET.SubElement(new_rel, 'destination')
                        dest.text = bank_id
                        continue

                if obj.get('class') == 'MixerInput' and rel.get('name') == 'output':
                    # Change to selected bus
                    dest = ET.SubElement(new_rel, 'destination')
                    dest.text = bus_id
                    continue

                # Copy all destinations
                for dest_elem in rel.findall('destination'):
                    new_dest = ET.SubElement(new_rel, 'destination')
                    old_dest_id = dest_elem.text
                    # Update to new ID if it's in our map
                    new_dest.text = id_map.get(old_dest_id, old_dest_id)

        # Create audio files and add them to the event
        if audio_files:
            # Create AudioFile objects and SingleSound objects
            single_sound_ids = []

            for audio_file_path in audio_files:
                # Get the source audio file
                audio_file_src = Path(audio_file_path)

                # Create the FMOD asset path (relative to Assets folder)
                # Combine the asset folder path with the filename
                asset_relative_path = audio_asset_folder + audio_file_src.name

                # Copy audio file to FMOD project Assets folder
                assets_folder = self.project_path.parent / "Assets"
                dest_folder = assets_folder / Path(audio_asset_folder)
                dest_folder.mkdir(parents=True, exist_ok=True)
                
                dest_file = dest_folder / audio_file_src.name
                shutil.copy2(audio_file_src, dest_file)

                # Create AudioFile using the helper method
                # Pass the actual file path for reading properties, and the FMOD asset path
                audio_file_id = self.create_audio_file(str(audio_file_src), asset_relative_path)

                # Create SingleSound object
                single_sound_id = "{" + str(uuid.uuid4()) + "}"
                single_sound_obj = ET.SubElement(new_root, 'object', {'class': 'SingleSound', 'id': single_sound_id})

                # Add audioFile relationship
                rel_audio = ET.SubElement(single_sound_obj, 'relationship', name='audioFile')
                dest_audio = ET.SubElement(rel_audio, 'destination')
                dest_audio.text = audio_file_id

                single_sound_ids.append(single_sound_id)

            # Create MultiSound object
            multi_sound_id = "{" + str(uuid.uuid4()) + "}"
            multi_sound_obj = ET.SubElement(new_root, 'object', {'class': 'MultiSound', 'id': multi_sound_id})

            # Add length property (calculate from first audio file)
            try:
                with wave.open(audio_files[0], 'rb') as wav_file:
                    length_seconds = wav_file.getnframes() / float(wav_file.getframerate())
                    prop_ms_length = ET.SubElement(multi_sound_obj, 'property', name='length')
                    value_ms_length = ET.SubElement(prop_ms_length, 'value')
                    value_ms_length.text = str(length_seconds)
            except:
                # If we can't read the file, use a default length
                prop_ms_length = ET.SubElement(multi_sound_obj, 'property', name='length')
                value_ms_length = ET.SubElement(prop_ms_length, 'value')
                value_ms_length.text = "0.0"

            # Add sounds relationship
            rel_sounds = ET.SubElement(multi_sound_obj, 'relationship', name='sounds')
            for ss_id in single_sound_ids:
                dest_sound = ET.SubElement(rel_sounds, 'destination')
                dest_sound.text = ss_id

            # Find or create GroupTrack
            group_track = new_root.find(".//object[@class='GroupTrack']")
            if group_track is None:
                # Create a new GroupTrack if it doesn't exist
                group_track_id = "{" + str(uuid.uuid4()) + "}"
                group_track = ET.SubElement(new_root, 'object', {'class': 'GroupTrack', 'id': group_track_id})

                # Create EventMixerGroup for the track
                mixer_group_id = "{" + str(uuid.uuid4()) + "}"
                mixer_group = ET.SubElement(new_root, 'object', {'class': 'EventMixerGroup', 'id': mixer_group_id})

                # Add name property to mixer group
                prop_mg_name = ET.SubElement(mixer_group, 'property', name='name')
                value_mg_name = ET.SubElement(prop_mg_name, 'value')
                value_mg_name.text = "Audio 1"

                # Add effectChain to mixer group
                effect_chain_id = "{" + str(uuid.uuid4()) + "}"
                rel_effect_chain = ET.SubElement(mixer_group, 'relationship', name='effectChain')
                dest_effect_chain = ET.SubElement(rel_effect_chain, 'destination')
                dest_effect_chain.text = effect_chain_id

                # Add panner to mixer group
                panner_id = "{" + str(uuid.uuid4()) + "}"
                rel_panner = ET.SubElement(mixer_group, 'relationship', name='panner')
                dest_panner = ET.SubElement(rel_panner, 'destination')
                dest_panner.text = panner_id

                # Add output to EventMixerMaster
                event_mixer_master = new_root.find(".//object[@class='EventMixerMaster']")
                if event_mixer_master is not None:
                    rel_output = ET.SubElement(mixer_group, 'relationship', name='output')
                    dest_output = ET.SubElement(rel_output, 'destination')
                    dest_output.text = event_mixer_master.get('id')

                # Create effect chain
                effect_chain = ET.SubElement(new_root, 'object', {'class': 'MixerBusEffectChain', 'id': effect_chain_id})
                fader_id = "{" + str(uuid.uuid4()) + "}"
                rel_effects = ET.SubElement(effect_chain, 'relationship', name='effects')
                dest_fader = ET.SubElement(rel_effects, 'destination')
                dest_fader.text = fader_id

                # Create panner
                ET.SubElement(new_root, 'object', {'class': 'MixerBusPanner', 'id': panner_id})

                # Create fader
                ET.SubElement(new_root, 'object', {'class': 'MixerBusFader', 'id': fader_id})

                # Add mixerGroup relationship to GroupTrack
                rel_mixer = ET.SubElement(group_track, 'relationship', name='mixerGroup')
                dest_mixer = ET.SubElement(rel_mixer, 'destination')
                dest_mixer.text = mixer_group_id

                # Add GroupTrack to Event's groupTracks relationship
                event_obj = new_root.find(".//object[@class='Event']")
                if event_obj is not None:
                    rel_group_tracks = event_obj.find(".//relationship[@name='groupTracks']")
                    if rel_group_tracks is None:
                        rel_group_tracks = ET.SubElement(event_obj, 'relationship', name='groupTracks')
                    dest_group_track = ET.SubElement(rel_group_tracks, 'destination')
                    dest_group_track.text = group_track_id

            # Update GroupTrack to reference MultiSound
            rel_modules = group_track.find(".//relationship[@name='modules']")
            if rel_modules is None:
                rel_modules = ET.SubElement(group_track, 'relationship', name='modules')
            else:
                # Clear existing modules
                for dest in list(rel_modules.findall('destination')):
                    rel_modules.remove(dest)

            dest_module = ET.SubElement(rel_modules, 'destination')
            dest_module.text = multi_sound_id

            # Update Timeline to reference MultiSound
            timeline = new_root.find(".//object[@class='Timeline']")
            if timeline is not None:
                rel_timeline_modules = timeline.find(".//relationship[@name='modules']")
                if rel_timeline_modules is None:
                    rel_timeline_modules = ET.SubElement(timeline, 'relationship', name='modules')
                else:
                    # Clear existing modules
                    for dest in list(rel_timeline_modules.findall('destination')):
                        rel_timeline_modules.remove(dest)

                dest_timeline_module = ET.SubElement(rel_timeline_modules, 'destination')
                dest_timeline_module.text = multi_sound_id

        # Write new event file
        event_file = self.metadata_path / "Event" / f"{new_event_id}.xml"
        self._write_pretty_xml(new_root, event_file)

        return new_event_id

    def create_audio_file(self, audio_file_path: str, asset_relative_path: str) -> str:
        """
        Create an AudioFile XML entry in the FMOD project

        Args:
            audio_file_path: Full path to the source audio file
            asset_relative_path: Relative path within FMOD project (e.g., "Characters/Cat Boss Rich/Cat_Boss_Rich_Run_03.wav")

        Returns:
            The new AudioFile UUID
        """
        # Generate new UUID for AudioFile
        audio_file_id = "{" + str(uuid.uuid4()) + "}"

        # Read audio file properties
        try:
            with wave.open(audio_file_path, 'rb') as wav_file:
                # Get audio properties
                channel_count = wav_file.getnchannels()
                sample_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()

                # Calculate frequency in kHz
                frequency_khz = sample_rate / 1000.0

                # Calculate length in seconds
                length_seconds = n_frames / float(sample_rate)
        except Exception as e:
            raise ValueError(f"Failed to read audio file properties: {e}")

        # Create XML structure
        root = ET.Element('objects', serializationModel="Studio.02.02.00")
        obj = ET.SubElement(root, 'object', {'class': 'AudioFile', 'id': audio_file_id})

        # Add assetPath property
        prop_path = ET.SubElement(obj, 'property', name='assetPath')
        value_path = ET.SubElement(prop_path, 'value')
        value_path.text = asset_relative_path

        # Add frequencyInKHz property
        prop_freq = ET.SubElement(obj, 'property', name='frequencyInKHz')
        value_freq = ET.SubElement(prop_freq, 'value')
        value_freq.text = str(frequency_khz)

        # Add channelCount property
        prop_channels = ET.SubElement(obj, 'property', name='channelCount')
        value_channels = ET.SubElement(prop_channels, 'value')
        value_channels.text = str(channel_count)

        # Add length property
        prop_length = ET.SubElement(obj, 'property', name='length')
        value_length = ET.SubElement(prop_length, 'value')
        value_length.text = str(length_seconds)

        # Add masterAssetFolder relationship
        rel = ET.SubElement(obj, 'relationship', name='masterAssetFolder')
        dest = ET.SubElement(rel, 'destination')
        dest.text = self.workspace['masterAssetFolder']

        # Ensure AudioFile directory exists
        audio_file_dir = self.metadata_path / "AudioFile"
        audio_file_dir.mkdir(exist_ok=True)

        # Write XML to file
        audio_file_xml_path = audio_file_dir / f"{audio_file_id}.xml"
        self._write_pretty_xml(root, audio_file_xml_path)

        return audio_file_id


class AudioMatcher:
    """Handles intelligent matching between audio files and event templates"""

    @staticmethod
    def collect_audio_files(directory: str) -> List[Dict]:
        """Collect all audio files from directory"""
        audio_extensions = {'.wav', '.mp3', '.ogg', '.flac', '.aif', '.aiff'}
        files = []

        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext in audio_extensions:
                    full_path = Path(root) / filename
                    base_name = Path(filename).stem

                    files.append({
                        'path': str(full_path),
                        'filename': filename,
                        'basename': base_name
                    })

        return files

    @staticmethod
    def build_event_name(prefix: str, character: str, template_name: str) -> str:
        """Build event name from template"""
        # Extract suffix from template (last part after underscore)
        parts = template_name.split('_')
        suffix = parts[-1]
        return f"{prefix}_{character}_{suffix}"

    @staticmethod
    def match_files_to_events(audio_files: List[Dict], prefix: str, character: str) -> Dict[str, List[Dict]]:
        """Group audio files by their base names to create events

        Args:
            audio_files: List of audio file dictionaries
            prefix: Event prefix (e.g., 'Cat')
            character: Character name (e.g., 'Infiltrator')

        Returns:
            Dictionary mapping event names to their audio files
            Example: {'Cat_Infiltrator_Attack': [file1, file2], 'Cat_Infiltrator_Jump': [file3]}
        """
        groups = {}

        for file in audio_files:
            # Remove trailing numbers (_01, _02, etc.) to get base event name
            basename = file['basename']

            # Try to match pattern: Prefix_CharacterName_Suffix[_##]
            # Example: Cat_Infiltrator_Attack_01 -> Cat_Infiltrator_Attack
            pattern = f"{prefix}_{character}_"

            if basename.startswith(pattern):
                # Remove prefix to get suffix part
                suffix_part = basename[len(pattern):]

                # Remove trailing numbers if present
                if '_' in suffix_part:
                    # Check if last part is a number
                    parts = suffix_part.rsplit('_', 1)
                    if parts[-1].isdigit():
                        event_suffix = parts[0]
                    else:
                        event_suffix = suffix_part
                else:
                    event_suffix = suffix_part

                # Build full event name
                event_name = f"{prefix}_{character}_{event_suffix}"

                if event_name not in groups:
                    groups[event_name] = []
                groups[event_name].append(file)

        return groups


class MocoAutoImportGUI:
    """Main GUI application"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Moco Auto Import - FMOD Asset Importer")
        self.root.geometry("900x700")

        self.project: Optional[FMODProject] = None
        self.config = {
            'project_path': '',
            'media_path': '',
            'template_folder_id': '',
            'prefix': 'Cat',
            'character_name': 'Infiltrator',
            'bank_name': 'CatInfiltrator',
            'destination_folder_id': ''
        }

        self._create_widgets()
        self._load_default_settings()

        self.media_lookup: Dict[str, List[str]] = {}

    def _init_media_lookup(self, audio_files: List[Dict]):
        """Create lookup from filename to available file paths"""
        self.media_lookup = {}
        for info in audio_files:
            self.media_lookup.setdefault(info['filename'], []).append(info['path'])

    def _consume_media_path(self, filename: str, expected_path: Optional[str] = None) -> Optional[str]:
        """Return and remove a media path associated with the filename"""
        paths = self.media_lookup.get(filename)
        if not paths:
            return expected_path

        if expected_path and expected_path in paths:
            paths.remove(expected_path)
            path = expected_path
        else:
            path = paths.pop(0)

        if not paths:
            self.media_lookup.pop(filename, None)

        return path

    def _create_widgets(self):
        """Create GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Project selection
        ttk.Label(main_frame, text="FMOD Project (.fspro):").grid(row=0, column=0, sticky=tk.W, pady=5)

        project_frame = ttk.Frame(main_frame)
        project_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.project_entry = ttk.Entry(project_frame, width=40)
        self.project_entry.grid(row=0, column=0, padx=(0, 5))
        ttk.Button(project_frame, text="Browse...", command=self.browse_project).grid(row=0, column=1, padx=5)
        ttk.Button(project_frame, text="Load", command=self.load_project).grid(row=0, column=2, padx=5)
        ttk.Button(project_frame, text="Reload Scripts", command=self.reload_fmod_scripts).grid(row=0, column=3, padx=5)

        # Media files path
        ttk.Label(main_frame, text="Media Files Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        media_frame = ttk.Frame(main_frame)
        media_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.media_entry = ttk.Entry(media_frame, width=60)
        self.media_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(media_frame, text="Browse...", command=self.browse_media).grid(row=0, column=1, padx=5)
        media_frame.columnconfigure(0, weight=1)

        # Template folder
        ttk.Label(main_frame, text="Template Folder:").grid(row=4, column=0, sticky=tk.W, pady=5)
        template_frame = ttk.Frame(main_frame)
        template_frame.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.template_var = tk.StringVar(value="(No folder selected)")
        self.template_label = ttk.Label(template_frame, textvariable=self.template_var, relief="sunken", width=55)
        self.template_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(template_frame, text="Select...", command=self.select_template_folder).grid(row=0, column=1, padx=5)
        template_frame.columnconfigure(0, weight=1)

        # Prefix
        ttk.Label(main_frame, text="Prefix:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.prefix_entry = ttk.Entry(main_frame, width=60)
        self.prefix_entry.insert(0, "")
        # Add placeholder effect
        self.prefix_entry.insert(0, "e.g. Cat")
        self.prefix_entry.config(foreground='gray')
        self.prefix_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.prefix_entry, 'e.g. Cat'))
        self.prefix_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.prefix_entry, 'e.g. Cat'))
        self.prefix_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Character name
        ttk.Label(main_frame, text="Character Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.character_entry = ttk.Entry(main_frame, width=60)
        self.character_entry.insert(0, "e.g. Infiltrator")
        self.character_entry.config(foreground='gray')
        self.character_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.character_entry, 'e.g. Infiltrator'))
        self.character_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.character_entry, 'e.g. Infiltrator'))
        self.character_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Destination folder (moved before Bank)
        ttk.Label(main_frame, text="Event Folder:").grid(row=6, column=0, sticky=tk.W, pady=5)
        dest_frame = ttk.Frame(main_frame)
        dest_frame.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.dest_var = tk.StringVar(value="(No folder selected)")
        self.dest_label = ttk.Label(dest_frame, textvariable=self.dest_var, relief="sunken", width=55)
        self.dest_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dest_frame, text="Select...", command=self.select_destination_folder).grid(row=0, column=1, padx=5)
        dest_frame.columnconfigure(0, weight=1)

        # Bank selection
        ttk.Label(main_frame, text="Bank:").grid(row=7, column=0, sticky=tk.W, pady=5)
        bank_frame = ttk.Frame(main_frame)
        bank_frame.grid(row=7, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.bank_var = tk.StringVar(value="(No bank selected)")
        self.bank_label = ttk.Label(bank_frame, textvariable=self.bank_var, relief="sunken", width=55)
        self.bank_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(bank_frame, text="Select...", command=self.select_bank).grid(row=0, column=1, padx=5)
        bank_frame.columnconfigure(0, weight=1)

        # Bus assignment
        ttk.Label(main_frame, text="Bus:").grid(row=8, column=0, sticky=tk.W, pady=5)
        bus_frame = ttk.Frame(main_frame)
        bus_frame.grid(row=8, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.bus_var = tk.StringVar(value="(No bus selected)")
        self.bus_label = ttk.Label(bus_frame, textvariable=self.bus_var, relief="sunken", width=55)
        self.bus_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(bus_frame, text="Select...", command=self.select_bus).grid(row=0, column=1, padx=5)
        bus_frame.columnconfigure(0, weight=1)

        # Audio Asset Folder
        ttk.Label(main_frame, text="Audio Asset Folder:").grid(row=5, column=0, sticky=tk.W, pady=5)
        asset_frame = ttk.Frame(main_frame)
        asset_frame.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.asset_var = tk.StringVar(value="(No asset folder selected)")
        self.asset_label = ttk.Label(asset_frame, textvariable=self.asset_var, relief="sunken", width=55)
        self.asset_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(asset_frame, text="Select...", command=self.select_asset_folder).grid(row=0, column=1, padx=5)
        asset_frame.columnconfigure(0, weight=1)

        # Preview section - Events matched to media
        ttk.Label(main_frame, text="Preview - Matched Events:").grid(row=9, column=0, sticky=tk.NW, pady=10)

        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Create Treeview with 2 columns (removed 'Events → Assets' column)
        columns = ('bank', 'bus')
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='tree headings', height=8)

        # Define headings
        self.preview_tree.heading('#0', text='Event Name')
        self.preview_tree.heading('bank', text='Bank')
        self.preview_tree.heading('bus', text='Bus')

        # Define column widths
        self.preview_tree.column('#0', width=500)
        self.preview_tree.column('bank', width=150)
        self.preview_tree.column('bus', width=150)

        self.preview_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_tree['yscrollcommand'] = scrollbar.set

        # Drag & Drop support for preview tree (for media files only)
        self.preview_tree.bind('<ButtonPress-1>', self._on_preview_tree_press)
        self.preview_tree.bind('<B1-Motion>', self._on_preview_tree_drag)
        self.preview_tree.bind('<ButtonRelease-1>', self._on_preview_tree_release)

        # Delete key support for removing media files from preview tree
        self.preview_tree.bind('<Delete>', self._on_preview_tree_delete)

        # Orphans section
        ttk.Label(main_frame, text="Orphans:").grid(row=11, column=0, sticky=tk.NW, pady=10)

        orphans_frame = ttk.Frame(main_frame)
        orphans_frame.grid(row=12, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Left side - Orphan Events
        orphan_events_frame = ttk.Frame(orphans_frame)
        orphan_events_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        ttk.Label(orphan_events_frame, text="Orphan Events (no media assigned)").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.orphan_events_list = tk.Listbox(orphan_events_frame, height=8, selectmode=tk.EXTENDED)
        self.orphan_events_list.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        events_scrollbar = ttk.Scrollbar(orphan_events_frame, orient=tk.VERTICAL, command=self.orphan_events_list.yview)
        events_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.orphan_events_list['yscrollcommand'] = events_scrollbar.set

        # Mouse wheel scrolling support
        self.orphan_events_list.bind('<MouseWheel>', self._on_mousewheel)
        self.orphan_events_list.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.orphan_events_list.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down

        orphan_events_frame.columnconfigure(0, weight=1)
        orphan_events_frame.rowconfigure(1, weight=1)

        # Right side - Orphan Media Files
        orphan_media_frame = ttk.Frame(orphans_frame)
        orphan_media_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        ttk.Label(orphan_media_frame, text="Orphan Media Files (Drag to assign, or Right-click)").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.orphan_media_list = tk.Listbox(orphan_media_frame, height=8, selectmode=tk.EXTENDED)
        self.orphan_media_list.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        media_scrollbar = ttk.Scrollbar(orphan_media_frame, orient=tk.VERTICAL, command=self.orphan_media_list.yview)
        media_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.orphan_media_list['yscrollcommand'] = media_scrollbar.set

        # Context menu for orphan media files
        self.orphan_media_menu = tk.Menu(self.root, tearoff=0)
        self.orphan_media_list.bind('<Button-3>', self._show_orphan_media_context_menu)

        # Drag & Drop support for orphan media
        # Use ButtonPress-1 to capture initial position, then detect drag in Motion
        self.orphan_media_list.bind('<ButtonPress-1>', self._on_listbox_press)
        self.orphan_media_list.bind('<B1-Motion>', self._on_drag_motion)
        self.orphan_media_list.bind('<ButtonRelease-1>', self._on_listbox_release)

        # Mouse wheel scrolling support
        self.orphan_media_list.bind('<MouseWheel>', self._on_mousewheel)
        self.orphan_media_list.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.orphan_media_list.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down

        # Override the default Listbox bindings that cause drag-select behavior
        # By changing bindtags order, our handlers run first and can prevent default behavior
        bindtags = list(self.orphan_media_list.bindtags())
        bindtags.remove('Listbox')  # Remove default Listbox class bindings
        self.orphan_media_list.bindtags(tuple(bindtags))

        # Add keyboard navigation bindings since we removed default Listbox bindings
        self.orphan_media_list.bind('<Up>', self._on_listbox_up)
        self.orphan_media_list.bind('<Down>', self._on_listbox_down)
        self.orphan_media_list.bind('<Control-a>', self._on_listbox_select_all)

        # Drop targets
        self.preview_tree.bind('<Enter>', lambda e: self._set_drop_target('preview'))
        self.orphan_events_list.bind('<Enter>', lambda e: self._set_drop_target('orphan'))

        # Store drag data
        self._drag_data = {
            'items': [],
            'indices': [],
            'start_x': 0,
            'start_y': 0,
            'dragging': False,
            'drop_target': None,
            'source_widget': None  # Track which widget initiated the drag
        }
        self._drag_threshold = 5  # pixels to move before starting drag
        self._drag_highlight_items = []  # Store items to highlight during drag

        # Create drag feedback label (hidden by default)
        self._drag_label = tk.Label(self.root, text="", bg="lightyellow", relief=tk.RIDGE,
                                     borderwidth=2, font=('Segoe UI', 9))
        self._drag_label.place_forget()  # Hide initially

        orphan_media_frame.columnconfigure(0, weight=1)
        orphan_media_frame.rowconfigure(1, weight=1)

        # Configure orphans_frame columns to split equally
        orphans_frame.columnconfigure(0, weight=1)
        orphans_frame.columnconfigure(1, weight=1)
        orphans_frame.rowconfigure(0, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=13, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Analyze", command=self.analyze, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Import", command=self.import_assets, width=15).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Settings", command=self.open_settings, width=15).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.root.quit, width=15).grid(row=0, column=3, padx=5)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(10, weight=1)
        main_frame.rowconfigure(12, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

    def _clear_placeholder(self, entry: ttk.Entry, placeholder: str):
        """Clear placeholder text when entry gets focus"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(foreground='black')

    def _restore_placeholder(self, entry: ttk.Entry, placeholder: str):
        """Restore placeholder if entry is empty"""
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(foreground='gray')

    def _get_entry_value(self, entry: ttk.Entry, placeholder: str) -> str:
        """Get actual value from entry (excluding placeholder)"""
        value = entry.get()
        return '' if value == placeholder else value

    def _center_dialog(self, dialog: tk.Toplevel):
        """Center dialog relative to main window"""
        dialog.update_idletasks()

        # Get main window position and size
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        # Get dialog size
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()

        # Calculate center position
        x = main_x + (main_width - dialog_width) // 2
        y = main_y + (main_height - dialog_height) // 2

        # Ensure dialog stays on screen
        if x < 0:
            x = 0
        if y < 0:
            y = 0

        dialog.geometry(f"+{x}+{y}")

    def browse_project(self):
        """Browse for FMOD project file"""
        filename = filedialog.askopenfilename(
            title="Select FMOD Project",
            filetypes=[("FMOD Project", "*.fspro"), ("All Files", "*.*")]
        )

        if filename:
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, filename)
            self.load_project(filename)

    def reload_fmod_scripts(self):
        """Force FMOD Studio to reload scripts"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        try:
            project_path = str(self.project.project_path)

            # Create a temporary empty JavaScript file to trigger script reload
            temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8')
            temp_script.write('// Trigger script reload\nstudio.system.message("Scripts reloaded");')
            temp_script.close()

            # Execute the script via FMOD Studio console API
            if platform.system() == "Windows":
                # Use fmod_console.exe to execute the script
                console_path = self._find_fmod_console()
                if console_path:
                    subprocess.run([
                        console_path,
                        project_path,
                        "--execute-script", temp_script.name
                    ], check=True)
                    messagebox.showinfo("Success", "FMOD scripts reloaded successfully")
                else:
                    messagebox.showwarning("Warning", "FMOD Console not found. Please reload scripts manually in FMOD Studio (File > Reload Scripts)")
            else:
                messagebox.showinfo("Info", "Please reload scripts manually in FMOD Studio (File > Reload Scripts)")

            # Cleanup temp file
            try:
                os.unlink(temp_script.name)
            except:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload scripts:\n{str(e)}\n\nPlease reload manually in FMOD Studio (File > Reload Scripts)")

    def _find_fmod_console(self) -> Optional[str]:
        """Find FMOD Console executable"""
        # Common installation paths for FMOD Studio
        possible_paths = [
            r"C:\Program Files (x86)\FMOD SoundSystem\FMOD Studio 2.02.25\fmod_console.exe",
            r"C:\Program Files\FMOD SoundSystem\FMOD Studio 2.02.25\fmod_console.exe",
            r"C:\Program Files (x86)\FMOD SoundSystem\FMOD Studio\fmod_console.exe",
            r"C:\Program Files\FMOD SoundSystem\FMOD Studio\fmod_console.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _find_fmod_studio_exe(self) -> Optional[str]:
        """Find FMOD Studio command line executable (fmodstudiocl.exe)"""
        # Check settings first
        settings = self.load_settings()
        if settings.get('fmod_exe_path') and os.path.exists(settings['fmod_exe_path']):
            # If it's FMOD Studio.exe, try to find fmodstudiocl.exe in same directory
            if settings['fmod_exe_path'].endswith("FMOD Studio.exe"):
                cl_path = settings['fmod_exe_path'].replace("FMOD Studio.exe", "fmodstudiocl.exe")
                if os.path.exists(cl_path):
                    return cl_path
            return settings['fmod_exe_path']

        # Search for FMOD Studio CL in common installation directories
        base_dirs = [
            r"C:\Program Files\FMOD SoundSystem",
            r"C:\Program Files (x86)\FMOD SoundSystem"
        ]

        for base_dir in base_dirs:
            if os.path.exists(base_dir):
                # Look for any FMOD Studio version folder
                for folder in os.listdir(base_dir):
                    if folder.startswith("FMOD Studio"):
                        # Prefer command line version
                        cl_path = os.path.join(base_dir, folder, "fmodstudiocl.exe")
                        if os.path.exists(cl_path):
                            return cl_path
                        # Fallback to regular exe
                        exe_path = os.path.join(base_dir, folder, "FMOD Studio.exe")
                        if os.path.exists(exe_path):
                            return exe_path

        return None

    def browse_media(self):
        """Browse for media files directory"""
        directory = filedialog.askdirectory(title="Select Media Files Directory")

        if directory:
            self.media_entry.delete(0, tk.END)
            self.media_entry.insert(0, directory)

    def select_template_folder(self):
        """Open tree dialog to select template folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_folder_tree_dialog("Select Template Folder")
        if selected:
            folder_name, folder_id = selected
            self.template_var.set(folder_name)
            self.selected_template_id = folder_id

    def select_destination_folder(self):
        """Open tree dialog to select destination folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_folder_tree_dialog("Select Destination Folder")
        if selected:
            folder_name, folder_id = selected
            self.dest_var.set(folder_name)
            self.selected_dest_id = folder_id

    def select_bank(self):
        """Open tree dialog to select bank"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_hierarchical_dialog(
            "Select Bank",
            self.project.banks,
            create_fn=lambda name, parent_id: self.project.create_bank(name),
            delete_fn=lambda item_id: self.project.delete_bank(item_id)
        )
        if selected:
            bank_name, bank_id = selected
            self.bank_var.set(bank_name)
            self.selected_bank_id = bank_id

    def select_bus(self):
        """Open tree dialog to select bus"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_hierarchical_dialog(
            "Select Bus",
            self.project.buses,
            create_fn=lambda name, parent_id: self.project.create_bus(name),
            delete_fn=lambda item_id: self.project.delete_bus(item_id)
        )
        if selected:
            bus_name, bus_id = selected
            self.bus_var.set(bus_name)
            self.selected_bus_id = bus_id

    def select_asset_folder(self):
        """Open tree dialog to select asset folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_asset_tree_dialog("Select Audio Asset Folder")
        if selected:
            asset_path, asset_id = selected
            self.asset_var.set(asset_path)
            self.selected_asset_id = asset_id

    def _show_crud_list_dialog(self, title: str, items: dict, create_fn, delete_fn):
        """Show a dialog with list view for CRUD operations"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create listbox
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        listbox = tk.Listbox(list_frame, selectmode='single')
        listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        listbox['yscrollcommand'] = scrollbar.set

        result = [None]

        def refresh_list():
            """Refresh the listbox sorted A-Z"""
            listbox.delete(0, tk.END)
            if items:
                # Sort items by name A-Z
                sorted_items = sorted(items.values(), key=lambda x: x['name'].lower())
                for item_data in sorted_items:
                    listbox.insert(tk.END, item_data['name'])
            else:
                listbox.insert(tk.END, "(No items found)")

        def on_new():
            """Create new item"""
            name = simpledialog.askstring("New Item", "Enter name:", parent=dialog)
            if name:
                try:
                    create_fn(name)
                    refresh_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create item:\n{str(e)}")

        def on_rename():
            """Rename selected item"""
            selection = listbox.curselection()
            if not selection or not items:
                return

            index = selection[0]
            item_ids = list(items.keys())
            item_id = item_ids[index]
            item_name = items[item_id]['name']

            new_name = simpledialog.askstring("Rename", "Enter new name:",
                                            initialvalue=item_name, parent=dialog)
            if new_name and new_name != item_name:
                try:
                    # Update XML directly
                    item_data = items[item_id]
                    xml_path = item_data['path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    name_elem = root_xml.find(".//property[@name='name']/value")
                    if name_elem is not None:
                        name_elem.text = new_name
                        self.project._write_pretty_xml(root_xml, xml_path)
                        item_data['name'] = new_name
                        refresh_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename:\n{str(e)}")

        def on_delete():
            """Delete selected item"""
            selection = listbox.curselection()
            if not selection or not items:
                return

            index = selection[0]
            item_ids = list(items.keys())
            item_id = item_ids[index]

            try:
                delete_fn(item_id)
                refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item:\n{str(e)}")

        def on_key(event):
            """Handle keyboard shortcuts"""
            if event.keysym == 'F2':
                on_rename()

        listbox.bind('<Key>', on_key)

        def on_select():
            selection = listbox.curselection()
            if selection and items:
                index = selection[0]
                item_ids = list(items.keys())
                item_id = item_ids[index]
                item_name = items[item_id]['name']
                result[0] = (item_name, item_id)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Initial populate
        refresh_list()

        # Edit buttons
        edit_frame = ttk.Frame(frame)
        edit_frame.grid(row=1, column=0, pady=5)
        ttk.Button(edit_frame, text="New", command=on_new, width=12).grid(row=0, column=0, padx=5)
        ttk.Button(edit_frame, text="Rename (F2)", command=on_rename, width=12).grid(row=0, column=1, padx=5)
        ttk.Button(edit_frame, text="Delete", command=on_delete, width=12).grid(row=0, column=2, padx=5)

        # Selection buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=10)
        ttk.Button(button_frame, text="Select", command=on_select, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).grid(row=0, column=1, padx=5)

        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        dialog.wait_window()
        return result[0]

    def _show_hierarchical_dialog(self, title: str, items: dict, create_fn, delete_fn):
        """Show a dialog with tree view for hierarchical items (Banks, Buses)"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Search field
        search_frame = ttk.Frame(frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        search_frame.columnconfigure(1, weight=1)

        # Create treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tree = ttk.Treeview(tree_frame, selectmode='browse')
        tree.heading('#0', text=title)
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree['yscrollcommand'] = scrollbar.set

        result = [None]

        def has_matching_descendant(item_id, search_filter):
            """Check if item or any descendant matches the search filter"""
            if not search_filter:
                return True

            # Check current item
            if item_id in items and search_filter.lower() in items[item_id]['name'].lower():
                return True

            # Check children recursively
            for child_id, child_data in items.items():
                if child_data.get('parent') == item_id:
                    if has_matching_descendant(child_id, search_filter):
                        return True

            return False

        def build_tree(parent_item, parent_id, search_filter=""):
            """Build tree hierarchy with alphabetical sorting and search filter"""
            # Get children and sort alphabetically
            children = [(item_id, item_data) for item_id, item_data in items.items()
                       if item_data.get('parent') == parent_id]
            children.sort(key=lambda x: x[1]['name'].lower())

            for item_id, item_data in children:
                # Apply search filter - show if item or any descendant matches
                if search_filter:
                    if not has_matching_descendant(item_id, search_filter):
                        continue

                node = tree.insert(parent_item, 'end', text=item_data['name'], values=(item_id,))
                build_tree(node, item_id, search_filter)

        def find_root_items():
            """Find root items (items without parent or with None parent), sorted alphabetically"""
            roots = []
            for item_id, item_data in items.items():
                parent = item_data.get('parent')
                if parent is None or parent not in items:
                    roots.append((item_id, item_data))
            roots.sort(key=lambda x: x[1]['name'].lower())
            return roots

        def get_expanded_items():
            """Get list of expanded item IDs"""
            expanded = []
            def check_item(item):
                if tree.item(item, 'open'):
                    values = tree.item(item, 'values')
                    if values:
                        expanded.append(values[0])
                for child in tree.get_children(item):
                    check_item(child)
            for item in tree.get_children():
                check_item(item)
            return expanded

        def expand_all():
            """Expand all tree items"""
            def expand_item(item):
                tree.item(item, open=True)
                for child in tree.get_children(item):
                    expand_item(child)
            for item in tree.get_children():
                expand_item(item)

        def collapse_all():
            """Collapse all tree items"""
            def collapse_item(item):
                for child in tree.get_children(item):
                    tree.item(child, open=False)
                    collapse_item(child)
            for item in tree.get_children():
                tree.item(item, open=True)
                collapse_item(item)

        def restore_expanded_state(expanded_ids):
            """Restore expanded state of items"""
            def restore_item(item):
                values = tree.item(item, 'values')
                if values and values[0] in expanded_ids:
                    tree.item(item, open=True)
                for child in tree.get_children(item):
                    restore_item(child)
            for item in tree.get_children():
                restore_item(item)

        def refresh_tree(search_filter=""):
            """Rebuild tree after changes, preserving expanded state"""
            expanded_ids = get_expanded_items()
            tree.delete(*tree.get_children())

            # Build tree from roots
            roots = find_root_items()
            for root_id, root_data in roots:
                # Apply search filter - show if root or any descendant matches
                if search_filter:
                    if not has_matching_descendant(root_id, search_filter):
                        continue

                root_node = tree.insert('', 'end', text=root_data['name'], values=(root_id,))
                build_tree(root_node, root_id, search_filter)

            restore_expanded_state(expanded_ids)
            if search_filter:
                expand_all()  # Expand all when searching

        # Bind search to refresh tree
        def on_search_change(*args):
            refresh_tree(search_var.get())

        search_var.trace('w', on_search_change)

        def on_new():
            selection = tree.selection()
            parent_id = None
            if selection:
                parent_item = selection[0]
                parent_id = tree.item(parent_item, 'values')[0]

            name = simpledialog.askstring("New Item", "Enter name:", parent=dialog)
            if name:
                try:
                    create_fn(name, parent_id)
                    refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create:\n{str(e)}")

        def on_rename():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            item_name = tree.item(item, 'text')
            item_id = tree.item(item, 'values')[0]

            new_name = simpledialog.askstring("Rename", "Enter new name:",
                                            initialvalue=item_name, parent=dialog)
            if new_name and new_name != item_name:
                try:
                    item_data = items[item_id]
                    xml_path = item_data['path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    name_elem = root_xml.find(".//property[@name='name']/value")
                    if name_elem is not None:
                        name_elem.text = new_name
                        self.project._write_pretty_xml(root_xml, xml_path)
                        item_data['name'] = new_name
                        refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename:\n{str(e)}")

        def on_delete():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            item_id = tree.item(item, 'values')[0]

            try:
                delete_fn(item_id)
                refresh_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete:\n{str(e)}")

        def on_select():
            selection = tree.selection()
            if selection:
                item = selection[0]
                item_name = tree.item(item, 'text')
                item_id = tree.item(item, 'values')[0]
                result[0] = (item_name, item_id)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        def on_key(event):
            """Handle keyboard shortcuts"""
            if event.keysym == 'F2':
                on_rename()

        tree.bind('<Key>', on_key)
        tree.bind('<Double-Button-1>', lambda e: on_select())

        # Initial build
        refresh_tree()
        expand_all()

        # Edit buttons
        edit_frame = ttk.Frame(frame)
        edit_frame.grid(row=2, column=0, pady=5)
        ttk.Button(edit_frame, text="New", command=on_new, width=10).grid(row=0, column=0, padx=2)
        ttk.Button(edit_frame, text="Rename (F2)", command=on_rename, width=12).grid(row=0, column=1, padx=2)
        ttk.Button(edit_frame, text="Delete", command=on_delete, width=10).grid(row=0, column=2, padx=2)
        ttk.Button(edit_frame, text="Expand All", command=expand_all, width=10).grid(row=0, column=3, padx=2)
        ttk.Button(edit_frame, text="Collapse", command=collapse_all, width=10).grid(row=0, column=4, padx=2)

        # Selection buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, pady=10)
        ttk.Button(button_frame, text="Select", command=on_select, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).grid(row=0, column=1, padx=5)

        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        dialog.wait_window()
        return result[0]

    def _show_folder_tree_dialog(self, title: str):
        """Show a dialog with tree view for folder selection"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tree = ttk.Treeview(tree_frame, selectmode='browse')
        tree.heading('#0', text='Event Folders')
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree['yscrollcommand'] = scrollbar.set

        # Build tree hierarchy sorted A-Z
        def build_tree(parent_item, parent_folder_id):
            # Get all child folders and sort them by name A-Z
            child_folders = [(folder_id, folder_data) for folder_id, folder_data in self.project.event_folders.items()
                           if folder_data['parent'] == parent_folder_id]
            child_folders.sort(key=lambda x: x[1]['name'].lower())

            for folder_id, folder_data in child_folders:
                item = tree.insert(parent_item, 'end', text=folder_data['name'], values=(folder_id,))
                build_tree(item, folder_id)

        # Start with master folder
        master_id = self.project.workspace['masterEventFolder']
        master_name = self.project.event_folders[master_id]['name']
        root_item = tree.insert('', 'end', text=master_name, values=(master_id,))
        build_tree(root_item, master_id)

        result = [None]

        def get_expanded_items():
            """Get list of expanded item IDs"""
            expanded = []
            def check_item(item):
                if tree.item(item, 'open'):
                    values = tree.item(item, 'values')
                    if values:
                        expanded.append(values[0])
                for child in tree.get_children(item):
                    check_item(child)
            for item in tree.get_children():
                check_item(item)
            return expanded

        def expand_all():
            """Expand all tree items"""
            def expand_item(item):
                tree.item(item, open=True)
                for child in tree.get_children(item):
                    expand_item(child)
            for item in tree.get_children():
                expand_item(item)

        def collapse_all():
            """Collapse all tree items except root"""
            def collapse_item(item):
                for child in tree.get_children(item):
                    tree.item(child, open=False)
                    collapse_item(child)
            for item in tree.get_children():
                tree.item(item, open=True)  # Keep root open
                collapse_item(item)

        def restore_expanded_state(expanded_ids):
            """Restore expanded state of items"""
            def restore_item(item):
                values = tree.item(item, 'values')
                if values and values[0] in expanded_ids:
                    tree.item(item, open=True)
                for child in tree.get_children(item):
                    restore_item(child)
            for item in tree.get_children():
                restore_item(item)

        def refresh_tree():
            """Rebuild tree after changes, preserving expanded state"""
            expanded_ids = get_expanded_items()
            tree.delete(*tree.get_children())
            master_id = self.project.workspace['masterEventFolder']
            master_name = self.project.event_folders[master_id]['name']
            root_item = tree.insert('', 'end', text=master_name, values=(master_id,))
            build_tree(root_item, master_id)
            restore_expanded_state(expanded_ids)

        def on_new_folder():
            selection = tree.selection()
            if not selection:
                return

            parent_item = selection[0]
            parent_id = tree.item(parent_item, 'values')[0]

            name = simpledialog.askstring("New Folder", "Enter folder name:", parent=dialog)
            if name:
                try:
                    self.project.create_event_folder(name, parent_id)
                    refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create folder:\n{str(e)}")

        def on_rename():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            folder_name = tree.item(item, 'text')
            folder_id = tree.item(item, 'values')[0]

            # Check if it's the master folder
            master_id = self.project.workspace['masterEventFolder']
            if folder_id == master_id:
                return

            new_name = simpledialog.askstring("Rename Folder", "Enter new name:",
                                            initialvalue=folder_name, parent=dialog)
            if new_name and new_name != folder_name:
                try:
                    # Update the name in the XML
                    folder_data = self.project.event_folders[folder_id]
                    xml_path = folder_data['path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    name_elem = root_xml.find(".//property[@name='name']/value")
                    if name_elem is not None:
                        name_elem.text = new_name
                        self.project._write_pretty_xml(root_xml, xml_path)
                        folder_data['name'] = new_name
                        refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename folder:\n{str(e)}")

        def on_delete_folder():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            folder_name = tree.item(item, 'text')
            folder_id = tree.item(item, 'values')[0]

            master_id = self.project.workspace['masterEventFolder']
            if folder_id == master_id:
                return

            try:
                self.project.delete_folder(folder_id)
                refresh_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete folder:\n{str(e)}")

        def on_select():
            selection = tree.selection()
            if selection:
                item = selection[0]
                folder_name = tree.item(item, 'text')
                folder_id = tree.item(item, 'values')[0]
                result[0] = (folder_name, folder_id)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        def on_key(event):
            """Handle keyboard shortcuts"""
            if event.keysym == 'F2':
                on_rename()

        tree.bind('<Key>', on_key)
        tree.bind('<Double-Button-1>', lambda e: on_select())

        # Expand all by default
        expand_all()

        # Edit buttons
        edit_frame = ttk.Frame(frame)
        edit_frame.grid(row=1, column=0, pady=5)
        ttk.Button(edit_frame, text="New", command=on_new_folder, width=10).grid(row=0, column=0, padx=2)
        ttk.Button(edit_frame, text="Rename (F2)", command=on_rename, width=12).grid(row=0, column=1, padx=2)
        ttk.Button(edit_frame, text="Delete", command=on_delete_folder, width=10).grid(row=0, column=2, padx=2)
        ttk.Button(edit_frame, text="Expand All", command=expand_all, width=10).grid(row=0, column=3, padx=2)
        ttk.Button(edit_frame, text="Collapse", command=collapse_all, width=10).grid(row=0, column=4, padx=2)

        # Selection buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=10)
        ttk.Button(button_frame, text="Select", command=on_select, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).grid(row=0, column=1, padx=5)

        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        dialog.wait_window()
        return result[0]

    def _show_asset_tree_dialog(self, title: str):
        """Show a dialog with tree view for asset folder selection"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tree = ttk.Treeview(tree_frame, selectmode='browse')
        tree.heading('#0', text='Asset Folders')
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree['yscrollcommand'] = scrollbar.set

        def build_path_hierarchy():
            """Build a hierarchical structure from asset paths"""
            # Create a dict to store path components: path -> (asset_id, full_path)
            path_tree = {}

            # First pass: collect all unique path components
            for asset_id, asset_data in self.project.asset_folders.items():
                asset_path = asset_data['path']
                if not asset_path:
                    continue

                # Split path into components (e.g., "Characters/Cat Boss Rich/" -> ["Characters", "Cat Boss Rich"])
                parts = [p for p in asset_path.split('/') if p]

                # Build intermediate paths
                for i in range(len(parts)):
                    partial_path = '/'.join(parts[:i+1]) + '/'
                    # Only store if it's the actual asset folder
                    if partial_path == asset_path:
                        path_tree[partial_path] = (asset_id, asset_path)
                    elif partial_path not in path_tree:
                        # Create placeholder for intermediate paths
                        path_tree[partial_path] = (None, partial_path)

            return path_tree

        def build_tree():
            """Build tree view from path hierarchy"""
            path_tree = build_path_hierarchy()

            # Get master asset folder ID
            master_id = self.project.workspace['masterAssetFolder']

            # Find master asset folder name (it should be in asset_folders)
            master_name = "Master Asset Folder"
            for asset_id, asset_data in self.project.asset_folders.items():
                if asset_id == master_id:
                    master_name = asset_data['path'].rstrip('/') if asset_data['path'] else master_name
                    break

            # Insert root (master asset folder)
            root_item = tree.insert('', 'end', text=master_name, values=(master_id, ''))

            # Create a mapping from path to tree item
            item_map = {'': root_item}

            # Sort paths to ensure parents are processed before children (case-insensitive A-Z)
            sorted_paths = sorted(path_tree.keys(), key=lambda x: x.lower())

            for path in sorted_paths:
                asset_id, full_path = path_tree[path]

                # Get display name (last component of path)
                display_name = path.rstrip('/').split('/')[-1] if path.rstrip('/') else path

                # Find parent path
                parts = [p for p in path.split('/') if p]
                if len(parts) > 1:
                    parent_path = '/'.join(parts[:-1]) + '/'
                else:
                    parent_path = ''

                # Get parent item
                parent_item = item_map.get(parent_path, root_item)

                # Insert item
                item = tree.insert(parent_item, 'end', text=display_name, values=(asset_id or '', full_path))
                item_map[path] = item

        build_tree()

        result = [None]

        def get_expanded_items():
            """Get list of expanded item paths"""
            expanded = []
            def check_item(item):
                if tree.item(item, 'open'):
                    values = tree.item(item, 'values')
                    if values and len(values) > 1:
                        expanded.append(values[1])  # Store the path
                for child in tree.get_children(item):
                    check_item(child)
            for item in tree.get_children():
                check_item(item)
            return expanded

        def expand_all():
            """Expand all tree items"""
            def expand_item(item):
                tree.item(item, open=True)
                for child in tree.get_children(item):
                    expand_item(child)
            for item in tree.get_children():
                expand_item(item)

        def collapse_all():
            """Collapse all tree items except root"""
            def collapse_item(item):
                for child in tree.get_children(item):
                    tree.item(child, open=False)
                    collapse_item(child)
            for item in tree.get_children():
                tree.item(item, open=True)  # Keep root open
                collapse_item(item)

        def restore_expanded_state(expanded_paths):
            """Restore expanded state of items by path"""
            def restore_item(item):
                values = tree.item(item, 'values')
                if values and len(values) > 1 and values[1] in expanded_paths:
                    tree.item(item, open=True)
                for child in tree.get_children(item):
                    restore_item(child)
            for item in tree.get_children():
                restore_item(item)

        def refresh_tree():
            """Rebuild tree after changes, preserving expanded state"""
            expanded_paths = get_expanded_items()
            tree.delete(*tree.get_children())
            build_tree()
            restore_expanded_state(expanded_paths)

        def on_new_folder():
            """Create a new asset folder"""
            selection = tree.selection()
            if not selection:
                return

            parent_item = selection[0]
            values = tree.item(parent_item, 'values')
            parent_path = values[1] if len(values) > 1 else ''

            name = simpledialog.askstring("New Asset Folder", "Enter folder name:", parent=dialog)
            if name:
                # Remove any slashes from the name
                name = name.replace('/', '')
                if not name:
                    messagebox.showerror("Error", "Invalid folder name")
                    return

                try:
                    # Create new path
                    new_path = parent_path + name + '/'

                    # Check if path already exists
                    for asset_data in self.project.asset_folders.values():
                        if asset_data['path'] == new_path:
                            messagebox.showerror("Error", "Asset folder with this path already exists")
                            return

                    # Create new asset folder
                    asset_id = "{" + str(uuid.uuid4()) + "}"
                    master_id = self.project.workspace['masterAssetFolder']

                    # Create XML structure
                    root_elem = ET.Element('objects', serializationModel="Studio.02.02.00")
                    obj = ET.SubElement(root_elem, 'object', {'class': 'EncodableAsset', 'id': asset_id})

                    # Add assetPath property
                    prop = ET.SubElement(obj, 'property', name='assetPath')
                    value = ET.SubElement(prop, 'value')
                    value.text = new_path

                    # Add masterAssetFolder relationship
                    rel = ET.SubElement(obj, 'relationship', name='masterAssetFolder')
                    dest = ET.SubElement(rel, 'destination')
                    dest.text = master_id

                    # Write to file
                    asset_file = self.project.metadata_path / "Asset" / f"{asset_id}.xml"
                    self.project._write_pretty_xml(root_elem, asset_file)

                    # Update internal structure
                    self.project.asset_folders[asset_id] = {
                        'path': new_path,
                        'xml_path': asset_file,
                        'master_folder': master_id
                    }

                    refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create asset folder:\n{str(e)}")

        def on_rename():
            """Rename an existing asset folder"""
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            values = tree.item(item, 'values')

            if len(values) < 2:
                return

            asset_id = values[0]
            current_path = values[1]

            # Can't rename master folder or empty paths
            if not asset_id or not current_path:
                return

            # Check if it's the master asset folder
            master_id = self.project.workspace['masterAssetFolder']
            if asset_id == master_id:
                return

            # Get current name (last component)
            current_name = current_path.rstrip('/').split('/')[-1]

            new_name = simpledialog.askstring("Rename Asset Folder", "Enter new name:",
                                            initialvalue=current_name, parent=dialog)
            if new_name and new_name != current_name:
                # Remove any slashes from the name
                new_name = new_name.replace('/', '')
                if not new_name:
                    messagebox.showerror("Error", "Invalid folder name")
                    return

                try:
                    # Build new path
                    parts = current_path.rstrip('/').split('/')
                    parts[-1] = new_name
                    new_path = '/'.join(parts) + '/'

                    # Check if new path already exists
                    for aid, asset_data in self.project.asset_folders.items():
                        if aid != asset_id and asset_data['path'] == new_path:
                            messagebox.showerror("Error", "Asset folder with this path already exists")
                            return

                    # Update the XML
                    asset_data = self.project.asset_folders[asset_id]
                    xml_path = asset_data['xml_path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    path_elem = root_xml.find(".//property[@name='assetPath']/value")
                    if path_elem is not None:
                        path_elem.text = new_path
                        self.project._write_pretty_xml(root_xml, xml_path)
                        asset_data['path'] = new_path

                        # Also update any child folders
                        for aid, adata in self.project.asset_folders.items():
                            if aid != asset_id and adata['path'].startswith(current_path):
                                # Update child path
                                child_xml_path = adata['xml_path']
                                child_tree = ET.parse(child_xml_path)
                                child_root = child_tree.getroot()
                                child_path_elem = child_root.find(".//property[@name='assetPath']/value")
                                if child_path_elem is not None:
                                    old_child_path = child_path_elem.text
                                    new_child_path = old_child_path.replace(current_path, new_path, 1)
                                    child_path_elem.text = new_child_path
                                    self.project._write_pretty_xml(child_root, child_xml_path)
                                    adata['path'] = new_child_path

                        refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename asset folder:\n{str(e)}")

        def on_delete_folder():
            """Delete an asset folder"""
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            values = tree.item(item, 'values')

            if len(values) < 2:
                return

            asset_id = values[0]
            current_path = values[1]

            # Can't delete master folder or empty
            if not asset_id or not current_path:
                return

            master_id = self.project.workspace['masterAssetFolder']
            if asset_id == master_id:
                return

            try:
                # Delete the XML file
                asset_data = self.project.asset_folders[asset_id]
                xml_path = asset_data['xml_path']
                if xml_path.exists():
                    xml_path.unlink()

                # Remove from internal structure
                del self.project.asset_folders[asset_id]

                refresh_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete asset folder:\n{str(e)}")

        def on_select():
            """Select the current asset folder"""
            selection = tree.selection()
            if selection:
                item = selection[0]
                values = tree.item(item, 'values')
                if len(values) >= 2:
                    asset_id = values[0]
                    asset_path = values[1]
                    result[0] = (asset_path, asset_id)
                    dialog.destroy()

        def on_cancel():
            dialog.destroy()

        def on_key(event):
            """Handle keyboard shortcuts"""
            if event.keysym == 'F2':
                on_rename()

        tree.bind('<Key>', on_key)
        tree.bind('<Double-Button-1>', lambda e: on_select())

        # Expand all by default
        expand_all()

        # Edit buttons
        edit_frame = ttk.Frame(frame)
        edit_frame.grid(row=1, column=0, pady=5)
        ttk.Button(edit_frame, text="New", command=on_new_folder, width=10).grid(row=0, column=0, padx=2)
        ttk.Button(edit_frame, text="Rename (F2)", command=on_rename, width=12).grid(row=0, column=1, padx=2)
        ttk.Button(edit_frame, text="Delete", command=on_delete_folder, width=10).grid(row=0, column=2, padx=2)
        ttk.Button(edit_frame, text="Expand All", command=expand_all, width=10).grid(row=0, column=3, padx=2)
        ttk.Button(edit_frame, text="Collapse", command=collapse_all, width=10).grid(row=0, column=4, padx=2)

        # Selection buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=10)
        ttk.Button(button_frame, text="Select", command=on_select, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).grid(row=0, column=1, padx=5)

        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        dialog.wait_window()
        return result[0]


    def load_project(self, project_path: str = None):
        """Load FMOD project and populate dropdowns"""
        try:
            # Use provided path or get from entry field
            if project_path is None:
                project_path = self.project_entry.get()

            if not project_path or not os.path.exists(project_path):
                messagebox.showwarning("Warning", "Please select a valid FMOD project file")
                return

            self.project = FMODProject(project_path)

            # Initialize selection variables
            self.selected_template_id = None
            self.selected_dest_id = None
            self.selected_bank_id = None
            self.selected_bus_id = None
            self.selected_asset_id = None

            # Project loaded successfully - no popup needed

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project:\n{str(e)}")

    def analyze(self):
        """Analyze what will be imported and populate preview tree"""
        try:
            # Validate inputs
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            media_path = self.media_entry.get()
            if not media_path or not os.path.exists(media_path):
                messagebox.showwarning("Warning", "Please select a valid media directory")
                return

            # Get config values (check for placeholders)
            prefix = self._get_entry_value(self.prefix_entry, 'e.g. Cat')
            character = self._get_entry_value(self.character_entry, 'e.g. Infiltrator')

            if not prefix or not character:
                messagebox.showwarning("Warning", "Please fill in Prefix and Character Name")
                return

            # Get destination folder
            if not self.selected_dest_id:
                messagebox.showwarning("Warning", "Please select a destination folder")
                return
            dest_folder_name = self.dest_var.get()
            dest_folder_id = self.selected_dest_id

            # Get bank
            if not self.selected_bank_id:
                messagebox.showwarning("Warning", "Please select a bank")
                return
            bank_name = self.bank_var.get()

            # Get bus
            if not self.selected_bus_id:
                messagebox.showwarning("Warning", "Please select a bus")
                return
            bus = self.bus_var.get()

            # Clear existing preview and orphan lists
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            self.orphan_events_list.delete(0, tk.END)
            self.orphan_media_list.delete(0, tk.END)

            # Get template folder
            if not self.selected_template_id:
                messagebox.showwarning("Warning", "Please select a template folder")
                return

            # Load events from template folder
            template_events = self.project.get_events_in_folder(self.selected_template_id)

            if not template_events:
                messagebox.showwarning("Warning", "No events found in template folder")
                return

            # Collect audio files
            audio_files = AudioMatcher.collect_audio_files(media_path)

            if not audio_files:
                messagebox.showinfo("Info", "No audio files found in the selected directory")
                return

            # Build expected event names by replacing template prefix/character with user input
            # Expected template format: "TemplatePrefix_TemplateCharacter_Suffix"
            # User wants: "UserPrefix_UserCharacter_Suffix"

            # First, extract the template prefix and character from the first event
            # Assume template events follow pattern: Prefix_Character_Suffix
            template_prefix = None
            template_character = None

            if template_events:
                first_event_name = template_events[0]['name']
                parts = first_event_name.split('_')
                if len(parts) >= 3:
                    template_prefix = parts[0]
                    template_character = parts[1]

            # Create mapping of expected event names (with user's prefix/character) to template events
            expected_events = {}
            for template_event in template_events:
                template_name = template_event['name']

                # Replace template prefix/character with user's input
                if template_prefix and template_character:
                    # Replace first two parts (prefix_character) with user's values
                    parts = template_name.split('_', 2)  # Split into max 3 parts
                    if len(parts) >= 3:
                        suffix = parts[2]  # Everything after the second underscore
                        expected_name = f"{prefix}_{character}_{suffix}"
                    else:
                        # Fallback if naming convention doesn't match
                        expected_name = template_name.replace(template_prefix, prefix).replace(template_character, character)
                else:
                    # Can't determine template pattern, just do simple replacement
                    expected_name = template_name

                expected_events[expected_name] = template_event

            # Match audio files to expected events
            matches = AudioMatcher.match_files_to_events(audio_files, prefix, character)

            # Track which events and media were matched
            matched_events = set()
            assigned_media = set()

            # Populate matched events tree
            for event_name, files in matches.items():
                if event_name in expected_events:
                    matched_events.add(event_name)

                    # Insert parent item (event)
                    parent = self.preview_tree.insert('', 'end', text=event_name,
                                                       values=(bank_name, bus))

                    # Insert child items (audio files)
                    for file_info in files:
                        self.preview_tree.insert(parent, 'end', text=f"  → {file_info['filename']}",
                                                 values=('', ''))
                        assigned_media.add(file_info['filename'])

            # Find orphan events (template events without matching media) - sorted A-Z
            orphan_events = [name for name in expected_events.keys() if name not in matched_events]
            orphan_events.sort()
            for expected_name in orphan_events:
                self.orphan_events_list.insert(tk.END, expected_name)

            # Find orphan media files (media not assigned to any expected event) - sorted A-Z
            orphan_media = [audio_file['filename'] for audio_file in audio_files if audio_file['filename'] not in assigned_media]
            orphan_media.sort()
            for media_file in orphan_media:
                self.orphan_media_list.insert(tk.END, media_file)

            orphan_media_count = self.orphan_media_list.size()
            orphan_events_count = self.orphan_events_list.size()
            matched_count = len(matched_events)

            messagebox.showinfo("Success",
                f"Analysis complete!\n\n"
                f"Template events: {len(expected_events)}\n"
                f"Matched events: {matched_count}\n"
                f"Orphan events: {orphan_events_count}\n\n"
                f"Audio files found: {len(audio_files)}\n"
                f"Audio files assigned: {len(assigned_media)}\n"
                f"Orphan media files: {orphan_media_count}\n\n"
                f"Destination: {dest_folder_name}\n"
                f"Bank: {bank_name}\n"
                f"Bus: {bus}")

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")

    def _show_orphan_media_context_menu(self, event):
        """Show context menu for orphan media files"""
        # Get selected media files
        selected_indices = self.orphan_media_list.curselection()
        if not selected_indices:
            return

        # Clear previous menu items
        self.orphan_media_menu.delete(0, tk.END)

        # Get all orphan events and sort them A-Z
        orphan_events = []
        for i in range(self.orphan_events_list.size()):
            orphan_events.append(self.orphan_events_list.get(i))
        orphan_events.sort()

        if not orphan_events:
            self.orphan_media_menu.add_command(label="(No orphan events available)", state=tk.DISABLED)
        else:
            self.orphan_media_menu.add_command(label="Assign to event:", state=tk.DISABLED)
            self.orphan_media_menu.add_separator()

            # Add menu item for each orphan event (sorted A-Z)
            for orphan_event in orphan_events:
                self.orphan_media_menu.add_command(
                    label=orphan_event,
                    command=lambda e=orphan_event: self._assign_media_to_event(e)
                )

        # Show menu at cursor position
        try:
            self.orphan_media_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.orphan_media_menu.grab_release()

    def _assign_media_to_event(self, event_name: str):
        """Assign selected orphan media files to an orphan event"""
        # Get selected media files
        selected_indices = list(self.orphan_media_list.curselection())
        if not selected_indices:
            return

        # Get the media filenames
        selected_media = []
        for idx in selected_indices:
            media_filename = self.orphan_media_list.get(idx)
            selected_media.append(media_filename)

        # Get bank and bus from current selection
        bank_name = self.bank_var.get()
        bus_name = self.bus_var.get()

        # Check if event already exists in preview tree
        event_item = None
        for item in self.preview_tree.get_children():
            if self.preview_tree.item(item, 'text') == event_name:
                event_item = item
                break

        # If event doesn't exist in tree, create it
        if event_item is None:
            event_item = self.preview_tree.insert('', 'end', text=event_name,
                                                   values=(bank_name, bus_name))

        # Add media files as children of the event
        for media_filename in selected_media:
            self.preview_tree.insert(event_item, 'end', text=f"  → {media_filename}",
                                     values=('', ''))

        # Remove from orphan media list (in reverse order to maintain indices)
        for idx in reversed(selected_indices):
            self.orphan_media_list.delete(idx)

        # Check if event should be removed from orphan events list
        # Remove it if it now has at least one media file assigned
        event_has_children = len(self.preview_tree.get_children(event_item)) > 0
        if event_has_children:
            # Remove event from orphan events list
            for i in range(self.orphan_events_list.size()):
                if self.orphan_events_list.get(i) == event_name:
                    self.orphan_events_list.delete(i)
                    break

    def _set_drop_target(self, target):
        """Set the current drop target"""
        if self._drag_data['dragging']:
            self._drag_data['drop_target'] = target

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for Listbox widgets"""
        # Get the widget that triggered the event
        widget = event.widget

        # Determine scroll direction and amount
        if event.num == 5 or event.delta < 0:
            # Scroll down
            widget.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            # Scroll up
            widget.yview_scroll(-1, "units")

        return "break"

    def _on_listbox_up(self, event):
        """Handle Up arrow key navigation"""
        current = self.orphan_media_list.curselection()
        if not current:
            # Select first item
            if self.orphan_media_list.size() > 0:
                self.orphan_media_list.selection_set(0)
                self.orphan_media_list.see(0)
        else:
            current_idx = current[0]
            if current_idx > 0:
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(current_idx - 1)
                self.orphan_media_list.see(current_idx - 1)
        return "break"

    def _on_listbox_down(self, event):
        """Handle Down arrow key navigation"""
        current = self.orphan_media_list.curselection()
        size = self.orphan_media_list.size()
        if not current:
            # Select first item
            if size > 0:
                self.orphan_media_list.selection_set(0)
                self.orphan_media_list.see(0)
        else:
            current_idx = current[0]
            if current_idx < size - 1:
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(current_idx + 1)
                self.orphan_media_list.see(current_idx + 1)
        return "break"

    def _on_listbox_select_all(self, event):
        """Handle Ctrl+A to select all"""
        self.orphan_media_list.selection_set(0, tk.END)
        return "break"

    def _on_listbox_press(self, event):
        """Handle initial press on listbox - store position and selection"""
        # Store initial position
        self._drag_data['start_x'] = event.x
        self._drag_data['start_y'] = event.y
        self._drag_data['dragging'] = False
        self._drag_data['click_index'] = None

        # Get the index under cursor
        index = self.orphan_media_list.nearest(event.y)

        # Handle selection manually to prevent drag-select behavior
        # Check if item is already selected
        if index in self.orphan_media_list.curselection():
            # Already selected
            # Check for modifiers
            if event.state & 0x4:  # Ctrl key - deselect immediately
                self.orphan_media_list.selection_clear(index)
            elif event.state & 0x1:  # Shift key - do nothing, wait for release
                pass
            else:
                # Normal click - store index to potentially deselect others on release
                # This allows drag of multiple items but also single-click to deselect others
                self._drag_data['click_index'] = index
            return "break"
        else:
            # Not selected, select it
            # Check for Ctrl or Shift modifiers
            if event.state & 0x4:  # Ctrl key
                # Toggle selection (add to selection)
                self.orphan_media_list.selection_set(index)
            elif event.state & 0x1:  # Shift key
                # Range selection from last selected to current
                current = self.orphan_media_list.curselection()
                if current:
                    start = current[0]
                    end = index
                    if start > end:
                        start, end = end, start
                    self.orphan_media_list.selection_clear(0, tk.END)
                    for i in range(start, end + 1):
                        self.orphan_media_list.selection_set(i)
                else:
                    self.orphan_media_list.selection_set(index)
            else:
                # Normal click - clear and select
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(index)

            return "break"

    def _on_drag_motion(self, event):
        """Handle drag motion - start drag if moved beyond threshold"""
        if self._drag_data['dragging']:
            # Already dragging, update label position
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Update drop target highlight
            self._update_drop_target_highlight(event.x_root, event.y_root)

            return "break"

        # Check if moved beyond threshold
        dx = abs(event.x - self._drag_data['start_x'])
        dy = abs(event.y - self._drag_data['start_y'])

        if dx > self._drag_threshold or dy > self._drag_threshold:
            # Start dragging
            selected_indices = self.orphan_media_list.curselection()
            if not selected_indices:
                return "break"

            # Store selected media files
            self._drag_data['items'] = [self.orphan_media_list.get(idx) for idx in selected_indices]
            self._drag_data['indices'] = list(selected_indices)
            self._drag_data['dragging'] = True
            self._drag_data['source_widget'] = 'orphan_media'

            # Show drag feedback label
            count = len(self._drag_data['items'])
            if count == 1:
                label_text = f"📁 {self._drag_data['items'][0]}"
            else:
                label_text = f"📁 {count} files"
            self._drag_label.config(text=label_text)

            # Position label near cursor (convert screen coords to root widget coords)
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Change cursor to indicate dragging
            self.orphan_media_list.config(cursor='hand2')

            # Highlight selected items with a different background
            for idx in selected_indices:
                self.orphan_media_list.itemconfig(idx, bg='lightblue')

        # Prevent default drag-select behavior
        return "break"

    def _on_preview_tree_press(self, event):
        """Handle initial press on preview tree"""
        # Store initial position
        self._drag_data['start_x'] = event.x
        self._drag_data['start_y'] = event.y
        self._drag_data['dragging'] = False

        # Let default selection happen
        return

    def _on_preview_tree_drag(self, event):
        """Handle drag from preview tree - only media files can be dragged"""
        if self._drag_data['dragging']:
            # Already dragging, update label position
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Update drop target highlight
            self._update_drop_target_highlight(event.x_root, event.y_root)
            return

        # Check if moved beyond threshold
        dx = abs(event.x - self._drag_data['start_x'])
        dy = abs(event.y - self._drag_data['start_y'])

        if dx > self._drag_threshold or dy > self._drag_threshold:
            # Get selected item
            selected = self.preview_tree.selection()
            if not selected:
                return

            # Only allow dragging media files (child items starting with "  → ")
            media_items = []
            media_files = []
            for item in selected:
                text = self.preview_tree.item(item, 'text')
                if text.startswith('  → '):
                    media_items.append(item)
                    # Extract filename (remove "  → " prefix)
                    filename = text[4:]
                    media_files.append(filename)

            if not media_files:
                # No media files selected, don't start drag
                return

            # Store media files for dragging
            self._drag_data['items'] = media_files
            self._drag_data['tree_items'] = media_items  # Store tree items for deletion
            self._drag_data['dragging'] = True
            self._drag_data['source_widget'] = 'preview_tree'

            # Show drag feedback label
            count = len(media_files)
            if count == 1:
                label_text = f"📁 {media_files[0]}"
            else:
                label_text = f"📁 {count} files"
            self._drag_label.config(text=label_text)

            # Position label near cursor (convert screen coords to root widget coords)
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Change cursor
            self.preview_tree.config(cursor='hand2')

    def _on_preview_tree_release(self, event):
        """Handle release from preview tree drag"""
        if not self._drag_data['dragging'] or self._drag_data['source_widget'] != 'preview_tree':
            return

        # Restore cursor
        self.preview_tree.config(cursor='')

        # Check if dropped over orphan media list
        x_root = event.x_root
        y_root = event.y_root

        try:
            media_x = self.orphan_media_list.winfo_rootx()
            media_y = self.orphan_media_list.winfo_rooty()
            media_width = self.orphan_media_list.winfo_width()
            media_height = self.orphan_media_list.winfo_height()

            if (media_x <= x_root <= media_x + media_width and
                media_y <= y_root <= media_y + media_height):
                # Valid drop - move media files back to orphan list
                self._drop_preview_to_orphan()
                return
        except:
            pass

        # Not a valid drop, cancel
        self._clear_drag_data()

    def _drop_preview_to_orphan(self):
        """Move media files from preview tree back to orphan media list"""
        if not self._drag_data['items']:
            return

        # Add files to orphan media list
        for filename in self._drag_data['items']:
            self.orphan_media_list.insert(tk.END, filename)

        # Sort the orphan media list
        items = list(self.orphan_media_list.get(0, tk.END))
        items.sort()
        self.orphan_media_list.delete(0, tk.END)
        for item in items:
            self.orphan_media_list.insert(tk.END, item)

        # Remove from preview tree
        for tree_item in self._drag_data.get('tree_items', []):
            # Get parent event
            parent = self.preview_tree.parent(tree_item)
            # Delete the media item
            self.preview_tree.delete(tree_item)

            # Check if parent event now has no media files
            if parent:
                event_name = self.preview_tree.item(parent, 'text')
                children = self.preview_tree.get_children(parent)
                if len(children) == 0:
                    # Event has no media, remove from preview tree
                    self.preview_tree.delete(parent)

                    # Add back to orphan events
                    orphan_events = list(self.orphan_events_list.get(0, tk.END))
                    if event_name not in orphan_events:
                        orphan_events.append(event_name)
                        orphan_events.sort()
                        self.orphan_events_list.delete(0, tk.END)
                        for event in orphan_events:
                            self.orphan_events_list.insert(tk.END, event)

        self._clear_drag_data()

    def _on_preview_tree_delete(self, event):
        """Handle Delete key press on preview tree - remove media files and move to orphan list"""
        selected = self.preview_tree.selection()
        if not selected:
            return

        # Filter to only media files (child items starting with "  → ")
        media_items = []
        media_files = []
        for item in selected:
            text = self.preview_tree.item(item, 'text')
            if text.startswith('  → '):
                media_items.append(item)
                # Extract filename (remove "  → " prefix)
                filename = text[4:]
                media_files.append(filename)

        if not media_files:
            # No media files selected, nothing to delete
            return

        # Add files back to orphan media list
        for filename in media_files:
            self.orphan_media_list.insert(tk.END, filename)

        # Sort the orphan media list
        items = list(self.orphan_media_list.get(0, tk.END))
        items.sort()
        self.orphan_media_list.delete(0, tk.END)
        for item in items:
            self.orphan_media_list.insert(tk.END, item)

        # Track parent events that might become orphans
        parent_events = set()

        # Remove from preview tree
        for tree_item in media_items:
            # Get parent event before deleting
            parent = self.preview_tree.parent(tree_item)
            if parent:
                parent_events.add(parent)
            # Delete the media item
            self.preview_tree.delete(tree_item)

        # Check if any parent events now have no media files
        for parent in parent_events:
            event_name = self.preview_tree.item(parent, 'text')
            children = self.preview_tree.get_children(parent)
            if len(children) == 0:
                # Event has no media, remove from preview tree
                self.preview_tree.delete(parent)

                # Add back to orphan events
                orphan_events = list(self.orphan_events_list.get(0, tk.END))
                if event_name not in orphan_events:
                    orphan_events.append(event_name)
                    orphan_events.sort()
                    self.orphan_events_list.delete(0, tk.END)
                    for event in orphan_events:
                        self.orphan_events_list.insert(tk.END, event)

        return "break"  # Prevent default behavior

    def _on_listbox_release(self, event):
        """Handle release - perform drop if dragging, otherwise allow normal selection"""
        if not self._drag_data['dragging']:
            # Not dragging - check if it was a simple click on already selected item
            if self._drag_data.get('click_index') is not None:
                # Simple click on selected item - deselect others and keep only this one
                index = self._drag_data['click_index']
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(index)
                self._drag_data['click_index'] = None
            return

        # Restore cursor
        self.orphan_media_list.config(cursor='')

        # Determine drop location based on cursor position
        # Convert event coordinates to screen coordinates
        x_root = event.x_root
        y_root = event.y_root

        # Check if over preview tree
        try:
            preview_x = self.preview_tree.winfo_rootx()
            preview_y = self.preview_tree.winfo_rooty()
            preview_width = self.preview_tree.winfo_width()
            preview_height = self.preview_tree.winfo_height()

            if (preview_x <= x_root <= preview_x + preview_width and
                preview_y <= y_root <= preview_y + preview_height):
                # Drop on preview tree
                # Convert to widget-relative coordinates
                widget_y = y_root - preview_y
                self._drop_on_preview(widget_y)
                return
        except:
            pass

        # Check if over orphan events list
        try:
            orphan_x = self.orphan_events_list.winfo_rootx()
            orphan_y = self.orphan_events_list.winfo_rooty()
            orphan_width = self.orphan_events_list.winfo_width()
            orphan_height = self.orphan_events_list.winfo_height()

            if (orphan_x <= x_root <= orphan_x + orphan_width and
                orphan_y <= y_root <= orphan_y + orphan_height):
                # Drop on orphan events
                widget_y = y_root - orphan_y
                self._drop_on_orphan_event(widget_y)
                return
        except:
            pass

        # Not over a valid drop target, cancel drag
        self._clear_drag_data()

    def _drop_on_preview(self, widget_y):
        """Drop orphan media onto preview tree event"""
        if not self._drag_data['items']:
            return

        # Identify the item under the cursor
        item = self.preview_tree.identify_row(widget_y)
        if not item:
            self._clear_drag_data()
            return

        # Get the top-level parent (event item)
        parent = self.preview_tree.parent(item)
        event_item = item if not parent else parent

        # Get event name
        event_name = self.preview_tree.item(event_item, 'text')

        # Add media files to this event
        for media_filename in self._drag_data['items']:
            self.preview_tree.insert(event_item, 'end', text=f"  → {media_filename}",
                                     values=('', ''))

        # Remove from orphan media list
        for idx in reversed(self._drag_data['indices']):
            self.orphan_media_list.delete(idx)

        # Check if event should be removed from orphan events list
        event_has_children = len(self.preview_tree.get_children(event_item)) > 0
        if event_has_children:
            for i in range(self.orphan_events_list.size()):
                if self.orphan_events_list.get(i) == event_name:
                    self.orphan_events_list.delete(i)
                    break

        self._clear_drag_data()

    def _drop_on_orphan_event(self, widget_y):
        """Drop orphan media onto orphan event"""
        if not self._drag_data['items']:
            return

        # Get the event under cursor
        index = self.orphan_events_list.nearest(widget_y)
        if index < 0:
            self._clear_drag_data()
            return

        event_name = self.orphan_events_list.get(index)

        # Get bank and bus from current selection
        bank_name = self.bank_var.get()
        bus_name = self.bus_var.get()

        # Check if event already exists in preview tree
        event_item = None
        for item in self.preview_tree.get_children():
            if self.preview_tree.item(item, 'text') == event_name:
                event_item = item
                break

        # If event doesn't exist in tree, create it
        if event_item is None:
            event_item = self.preview_tree.insert('', 'end', text=event_name,
                                                   values=(bank_name, bus_name))

        # Add media files to this event
        for media_filename in self._drag_data['items']:
            self.preview_tree.insert(event_item, 'end', text=f"  → {media_filename}",
                                     values=('', ''))

        # Remove from orphan media list
        for idx in reversed(self._drag_data['indices']):
            self.orphan_media_list.delete(idx)

        # Check if event should be removed from orphan events list
        event_has_children = len(self.preview_tree.get_children(event_item)) > 0
        if event_has_children:
            for i in range(self.orphan_events_list.size()):
                if self.orphan_events_list.get(i) == event_name:
                    self.orphan_events_list.delete(i)
                    break

        self._clear_drag_data()

    def _update_drop_target_highlight(self, x_root, y_root):
        """Highlight valid drop targets when hovering during drag"""
        # Clear previous highlights
        self._clear_drop_highlights()

        source = self._drag_data.get('source_widget')

        # If dragging from orphan_media, highlight preview tree and orphan events
        if source == 'orphan_media':
            # Check if over preview tree
            try:
                preview_x = self.preview_tree.winfo_rootx()
                preview_y = self.preview_tree.winfo_rooty()
                preview_width = self.preview_tree.winfo_width()
                preview_height = self.preview_tree.winfo_height()

                if (preview_x <= x_root <= preview_x + preview_width and
                    preview_y <= y_root <= preview_y + preview_height):
                    # Highlight the preview tree
                    widget_y = y_root - preview_y
                    item = self.preview_tree.identify_row(widget_y)
                    if item:
                        # Get the top-level parent (event item)
                        parent = self.preview_tree.parent(item)
                        event_item = item if not parent else parent
                        # Highlight this event
                        self.preview_tree.selection_set(event_item)
                        self._drag_highlight_items.append(('preview_tree', event_item))
                    return
            except:
                pass

            # Check if over orphan events list
            try:
                orphan_x = self.orphan_events_list.winfo_rootx()
                orphan_y = self.orphan_events_list.winfo_rooty()
                orphan_width = self.orphan_events_list.winfo_width()
                orphan_height = self.orphan_events_list.winfo_height()

                if (orphan_x <= x_root <= orphan_x + orphan_width and
                    orphan_y <= y_root <= orphan_y + orphan_height):
                    # Highlight the orphan events list
                    widget_y = y_root - orphan_y
                    index = self.orphan_events_list.nearest(widget_y)
                    if index >= 0 and index < self.orphan_events_list.size():
                        self.orphan_events_list.selection_clear(0, tk.END)
                        self.orphan_events_list.selection_set(index)
                        self._drag_highlight_items.append(('orphan_events', index))
                    return
            except:
                pass

        # If dragging from preview_tree, highlight orphan media list
        elif source == 'preview_tree':
            try:
                media_x = self.orphan_media_list.winfo_rootx()
                media_y = self.orphan_media_list.winfo_rooty()
                media_width = self.orphan_media_list.winfo_width()
                media_height = self.orphan_media_list.winfo_height()

                if (media_x <= x_root <= media_x + media_width and
                    media_y <= y_root <= media_y + media_height):
                    # Highlight the entire orphan media list
                    self.orphan_media_list.config(bg='lightyellow')
                    self._drag_highlight_items.append(('orphan_media_list', None))
                    return
            except:
                pass

    def _clear_drop_highlights(self):
        """Clear all drop target highlights"""
        for widget_type, item in self._drag_highlight_items:
            if widget_type == 'preview_tree':
                self.preview_tree.selection_remove(item)
            elif widget_type == 'orphan_events':
                self.orphan_events_list.selection_clear(item)
            elif widget_type == 'orphan_media_list':
                self.orphan_media_list.config(bg='white')
        self._drag_highlight_items = []

    def _clear_drag_data(self):
        """Clear drag data after drop or cancel"""
        # Hide drag label
        self._drag_label.place_forget()

        # Restore cursors based on source
        source = self._drag_data.get('source_widget')
        if source == 'orphan_media':
            self.orphan_media_list.config(cursor='')
        elif source == 'preview_tree':
            self.preview_tree.config(cursor='')

        # Clear item highlights
        for idx in self._drag_data.get('indices', []):
            try:
                self.orphan_media_list.itemconfig(idx, bg='white')
            except:
                pass  # Item may have been deleted

        # Clear drop target highlights
        self._clear_drop_highlights()

        # Reset drag data
        self._drag_data['items'] = []
        self._drag_data['indices'] = []
        self._drag_data['dragging'] = False
        self._drag_data['drop_target'] = None
        self._drag_data['source_widget'] = None

    def import_assets(self):
        """Import assets using FMOD JavaScript API via auto-execute script"""
        try:
            # 1. Validate inputs
            if not self.project:
                messagebox.showerror("Error", "No FMOD Studio project is loaded.")
                return
    
            asset_id = getattr(self, "selected_asset_id", None)
            if not asset_id:
                messagebox.showerror("Error", "Please select an audio asset folder.")
                return
    
            asset_info = self.project.asset_folders.get(asset_id)
            if not asset_info:
                messagebox.showerror("Error", "Selected audio asset folder could not be found.")
                return
    
            asset_folder = asset_info["path"] or ""
            if asset_folder and not asset_folder.endswith(("/", "\\\\")):
                asset_folder += "/"
    
            media_path_input = self.media_entry.get()
            media_root = Path(media_path_input) if media_path_input else None
    
            # 2. Get event-audio mapping from preview tree
            event_audio_map = {}
            for item in self.preview_tree.get_children():
                event_name = self.preview_tree.item(item, "text")
                audio_files = []
                for child in self.preview_tree.get_children(item):
                    audio_label = self.preview_tree.item(child, "text") or ""
                    if "→" in audio_label:
                        audio_label = audio_label.split("→", 1)[1]
                    audio_label = audio_label.strip()
    
                    values = self.preview_tree.item(child, "values") or []
                    audio_path = values[0] if len(values) > 0 and values[0] else None
    
                    if not audio_path:
                        if media_root:
                            audio_path = str((media_root / audio_label).resolve())
                        else:
                            audio_path = audio_label
    
                    audio_path = os.path.normpath(audio_path)
                    audio_files.append((audio_label, audio_path))
    
                if audio_files:
                    event_audio_map[event_name] = audio_files
    
            if not event_audio_map:
                messagebox.showerror("Error", "No events in the preview tree to import.")
                return
    
            # 3. Validate other fields
            media_path = media_path_input
            if not media_path or not os.path.exists(media_path):
                messagebox.showerror("Error", "Please specify a valid media path.")
                return
    
            prefix = self._get_entry_value(self.prefix_entry, "e.g. Cat")
            character = self._get_entry_value(self.character_entry, "e.g. Infiltrator")
            if not prefix or not character:
                messagebox.showerror("Error", "Please specify prefix and character name.")
                return
    
            template_folder_id = getattr(self, "selected_template_id", None)
            dest_folder_id = getattr(self, "selected_dest_id", None)
            bank_id = getattr(self, "selected_bank_id", None)
            bus_id = getattr(self, "selected_bus_id", None)
    
            if not all([template_folder_id, dest_folder_id, bank_id, bus_id]):
                messagebox.showerror("Error", "Please select template folder, destination folder, bank, and bus.")
                return
    
            # 4. Load templates
            template_events = self.project.get_events_in_folder(template_folder_id)
            if not template_events:
                messagebox.showerror("Error", "No template events found.")
                return
    
            template_map = {}
            for tmpl in template_events:
                parts = tmpl["name"].split("_", 2)
                if len(parts) >= 3:
                    expected_name = f"{prefix}_{character}_{parts[2]}"
                    template_map[expected_name] = tmpl
    
            # 5. Build import data
            import_events = []
            template_folder_path = self._get_folder_path(template_folder_id)
            dest_folder_path = self._get_folder_path(dest_folder_id)
            bank_name = self.project.banks[bank_id]["name"]
            bus_name = self.project.buses[bus_id]["name"]
    
            for event_name, audio_entries in event_audio_map.items():
                template_event = template_map.get(event_name)
                if not template_event:
                    continue
    
                audio_paths = []
                for label, path_str in audio_entries:
                    resolved_path = Path(path_str)
                    if not resolved_path.is_absolute():
                        resolved_path = Path(media_path) / resolved_path
                    if not resolved_path.exists():
                        continue
                    audio_paths.append(resolved_path.resolve().as_posix())
    
                if not audio_paths:
                    continue
    
                import_events.append({
                    "templateEventPath": f"{template_folder_path}/{template_event['name']}",
                    "newEventName": event_name,
                    "destFolderPath": dest_folder_path,
                    "audioFilePaths": audio_paths,
                    "assetFolderPath": asset_folder,
                    "bankName": bank_name,
                    "busName": bus_name,
                    "isMulti": len(audio_paths) > 1,
                })
    
            if not import_events:
                messagebox.showerror("Error", "No events ready for import.")
                return

            # 6. Copy audio files to FMOD Assets folder
            import shutil
            project_dir = self.project.project_path.parent
            assets_dir = project_dir / "Assets"

            for event in import_events:
                # Create destination folder
                dest_folder = assets_dir / event["assetFolderPath"]
                dest_folder.mkdir(parents=True, exist_ok=True)

                # Copy each audio file and update paths
                copied_paths = []
                for source_path in event["audioFilePaths"]:
                    source = Path(source_path)
                    dest = dest_folder / source.name

                    # Copy file (overwrites automatically if exists)
                    shutil.copy2(source, dest)
                    copied_paths.append(str(dest.as_posix()))

                # Update paths to point to copied files
                event["audioFilePaths"] = copied_paths

            # 7. Create JSON and auto-exec script
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            json_path = temp_dir / f"moco_import_data_{uuid.uuid4().hex}.json"
            result_path = temp_dir / f"moco_import_result_{uuid.uuid4().hex}.json"
    
            import_payload = {
                "projectPath": str(self.project.project_path),
                "resultPath": str(result_path),
                "bankName": bank_name,
                "busName": bus_name,
                "defaultDestFolderPath": dest_folder_path,
                "events": import_events,
            }

            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump(import_payload, fh, indent=2)

            # Write debug log for Python side
            debug_log_path = temp_dir / f"moco_import_python_debug_{uuid.uuid4().hex}.txt"
            with open(debug_log_path, "w", encoding="utf-8") as fh:
                fh.write("=" * 80 + "\n")
                fh.write("PYTHON IMPORT GENERATION DEBUG\n")
                fh.write("=" * 80 + "\n\n")
                fh.write(f"Timestamp: {uuid.uuid4()}\n")
                fh.write(f"Project: {self.project.project_path}\n")
                fh.write(f"JSON Path: {json_path}\n")
                fh.write(f"Result Path: {result_path}\n\n")

                fh.write(f"[USER SELECTIONS]\n")
                fh.write(f"  Prefix: {prefix}\n")
                fh.write(f"  Character: {character}\n")
                fh.write(f"  Media Path: {media_path}\n")
                fh.write(f"  Asset Folder ID: {asset_id}\n")
                fh.write(f"  Asset Folder Path: {asset_folder}\n")
                fh.write(f"  Template Folder ID: {template_folder_id}\n")
                fh.write(f"  Template Folder Path: {template_folder_path}\n")
                fh.write(f"  Dest Folder ID: {dest_folder_id}\n")
                fh.write(f"  Dest Folder Path: {dest_folder_path}\n")
                fh.write(f"  Bank ID: {bank_id}\n")
                fh.write(f"  Bank Name: {bank_name}\n")
                fh.write(f"  Bus ID: {bus_id}\n")
                fh.write(f"  Bus Name: {bus_name}\n\n")

                fh.write(f"[EVENTS TO IMPORT] ({len(import_events)} total)\n")
                for event in import_events:
                    fh.write(f"\n  Event: {event['newEventName']}\n")
                    fh.write(f"    Template: {event['templateEventPath']}\n")
                    fh.write(f"    Dest Folder: {event['destFolderPath']}\n")
                    fh.write(f"    Asset Folder: {event['assetFolderPath']}\n")
                    fh.write(f"    Bank: {event['bankName']}\n")
                    fh.write(f"    Bus: {event['busName']}\n")
                    fh.write(f"    Is Multi: {event['isMulti']}\n")
                    fh.write(f"    Audio Files: {len(event['audioFilePaths'])}\n")
                    for i, path in enumerate(event['audioFilePaths'], 1):
                        fh.write(f"      {i}. {path}\n")

                fh.write(f"\n[JSON PAYLOAD]\n")
                fh.write(json.dumps(import_payload, indent=2))
    
            # 7. Execute import directly via FMOD Studio command line
            num_events = len(import_events)

            # Find FMOD Studio executable
            fmod_exe = self._find_fmod_studio_exe()
            if not fmod_exe:
                msg = (f"Import JSON created for {num_events} event(s).\\n\\n"
                       "Could not find FMOD Studio executable.\\n"
                       "Please set it in Settings or import manually:\\n"
                       "  Scripts > Moco: Import JSON")
                messagebox.showwarning("Manual Import Required", msg)
                return

            # Execute the import script via FMOD Studio console
            script_path = Path(__file__).resolve().parent / "Script" / "_Internal" / "MocoImportFromJson.js"

            try:
                # Create a temporary wrapper script that includes the JSON path
                # This is needed because fmodstudiocl.exe doesn't pass arguments to scripts
                wrapper_script_path = json_path.parent / "_temp_import_wrapper.js"

                wrapper_script_content = f"""
// Temporary wrapper script - auto-generated
// Sets the JSON path as a global variable and runs the import script

// Set JSON path as global variable
var MOCO_JSON_PATH = "{str(json_path).replace(chr(92), '/')}";

// Load and execute the main import script
var importScriptPath = "{str(script_path).replace(chr(92), '/')}";

function readTextFile(path) {{
    var file = studio.system.getFile(path);
    file.open(studio.system.openMode.ReadOnly);
    var size = file.size();
    var text = file.readText(size);
    file.close();
    return text;
}}

var importScriptContent = readTextFile(importScriptPath);

// Execute the import script (it will use MOCO_JSON_PATH global variable)
eval(importScriptContent);
"""

                with open(wrapper_script_path, 'w', encoding='utf-8') as f:
                    f.write(wrapper_script_content)

                # Build command: fmodstudiocl.exe -script wrapper.js project.fspro
                cmd = [
                    str(fmod_exe),
                    "-script",
                    str(wrapper_script_path),
                    str(self.project.project_path)
                ]

                # Show progress message
                progress_msg = f"Importing {num_events} event(s) to FMOD Studio...\n\nThis may take a moment."
                print(f"Executing command: {' '.join(cmd)}")
                messagebox.showinfo("Import Started", progress_msg)

                # Execute the command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                # Clean up wrapper script
                try:
                    if wrapper_script_path.exists():
                        wrapper_script_path.unlink()
                except:
                    pass

                # Print output for debugging
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                print("Return code:", result.returncode)

                # Check result file
                if result_path.exists():
                    with open(result_path, 'r', encoding='utf-8') as f:
                        import_result = json.load(f)

                    success_msg = (f"Import Complete!\\n\\n"
                                 f"Imported: {import_result.get('imported', 0)}\\n"
                                 f"Failed: {import_result.get('failed', 0)}")

                    if import_result.get('messages'):
                        success_msg += "\\n\\nMessages:\\n" + "\\n".join(import_result['messages'][:5])

                    messagebox.showinfo("Import Complete", success_msg)
                else:
                    messagebox.showwarning("Import Status Unknown",
                                         "Import executed but result file not found.\\n"
                                         "Check FMOD Studio console for details.")

            except subprocess.TimeoutExpired:
                messagebox.showerror("Import Timeout",
                                   "Import operation timed out after 5 minutes.\\n"
                                   "The project may be too large.")
            except Exception as e:
                messagebox.showerror("Import Failed",
                                   f"Failed to execute import:\\n{str(e)}\\n\\n"
                                   "You can try manual import:\\n"
                                   "Scripts > Moco: Import JSON")
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to prepare import: {str(e)}")
            import traceback
            traceback.print_exc()
    def _get_folder_path(self, folder_id):
        """Get full path of an event folder (excluding master folder)"""
        parts = []
        current_id = folder_id
        master_folder_id = self.project.workspace['masterEventFolder']

        while current_id and current_id in self.project.event_folders:
            # Don't include the master folder itself
            if current_id == master_folder_id:
                break

            folder = self.project.event_folders[current_id]
            parts.insert(0, folder['name'])
            current_id = folder.get('parent')

        return '/'.join(parts)


    def _load_default_settings(self):
        """Load default settings and populate UI fields at startup"""
        settings = self.load_settings()

        if settings.get('default_project_path'):
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, settings['default_project_path'])
            # Auto-load project if path exists
            if os.path.exists(settings['default_project_path']):
                self.load_project()

        if settings.get('default_media_path'):
            self.media_entry.delete(0, tk.END)
            self.media_entry.insert(0, settings['default_media_path'])

        # Apply default template folder if project is loaded
        if settings.get('default_template_folder_id') and self.project:
            template_id = settings['default_template_folder_id']
            if template_id in self.project.event_folders:
                self.template_var.set(self.project.event_folders[template_id]['name'])
                self.selected_template_id = template_id

        # Apply default bank if project is loaded
        if settings.get('default_bank_id') and self.project:
            bank_id = settings['default_bank_id']
            if bank_id in self.project.banks:
                self.bank_var.set(self.project.banks[bank_id]['name'])
                self.selected_bank_id = bank_id

        # Apply default destination folder if project is loaded
        if settings.get('default_destination_folder_id') and self.project:
            dest_id = settings['default_destination_folder_id']
            if dest_id in self.project.event_folders:
                self.dest_var.set(self.project.event_folders[dest_id]['name'])
                self.selected_dest_id = dest_id

        # Apply default bus if project is loaded
        if settings.get('default_bus_id') and self.project:
            bus_id = settings['default_bus_id']
            if bus_id in self.project.buses:
                self.bus_var.set(self.project.buses[bus_id]['name'])
                self.selected_bus_id = bus_id

    def load_settings(self):
        """Load settings from JSON file"""
        settings_file = Path.home() / ".moco_auto_import_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings
            except Exception as e:
                print(f"Failed to load settings: {e}")
        return {
            'default_project_path': '',
            'default_media_path': '',
            'default_template_folder_id': '',
            'default_bank_id': '',
            'default_destination_folder_id': '',
            'default_bus_id': '',
            'fmod_exe_path': ''
        }

    def save_settings(self, settings: dict):
        """Save settings to JSON file"""
        settings_file = Path.home() / ".moco_auto_import_settings.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{str(e)}")
            return False

    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x450")
        settings_window.transient(self.root)
        settings_window.grab_set()
        self._center_dialog(settings_window)

        frame = ttk.Frame(settings_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Load current settings
        current_settings = self.load_settings()

        # Default project path
        ttk.Label(frame, text="Default FMOD Project:").grid(row=0, column=0, sticky=tk.W, pady=5)
        project_entry = ttk.Entry(frame, width=50)
        project_entry.insert(0, current_settings.get('default_project_path', ''))
        project_entry.grid(row=0, column=1, pady=5, padx=5)

        def browse_default_project():
            filename = filedialog.askopenfilename(
                title="Select Default FMOD Project",
                filetypes=[("FMOD Project", "*.fspro"), ("All Files", "*.*")]
            )
            if filename:
                project_entry.delete(0, tk.END)
                project_entry.insert(0, filename)

        ttk.Button(frame, text="Browse...", command=browse_default_project).grid(row=0, column=2, padx=5)

        # FMOD executable path
        ttk.Label(frame, text="FMOD Studio Executable:").grid(row=1, column=0, sticky=tk.W, pady=5)
        fmod_entry = ttk.Entry(frame, width=50)
        fmod_entry.insert(0, current_settings.get('fmod_exe_path', ''))
        fmod_entry.grid(row=1, column=1, pady=5, padx=5)

        def browse_fmod_exe():
            filename = filedialog.askopenfilename(
                title="Select FMOD Studio Executable",
                filetypes=[("FMOD Studio", "FMOD Studio*.exe"), ("All Files", "*.*")]
            )
            if filename:
                fmod_entry.delete(0, tk.END)
                fmod_entry.insert(0, filename)

        ttk.Button(frame, text="Browse...", command=browse_fmod_exe).grid(row=1, column=2, padx=5)

        # Default media path
        ttk.Label(frame, text="Default Media Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        media_entry = ttk.Entry(frame, width=50)
        media_entry.insert(0, current_settings.get('default_media_path', ''))
        media_entry.grid(row=2, column=1, pady=5, padx=5)

        def browse_default_media():
            dirname = filedialog.askdirectory(title="Select Default Media Directory")
            if dirname:
                media_entry.delete(0, tk.END)
                media_entry.insert(0, dirname)

        ttk.Button(frame, text="Browse...", command=browse_default_media).grid(row=2, column=2, padx=5)

        # Default template folder
        ttk.Label(frame, text="Default Template Folder:").grid(row=3, column=0, sticky=tk.W, pady=5)

        template_folder_var = tk.StringVar()
        template_folder_id_var = tk.StringVar()

        # Try to get folder name from ID if project is loaded
        saved_template_id = current_settings.get('default_template_folder_id', '')
        if saved_template_id and self.project and saved_template_id in self.project.event_folders:
            template_folder_var.set(self.project.event_folders[saved_template_id]['name'])
            template_folder_id_var.set(saved_template_id)
        else:
            template_folder_var.set("(No folder selected)")

        template_label = ttk.Label(frame, textvariable=template_folder_var, relief="sunken", width=45)
        template_label.grid(row=3, column=1, pady=5, padx=5)

        def browse_template_folder():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_folder_tree_dialog("Select Default Template Folder")
            if selected:
                folder_name, folder_id = selected
                template_folder_var.set(folder_name)
                template_folder_id_var.set(folder_id)

        ttk.Button(frame, text="Select...", command=browse_template_folder).grid(row=3, column=2, padx=5)

        # Default bank
        ttk.Label(frame, text="Default Bank:").grid(row=4, column=0, sticky=tk.W, pady=5)

        bank_var = tk.StringVar()
        bank_id_var = tk.StringVar()

        saved_bank_id = current_settings.get('default_bank_id', '')
        if saved_bank_id and self.project and saved_bank_id in self.project.banks:
            bank_var.set(self.project.banks[saved_bank_id]['name'])
            bank_id_var.set(saved_bank_id)
        else:
            bank_var.set("(No bank selected)")

        bank_label = ttk.Label(frame, textvariable=bank_var, relief="sunken", width=45)
        bank_label.grid(row=4, column=1, pady=5, padx=5)

        def browse_bank():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_hierarchical_dialog(
                "Select Default Bank",
                self.project.banks,
                create_fn=lambda name, parent_id: self.project.create_bank(name),
                delete_fn=lambda item_id: self.project.delete_bank(item_id)
            )
            if selected:
                selected_name, selected_id = selected
                bank_var.set(selected_name)
                bank_id_var.set(selected_id)

        ttk.Button(frame, text="Select...", command=browse_bank).grid(row=3, column=2, padx=5)

        # Default destination folder
        ttk.Label(frame, text="Default Destination Folder:").grid(row=5, column=0, sticky=tk.W, pady=5)

        dest_folder_var = tk.StringVar()
        dest_folder_id_var = tk.StringVar()

        saved_dest_id = current_settings.get('default_destination_folder_id', '')
        if saved_dest_id and self.project and saved_dest_id in self.project.event_folders:
            dest_folder_var.set(self.project.event_folders[saved_dest_id]['name'])
            dest_folder_id_var.set(saved_dest_id)
        else:
            dest_folder_var.set("(No folder selected)")

        dest_label = ttk.Label(frame, textvariable=dest_folder_var, relief="sunken", width=45)
        dest_label.grid(row=5, column=1, pady=5, padx=5)

        def browse_dest_folder():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_folder_tree_dialog("Select Default Destination Folder")
            if selected:
                folder_name, folder_id = selected
                dest_folder_var.set(folder_name)
                dest_folder_id_var.set(folder_id)

        ttk.Button(frame, text="Select...", command=browse_dest_folder).grid(row=5, column=2, padx=5)

        # Default bus
        ttk.Label(frame, text="Default Bus:").grid(row=6, column=0, sticky=tk.W, pady=5)

        bus_var = tk.StringVar()
        bus_id_var = tk.StringVar()

        saved_bus_id = current_settings.get('default_bus_id', '')
        if saved_bus_id and self.project and saved_bus_id in self.project.buses:
            bus_var.set(self.project.buses[saved_bus_id]['name'])
            bus_id_var.set(saved_bus_id)
        else:
            bus_var.set("(No bus selected)")

        bus_label = ttk.Label(frame, textvariable=bus_var, relief="sunken", width=45)
        bus_label.grid(row=6, column=1, pady=5, padx=5)

        def browse_bus():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_hierarchical_dialog(
                "Select Default Bus",
                self.project.buses,
                create_fn=lambda name, parent_id: self.project.create_bus(name),
                delete_fn=lambda item_id: self.project.delete_bus(item_id)
            )
            if selected:
                selected_name, selected_id = selected
                bus_var.set(selected_name)
                bus_id_var.set(selected_id)

        ttk.Button(frame, text="Select...", command=browse_bus).grid(row=6, column=2, padx=5)

        # Save button
        def save_and_close():
            new_settings = {
                'default_project_path': project_entry.get(),
                'default_media_path': media_entry.get(),
                'default_template_folder_id': template_folder_id_var.get(),
                'default_bank_id': bank_id_var.get(),
                'default_destination_folder_id': dest_folder_id_var.get(),
                'default_bus_id': bus_id_var.get(),
                'fmod_exe_path': fmod_entry.get()
            }
            if self.save_settings(new_settings):
                # Apply settings to current UI
                if new_settings['default_project_path']:
                    self.project_entry.delete(0, tk.END)
                    self.project_entry.insert(0, new_settings['default_project_path'])
                if new_settings['default_media_path']:
                    self.media_entry.delete(0, tk.END)
                    self.media_entry.insert(0, new_settings['default_media_path'])

                # Apply all defaults if project is loaded
                if self.project:
                    # Template folder
                    if new_settings['default_template_folder_id']:
                        template_id = new_settings['default_template_folder_id']
                        if template_id in self.project.event_folders:
                            self.template_var.set(self.project.event_folders[template_id]['name'])
                            self.selected_template_id = template_id

                    # Bank
                    if new_settings['default_bank_id']:
                        selected_bank_id = new_settings['default_bank_id']
                        if selected_bank_id in self.project.banks:
                            self.bank_var.set(self.project.banks[selected_bank_id]['name'])
                            self.selected_bank_id = selected_bank_id

                    # Destination folder
                    if new_settings['default_destination_folder_id']:
                        selected_dest_id = new_settings['default_destination_folder_id']
                        if selected_dest_id in self.project.event_folders:
                            self.dest_var.set(self.project.event_folders[selected_dest_id]['name'])
                            self.selected_dest_id = selected_dest_id

                    # Bus
                    if new_settings['default_bus_id']:
                        selected_bus_id = new_settings['default_bus_id']
                        if selected_bus_id in self.project.buses:
                            self.bus_var.set(self.project.buses[selected_bus_id]['name'])
                            self.selected_bus_id = selected_bus_id

                messagebox.showinfo("Success", "Settings saved successfully!")
                settings_window.destroy()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Save", command=save_and_close, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy, width=15).grid(row=0, column=1, padx=5)

        settings_window.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)


def main():
    root = tk.Tk()
    app = MocoAutoImportGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()










