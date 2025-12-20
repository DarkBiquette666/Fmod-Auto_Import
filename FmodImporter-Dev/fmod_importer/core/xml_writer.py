"""XML writing utilities for FMOD project management.

Shared utilities for writing properly formatted XML files.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path


def write_pretty_xml(element: ET.Element, filepath: Path):
    """
    Write an XML element tree to a file with proper formatting.

    Args:
        element: The root XML element to write
        filepath: Path where to write the XML file

    The output will be properly indented with tabs and encoded in UTF-8.
    """
    # Convert element tree to string
    xml_str = ET.tostring(element, encoding='unicode')

    # Parse and prettify
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='\t', encoding='UTF-8')

    # Write to file
    with open(filepath, 'wb') as f:
        f.write(pretty_xml)
