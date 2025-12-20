"""Audio file management for FMOD project.

Handles creation of AudioFile XML entries with audio properties.
"""

import uuid
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

from .xml_writer import write_pretty_xml


class AudioFileManager:
    """Static methods for audio file operations."""

    @staticmethod
    def create(audio_file_path: str, asset_relative_path: str,
               metadata_path: Path, workspace: Dict) -> str:
        """
        Create an AudioFile XML entry in the FMOD project.

        Args:
            audio_file_path: Full path to the source audio file
            asset_relative_path: Relative path within FMOD project (e.g., "Characters/Cat.wav")
            metadata_path: Path to the Metadata directory
            workspace: Workspace dictionary with master folder references

        Returns:
            The new AudioFile UUID

        Raises:
            ValueError: If audio file cannot be read
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
        dest.text = workspace['masterAssetFolder']

        # Ensure AudioFile directory exists
        audio_file_dir = metadata_path / "AudioFile"
        audio_file_dir.mkdir(exist_ok=True)

        # Write XML to file
        audio_file_xml_path = audio_file_dir / f"{audio_file_id}.xml"
        write_pretty_xml(root, audio_file_xml_path)

        return audio_file_id
