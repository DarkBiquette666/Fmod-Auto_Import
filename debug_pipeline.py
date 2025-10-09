#!/usr/bin/env python3
"""
Pipeline Debug Tool - Captures complete state at each stage
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from moco_auto_import import FMODProject


def dump_fmod_project_state(project: FMODProject, label: str):
    """Dump complete FMOD project state"""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")

    print(f"\n[WORKSPACE]")
    print(f"  Master Event Folder: {project.workspace['masterEventFolder']}")
    print(f"  Master Bank Folder: {project.workspace['masterBankFolder']}")
    print(f"  Master Asset Folder: {project.workspace['masterAssetFolder']}")

    print(f"\n[EVENT FOLDERS] ({len(project.event_folders)} total)")
    for folder_id, folder_data in list(project.event_folders.items())[:5]:
        print(f"  {folder_data['name']}: {folder_id}")

    print(f"\n[BANKS] ({len(project.banks)} total)")
    for bank_id, bank_data in project.banks.items():
        print(f"  {bank_data['name']}: {bank_id}")

    print(f"\n[BUSES] ({len(project.buses)} total)")
    for bus_id, bus_data in project.buses.items():
        print(f"  {bus_data['name']}: {bus_id}")

    print(f"\n[ASSET FOLDERS] ({len(project.asset_folders)} total)")
    for asset_id, asset_data in list(project.asset_folders.items())[:5]:
        print(f"  {asset_data['path']}: {asset_id}")


def dump_json_payload(json_path: Path):
    """Dump generated JSON payload"""
    print(f"\n{'='*80}")
    print("JSON PAYLOAD GENERATED")
    print(f"{'='*80}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\nPath: {json_path}")
    print(f"Project: {data.get('projectPath')}")
    print(f"Bank: {data.get('bankName')}")
    print(f"Bus: {data.get('busName')}")
    print(f"Default Dest Folder: {data.get('defaultDestFolderPath')}")

    print(f"\n[EVENTS TO IMPORT] ({len(data.get('events', []))} total)")
    for event in data.get('events', []):
        print(f"\n  Event: {event['newEventName']}")
        print(f"    Template: {event.get('templateEventPath')}")
        print(f"    Dest Folder: {event.get('destFolderPath')}")
        print(f"    Asset Folder: {event.get('assetFolderPath', 'NONE')}")
        print(f"    Bank: {event.get('bankName')}")
        print(f"    Bus: {event.get('busName')}")
        print(f"    Is Multi: {event.get('isMulti')}")
        print(f"    Audio files ({len(event.get('audioFilePaths', []))}):")
        for i, audio_path in enumerate(event.get('audioFilePaths', [])[:3], 1):
            print(f"      {i}. {audio_path}")
        if len(event.get('audioFilePaths', [])) > 3:
            print(f"      ... and {len(event.get('audioFilePaths', [])) - 3} more")


def dump_fmod_post_import(project_path: Path, event_names: list):
    """Dump FMOD project state after import"""
    print(f"\n{'='*80}")
    print("FMOD POST-IMPORT STATE")
    print(f"{'='*80}")

    metadata_path = project_path.parent / "Metadata"
    event_dir = metadata_path / "Event"
    audio_dir = metadata_path / "AudioFile"

    print(f"\n[IMPORTED EVENTS]")
    for event_name in event_names:
        # Find event XML
        found = False
        for xml_file in event_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall(".//object[@class='Event']"):
                name_elem = obj.find(".//property[@name='name']/value")
                if name_elem is not None and name_elem.text == event_name:
                    found = True
                    event_id = obj.get('id')

                    print(f"\n  Event: {event_name}")
                    print(f"    XML: {xml_file.name}")
                    print(f"    ID: {event_id}")

                    # Check relationships
                    bank_rel = obj.find(".//relationship[@name='banks']/destination")
                    if bank_rel is not None:
                        print(f"    Bank relationship: {bank_rel.text}")

                    group_tracks = obj.findall(".//relationship[@name='groupTracks']/destination")
                    print(f"    GroupTracks: {len(group_tracks)}")

                    # Find SingleSounds/MultiSounds in this XML
                    single_sounds = root.findall(".//object[@class='SingleSound']")
                    multi_sounds = root.findall(".//object[@class='MultiSound']")
                    print(f"    SingleSounds in XML: {len(single_sounds)}")
                    print(f"    MultiSounds in XML: {len(multi_sounds)}")

                    # Check audio files
                    for ms in multi_sounds:
                        sounds_rel = ms.findall(".//relationship[@name='sounds']/destination")
                        print(f"      MultiSound has {len(sounds_rel)} sounds in relationship")

                    for i, ss in enumerate(single_sounds[:3], 1):
                        audio_rel = ss.find(".//relationship[@name='audioFile']/destination")
                        if audio_rel is not None:
                            audio_id = audio_rel.text
                            # Try to find this audio file
                            audio_file = audio_dir / f"{audio_id}.xml"
                            if audio_file.exists():
                                audio_tree = ET.parse(audio_file)
                                audio_root = audio_tree.getroot()
                                asset_path_elem = audio_root.find(".//property[@name='assetPath']/value")
                                if asset_path_elem is not None:
                                    print(f"      SingleSound {i} -> {asset_path_elem.text}")

                    break

        if not found:
            print(f"\n  Event: {event_name} - NOT FOUND IN FMOD")

    print(f"\n[AUDIO FILES IN FMOD] (sampling first 10)")
    audio_files = list(audio_dir.glob("*.xml"))[:10]
    for audio_file in audio_files:
        tree = ET.parse(audio_file)
        root = tree.getroot()

        audio_obj = root.find(".//object[@class='AudioFile']")
        if audio_obj is not None:
            asset_path = audio_obj.find(".//property[@name='assetPath']/value")
            if asset_path is not None:
                print(f"  {asset_path.text}")


def main():
    """Main debug pipeline"""
    print("FMOD IMPORT PIPELINE DEBUGGER")
    print("=" * 80)

    # Load project
    project_path = Path("D:/Git/Fmod Scripts/Moco AutoImport/MocoAutoImport/MocoAutoImport.fspro")

    if not project_path.exists():
        print(f"ERROR: Project not found: {project_path}")
        return

    print(f"\nLoading project: {project_path}")
    project = FMODProject(str(project_path))

    # Dump initial state
    dump_fmod_project_state(project, "FMOD PROJECT INITIAL STATE")

    # Look for latest JSON
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    json_files = sorted(temp_dir.glob("moco_import_data_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if json_files:
        latest_json = json_files[0]
        print(f"\nFound latest JSON: {latest_json}")
        dump_json_payload(latest_json)

        # Load event names from JSON
        with open(latest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        event_names = [e['newEventName'] for e in data.get('events', [])]

        # Dump post-import state
        dump_fmod_post_import(project_path, event_names)
    else:
        print("\nNo JSON files found in temp directory")

    print(f"\n{'='*80}")
    print("DEBUG COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
