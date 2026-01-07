import unittest
import tempfile
import shutil
import os
from pathlib import Path
import xml.etree.ElementTree as ET

# Add parent directory to path to allow import
import sys
sys.path.append(str(Path(__file__).parent.parent))

from fmod_importer.core.pending_folder_manager import PendingFolderManager

class TestPendingFolderManager(unittest.TestCase):
    def setUp(self):
        self.manager = PendingFolderManager()
        self.test_dir = tempfile.mkdtemp()
        self.metadata_path = Path(self.test_dir)
        
        # Dummy committed dicts
        self.event_folders = {}
        self.asset_folders = {}
        self.banks = {}
        self.buses = {}
        self.workspace = {
            'masterEventFolder': 'master_event',
            'masterBankFolder': 'master_bank',
            'masterAssetFolder': 'master_asset'
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_add_and_check_pending(self):
        """Test adding items and checking is_pending status"""
        self.manager.add_event_folder('folder1', {'name': 'Folder 1', 'parent': 'master_event'})
        self.assertTrue(self.manager.is_pending('folder1'))
        self.assertFalse(self.manager.is_pending('non_existent'))
        
        self.manager.add_bank('bank1', {'name': 'Bank 1', 'parent': 'master_bank', 'type': 'bank'})
        self.assertTrue(self.manager.is_pending('bank1'))

    def test_get_all_merged(self):
        """Test that get_all_... returns merged dictionaries"""
        # Setup committed
        self.event_folders['committed1'] = {'name': 'Committed'}
        
        # Add pending
        self.manager.add_event_folder('pending1', {'name': 'Pending'})
        
        # Check merge
        merged = self.manager.get_all_event_folders(self.event_folders)
        self.assertIn('committed1', merged)
        self.assertIn('pending1', merged)
        self.assertEqual(len(merged), 2)

    def test_commit_event_folder(self):
        """Test committing an event folder writes XML"""
        # Add pending folder
        folder_id = '{fake-uuid}'
        self.manager.add_event_folder(folder_id, {
            'name': 'New Folder', 
            'parent': 'master_event'
        })
        
        # Commit
        counts = self.manager.commit_all(
            self.event_folders, self.asset_folders, 
            self.banks, self.buses, 
            self.workspace, self.metadata_path
        )
        
        # Verify count (events, assets, banks, buses)
        self.assertEqual(counts, (1, 0, 0, 0))
        
        # Verify file exists
        expected_file = self.metadata_path / "EventFolder" / f"{folder_id}.xml"
        self.assertTrue(expected_file.exists())
        
        # Verify content
        tree = ET.parse(expected_file)
        root = tree.getroot()
        self.assertEqual(root.find(".//property[@name='name']/value").text, 'New Folder')
        
        # Verify it moved to committed dict
        self.assertIn(folder_id, self.event_folders)
        self.assertFalse(self.manager.is_pending(folder_id))

    def test_topological_sort(self):
        """Test that parents are created before children"""
        # Parent
        self.manager.add_event_folder('parent', {
            'name': 'Parent', 
            'parent': 'master_event'
        })
        # Child (depends on Parent)
        self.manager.add_event_folder('child', {
            'name': 'Child', 
            'parent': 'parent'
        })
        
        counts = self.manager.commit_all(
            self.event_folders, self.asset_folders, 
            self.banks, self.buses, 
            self.workspace, self.metadata_path
        )
        
        self.assertEqual(counts, (2, 0, 0, 0))
        self.assertTrue((self.metadata_path / "EventFolder" / "parent.xml").exists())
        self.assertTrue((self.metadata_path / "EventFolder" / "child.xml").exists())

    def test_commit_bank_and_bus(self):
        """Test committing banks and buses"""
        # Bank
        self.manager.add_bank('bank1', {
            'name': 'New Bank',
            'parent': 'master_bank',
            'type': 'bank'
        })
        # Bus
        self.manager.add_bus('bus1', {
            'name': 'New Bus',
            'parent': None # Master bus
        })

        counts = self.manager.commit_all(
            self.event_folders, self.asset_folders, 
            self.banks, self.buses, 
            self.workspace, self.metadata_path
        )

        self.assertEqual(counts, (0, 0, 1, 1))
        self.assertTrue((self.metadata_path / "Bank" / "bank1.xml").exists())
        self.assertTrue((self.metadata_path / "Group" / "bus1.xml").exists())

if __name__ == '__main__':
    unittest.main()
