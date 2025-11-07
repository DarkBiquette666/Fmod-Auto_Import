#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the new intelligent matching system
"""

import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, r"D:\Git\Fmod Scripts")

from moco_auto_import import AudioMatcher

def test_mechaflora_cases():
    """Test the Mechaflora examples provided by the user"""

    print("=" * 80)
    print("Testing Mechaflora Cases")
    print("=" * 80)

    # Setup
    prefix = "Mechaflora"
    character = "Weak_Ranged"

    # Expected events from template
    expected_events = {
        "Mechaflora_Weak_Ranged_AttackA": {},
        "Mechaflora_Weak_Ranged_IdleA": {},
        "Mechaflora_Weak_Ranged_Death": {},
    }

    # Audio files found
    audio_files = [
        {'filename': 'Mechaflora_Weak_Ranged_Attack_A.wav', 'basename': 'Mechaflora_Weak_Ranged_Attack_A', 'path': '/test/Attack_A.wav'},
        {'filename': 'Mechaflora_Weak_Ranged_Idle_A.wav', 'basename': 'Mechaflora_Weak_Ranged_Idle_A', 'path': '/test/Idle_A.wav'},
        {'filename': 'Mechaflora_Weak_Death.wav', 'basename': 'Mechaflora_Weak_Death', 'path': '/test/Death.wav'},
    ]

    print(f"\nPrefix: {prefix}")
    print(f"Character: {character}")
    print(f"\nExpected Events:")
    for event_name in expected_events.keys():
        print(f"  - {event_name}")

    print(f"\nAudio Files:")
    for audio in audio_files:
        print(f"  - {audio['basename']}")

    print("\n" + "-" * 80)
    print("Running Matching Algorithm...")
    print("-" * 80)

    # Test matching
    matches = AudioMatcher.match_files_to_events(audio_files, prefix, character, expected_events)

    print("\nMatching Results:")
    print("-" * 80)

    if not matches:
        print("❌ NO MATCHES FOUND!")
    else:
        for event_name, match_data in matches.items():
            files = match_data['files'] if isinstance(match_data, dict) else match_data
            confidence = match_data.get('confidence', 1.0) if isinstance(match_data, dict) else 1.0

            confidence_icon = ""
            if confidence >= 0.95:
                confidence_icon = "✓"
            elif confidence >= 0.85:
                confidence_icon = "~"
            elif confidence >= 0.7:
                confidence_icon = "?"
            else:
                confidence_icon = "✗"

            print(f"\n{confidence_icon} Event: {event_name}")
            print(f"   Confidence: {confidence:.2%}")
            print(f"   Matched Files:")
            for file_info in files:
                print(f"     → {file_info['basename']}")

    # Check coverage
    print("\n" + "=" * 80)
    print("Coverage Analysis:")
    print("=" * 80)

    matched_events = set(matches.keys())
    unmatched_events = set(expected_events.keys()) - matched_events

    matched_files = set()
    for match_data in matches.values():
        files = match_data['files'] if isinstance(match_data, dict) else match_data
        for f in files:
            matched_files.add(f['filename'])

    unmatched_files = {f['filename'] for f in audio_files} - matched_files

    print(f"\n✓ Matched Events: {len(matched_events)}/{len(expected_events)}")
    for event in matched_events:
        print(f"  - {event}")

    if unmatched_events:
        print(f"\n✗ Unmatched Events (Orphans): {len(unmatched_events)}")
        for event in unmatched_events:
            print(f"  - {event}")

    print(f"\n✓ Matched Files: {len(matched_files)}/{len(audio_files)}")
    for file in matched_files:
        print(f"  - {file}")

    if unmatched_files:
        print(f"\n✗ Unmatched Files (Orphans): {len(unmatched_files)}")
        for file in unmatched_files:
            print(f"  - {file}")

    print("\n" + "=" * 80)

    # Test individual functions
    print("\nDetailed Analysis:")
    print("=" * 80)

    for audio in audio_files:
        basename = audio['basename']
        print(f"\nFile: {basename}")

        suffix = AudioMatcher.extract_suffix_from_basename(basename, prefix, character)
        print(f"  Extracted Suffix: {suffix}")

        if suffix:
            for event_name in expected_events.keys():
                # Extract suffix from event name properly
                exact_pattern = f"{prefix}_{character}_"
                event_suffix = None

                if event_name.startswith(exact_pattern):
                    event_suffix = event_name[len(exact_pattern):]
                else:
                    # Try partial character matching
                    prefix_pattern = f"{prefix}_"
                    if event_name.startswith(prefix_pattern):
                        after_prefix = event_name[len(prefix_pattern):]

                        # Split character into parts and try to match
                        char_parts = character.split('_')
                        for i in range(len(char_parts), 0, -1):
                            partial_char = '_'.join(char_parts[:i]) + '_'
                            if after_prefix.startswith(partial_char):
                                event_suffix = after_prefix[len(partial_char):]
                                break

                if event_suffix:
                    similarity = AudioMatcher.calculate_similarity(suffix, event_suffix)
                    print(f"  Similarity to '{event_suffix}': {similarity:.2%}")

if __name__ == "__main__":
    test_mechaflora_cases()
