"""Event creation and copying for FMOD project.

Handles complex event copying from templates with audio file assignment.
"""

import uuid
import shutil
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

from .xml_writer import write_pretty_xml
from .audio_file_manager import AudioFileManager


class EventCreator:
    """Static methods for event creation and copying operations."""

    @staticmethod
    def copy_from_template(template_event_id: str, new_name: str,
                          dest_folder_id: str, bank_id: str, bus_id: str,
                          audio_files: List[str], audio_asset_folder: str,
                          metadata_path: Path, project_path: Path, workspace: Dict) -> str:
        """
        Copy an event from template and assign audio files to it.

        This is a complex operation that:
        1. Deep copies the entire event XML structure
        2. Remaps all UUIDs to new ones
        3. Overrides folder, bank, and bus assignments
        4. Creates audio files and attaches them to the event
        5. Creates MultiSound and SingleSound objects
        6. Updates GroupTrack and Timeline references

        Args:
            template_event_id: ID of the template event to copy
            new_name: New name for the event
            dest_folder_id: Destination folder ID
            bank_id: Bank ID to assign
            bus_id: Bus ID to assign
            audio_files: List of audio file paths to assign
            audio_asset_folder: Folder where audio assets should be placed
            metadata_path: Path to the Metadata directory
            project_path: Path to the project file
            workspace: Workspace dictionary with master folder references

        Returns:
            New event ID

        Raises:
            ValueError: If template event not found
        """
        # Find template event
        template_event_path = metadata_path / "Event" / f"{template_event_id}.xml"
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
                assets_folder = project_path.parent / "Assets"
                dest_folder = assets_folder / Path(audio_asset_folder)
                dest_folder.mkdir(parents=True, exist_ok=True)

                dest_file = dest_folder / audio_file_src.name
                shutil.copy2(audio_file_src, dest_file)

                # Create AudioFile using the AudioFileManager
                # Pass the actual file path for reading properties, and the FMOD asset path
                audio_file_id = AudioFileManager.create(
                    str(audio_file_src), asset_relative_path,
                    metadata_path, workspace
                )

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
            except Exception:
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

        # Ensure Event directory exists
        event_dir = metadata_path / "Event"
        event_dir.mkdir(exist_ok=True)

        # Write new event file
        event_file = event_dir / f"{new_event_id}.xml"
        write_pretty_xml(new_root, event_file)

        return new_event_id
