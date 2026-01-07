import unittest
import sys
from pathlib import Path

# Add parent directory to path to allow import
sys.path.append(str(Path(__file__).parent.parent))

from fmod_importer.naming import NamingPattern, normalize_for_comparison

class TestNamingPattern(unittest.TestCase):
    def test_basic_parsing_simple(self):
        """Test parsing simple pattern $prefix_$feature_$action with single-word components"""
        pattern = NamingPattern("$prefix_$feature_$action")
        
        # Test exact match with simple words (unambiguous)
        result = pattern.parse_asset("Mechaflora_Boss_Attack")
        self.assertEqual(result['prefix'], 'Mechaflora')
        self.assertEqual(result['feature'], 'Boss')
        self.assertEqual(result['action'], 'Attack')

    def test_basic_parsing_complex_ambiguous(self):
        """
        Test parsing complex pattern where components contain separators.
        Without user_values, regex is ambiguous and will split on first separator.
        This test documents expected 'failure' of automatic parsing in ambiguous cases.
        """
        pattern = NamingPattern("$prefix_$feature_$action")
        
        # "Strong_Repair" contains separator. Regex non-greedy feature captures "Strong".
        result = pattern.parse_asset("Mechaflora_Strong_Repair_Attack")
        
        # Expect 'incorrect' but predictable regex behavior
        self.assertEqual(result['prefix'], 'Mechaflora')
        self.assertEqual(result['feature'], 'Strong') 
        self.assertEqual(result['action'], 'Repair_Attack')

    def test_parsing_with_user_values(self):
        """Test parsing with known user values to resolve ambiguity"""
        pattern = NamingPattern("$prefix_$feature_$action")
        user_values = {'prefix': 'Mechaflora', 'feature': 'Strong_Repair'}
        
        result = pattern.parse_asset("Mechaflora_Strong_Repair_Attack", user_values)
        self.assertEqual(result['action'], 'Attack')
        self.assertEqual(result['feature'], 'Strong_Repair')

    def test_iterator_stripping(self):
        """Test that iterators are stripped before parsing"""
        pattern = NamingPattern("$prefix_$feature_$action")
        
        # Use simple words to avoid regex ambiguity distracting from the test
        result = pattern.parse_asset("Mechaflora_Boss_Attack_01")
        self.assertEqual(result['action'], 'Attack')
        self.assertEqual(result['feature'], 'Boss')

    def test_variation_parsing(self):
        """Test parsing with variation tag"""
        pattern = NamingPattern("$prefix_$feature_$action_$variation")
        
        # Use simple words
        result = pattern.parse_asset("Mechaflora_Boss_Attack_A_01")
        self.assertEqual(result['action'], 'Attack')
        self.assertEqual(result['variation'], 'A')

    def test_camel_case_fails_without_hints(self):
        """Test CamelCase pattern without separators is ambiguous"""
        pattern = NamingPattern("$prefix$feature$action", separator="")
        
        # Regex greedy match consumes everything into first group
        result = pattern.parse_asset("MechafloraStrongRepairAttack")
        # prefix matches everything because [A-Za-z0-9]+ captures it all
        self.assertNotEqual(result['action'], 'Attack') 

    def test_camel_case_with_user_values(self):
        """Test CamelCase parsing with known user values"""
        pattern = NamingPattern("$prefix$feature$action", separator="")
        user_values = {'prefix': 'Mechaflora', 'feature': 'StrongRepair'}
        
        result = pattern.parse_asset("MechafloraStrongRepairAttack", user_values)
        self.assertEqual(result['action'], 'Attack')

    def test_generic_extraction(self):
        """
        Test generic action extraction logic.
        This is the robust method used when user inputs are known.
        """
        pattern = NamingPattern("$prefix_$feature_$action")
        
        # Scenario: User knows prefix="Mechaflora" and feature="Boss"
        # File: "Mechaflora_Boss_Attack_Heavy_01"
        # Action should be "Attack_Heavy"
        
        action = pattern.extract_action_generic(
            "Mechaflora_Boss_Attack_Heavy_01",
            prefix="Mechaflora",
            feature="Boss"
        )
        self.assertEqual(action, "Attack_Heavy")

    def test_generic_extraction_flexible(self):
        """Test generic extraction handles separator mismatch (User: Camel, File: Snake)"""
        pattern = NamingPattern("$prefix_$feature_$action")
        
        # User input: CamelCase
        prefix = "Mechaflora"
        feature = "StrongRepair" 
        
        # File: Snake_Case
        filename = "Mechaflora_Strong_Repair_Attack_01"
        
        # Logic: 
        # 1. Remove prefix -> "Strong_Repair_Attack_01"
        # 2. Find feature "StrongRepair" in "Strong_Repair_Attack..."
        #    "Strong_Repair" normalizes to "strongrepair". Match!
        # 3. Remainder is "Attack"
        
        action = pattern.extract_action_generic(filename, prefix, feature)
        self.assertEqual(action, "Attack")

    def test_build_name(self):
        """Test building event name from components"""
        pattern = NamingPattern("$prefix_$feature_$action")
        name = pattern.build(prefix="Mechaflora", feature="Boss", action="Attack")
        self.assertEqual(name, "Mechaflora_Boss_Attack")

    def test_normalization(self):
        """Test string normalization"""
        self.assertEqual(normalize_for_comparison("Strong_Repair"), "strongrepair")
        self.assertEqual(normalize_for_comparison("Strong Repair"), "strongrepair")
        # Note: current implementation retains hyphens
        self.assertEqual(normalize_for_comparison("Strong-Repair"), "strong-repair")

if __name__ == '__main__':
    unittest.main()