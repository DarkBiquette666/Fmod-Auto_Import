"""Bus management for FMOD project.

Handles creation and deletion of mixer buses (MixerGroup objects).
"""

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

from .xml_writer import write_pretty_xml


class BusManager:
    """Static methods for bus (mixer group) operations."""

    @staticmethod
    def create(name: str, parent_id: str, metadata_path: Path, buses_dict: Dict) -> str:
        """
        Create a new bus (MixerGroup).

        Args:
            name: Name of the bus
            parent_id: Parent bus ID (output destination)
            metadata_path: Path to the Metadata directory
            buses_dict: Dictionary of buses to update

        Returns:
            UUID of the created bus
        """
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
        group_folder = metadata_path / "Group"
        group_folder.mkdir(exist_ok=True)

        # Write to file
        bus_file = group_folder / f"{bus_id}.xml"
        write_pretty_xml(root, bus_file)

        # Update internal structure
        buses_dict[bus_id] = {
            'name': name,
            'path': bus_file,
            'parent': parent_id
        }

        return bus_id

    @staticmethod
    def delete(bus_id: str, buses_dict: Dict, metadata_path: Path):
        """
        Delete a bus.

        Args:
            bus_id: UUID of the bus to delete
            buses_dict: Dictionary of buses to update
            metadata_path: Path to the Metadata directory (unused but kept for consistency)
        """
        if bus_id in buses_dict:
            bus_path = buses_dict[bus_id]['path']
            if bus_path.exists():
                bus_path.unlink()
            del buses_dict[bus_id]

    @staticmethod
    def get_master_bus_id(buses_dict: Dict) -> Optional[str]:
        """
        Get the master bus ID.

        The master bus is identified by having no parent (parent = None).

        Args:
            buses_dict: Dictionary of buses

        Returns:
            UUID of the master bus, or None if not found
        """
        for bus_id, bus_info in buses_dict.items():
            if bus_info['parent'] is None:  # Master bus has no parent
                return bus_id
        return None
