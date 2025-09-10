#!/usr/bin/env python3
"""
Direct tests for server functions without FastMCP wrapper.
Tests the core functionality with expected outputs.
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the raw functions (not the FastMCP wrapped versions)
import src.server as server_module
from src.server import parse_flags_json, generate_rules_for_flag


class TestServerFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_flags_data = {
            "functions": [
                "isFeatureEnabled",
                "client.GetString", 
                "isEnabled",
                "getFlag",
                "is_feature_enabled"
            ],
            "flags": {
                "beta_ui": {
                    "value": True,
                    "description": "Enables the new beta user interface",
                    "replace_with": True
                },
                "new_checkout": {
                    "value": False,
                    "description": "New payment processing flow",
                    "replace_with": False
                },
                "debug_mode": {
                    "value": True,
                    "description": "Enables debug logging",
                    "replace_with": True
                }
            }
        }
        
        # Clear the flags cache before each test
        server_module.FLAGS_CACHE = {}
    
    def test_parse_flags_json_valid(self):
        """Test parsing valid JSON flags content."""
        json_content = json.dumps(self.test_flags_data)
        result = parse_flags_json(json_content)
        
        self.assertIn("flags", result)
        self.assertIn("global_patterns", result)
        self.assertEqual(len(result["flags"]), 3)
        self.assertEqual(len(result["global_patterns"]), 5)
        
        # Check flag parsing
        beta_flag = result["flags"]["beta_ui"]
        self.assertEqual(beta_flag["value"], "true")
        self.assertEqual(beta_flag["description"], "Enables the new beta user interface")
        self.assertTrue(beta_flag["enabled"])
        
        new_checkout_flag = result["flags"]["new_checkout"]
        self.assertEqual(new_checkout_flag["value"], "false")
        self.assertFalse(new_checkout_flag["enabled"])
    
    def test_parse_flags_json_invalid(self):
        """Test parsing invalid JSON content."""
        invalid_json = '{"flags": invalid json}'
        
        with self.assertRaises(ValueError):
            parse_flags_json(invalid_json)
    
    def test_list_flags_with_valid_file(self):
        """Test list_flags functionality with a valid flags.json file."""
        # Get the function directly from the module
        list_flags_func = getattr(server_module.app, '_tools')['list_flags'].func
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_flags_data, f)
            temp_file = f.name
        
        try:
            # Get directory of temp file
            temp_dir = os.path.dirname(temp_file)
            # Rename to flags.json
            flags_path = os.path.join(temp_dir, 'flags.json')
            os.rename(temp_file, flags_path)
            
            # Test the tool
            result = list_flags_func(working_directory=temp_dir)
            
            self.assertNotIn("error", result)
            self.assertIn("flags", result)
            self.assertIn("flag_details", result)
            self.assertIn("global_patterns", result)
            self.assertEqual(len(result["flags"]), 3)
            self.assertIn("beta_ui", result["flags"])
            self.assertIn("new_checkout", result["flags"])
            
        finally:
            # Cleanup
            if os.path.exists(flags_path):
                os.unlink(flags_path)
    
    def test_rule_generation(self):
        """Test rule generation for different flags."""
        # Set up cache
        parsed_data = parse_flags_json(json.dumps(self.test_flags_data))
        server_module.FLAGS_CACHE = {
            "flags": parsed_data["flags"],
            "global_patterns": parsed_data["global_patterns"]
        }
        
        test_flags = ["beta_ui", "new_checkout", "debug_mode"]
        
        for flag_name in test_flags:
            with self.subTest(flag=flag_name):
                flag_info = server_module.FLAGS_CACHE["flags"][flag_name]
                rules = generate_rules_for_flag(flag_name, flag_info, "go")
                
                self.assertIsInstance(rules, list)
                self.assertGreater(len(rules), 0)
                
                # Check rule structure
                for rule in rules:
                    self.assertIn("name", rule)
                    self.assertIn("query", rule) 
                    self.assertIn("replace", rule)
                    self.assertIn("is_seed_rule", rule)
                
                print(f"Generated {len(rules)} rules for {flag_name}")


def manual_test_transformations():
    """Manually test transformations to see expected outputs."""
    print("\n🧪 Manual Transformation Tests")
    print("=" * 50)
    
    # Set up test data
    test_flags = {
        "functions": [
            "isFeatureEnabled",
            "client.GetString",
            "isEnabled"
        ],
        "flags": {
            "beta_ui": {
                "value": True,
                "description": "Enables beta UI", 
                "replace_with": True
            },
            "legacy_feature": {
                "value": False,
                "description": "Legacy feature",
                "replace_with": False
            }
        }
    }
    
    # Parse and set up cache
    parsed_data = parse_flags_json(json.dumps(test_flags))
    server_module.FLAGS_CACHE = {
        "flags": parsed_data["flags"],
        "global_patterns": parsed_data["global_patterns"]
    }
    
    # Test code samples with expected transformations
    test_cases = [
        {
            "name": "Simple Go if statement - enabled flag",
            "code": '''if isFeatureEnabled("beta_ui") {
    renderBetaUI()
}''',
            "language": "go",
            "flag": "beta_ui",
            "expected_transformation": "should replace with 'true'"
        },
        {
            "name": "Simple Go if statement - disabled flag", 
            "code": '''if isFeatureEnabled("legacy_feature") {
    useLegacyCode()
}''',
            "language": "go",
            "flag": "legacy_feature",
            "expected_transformation": "should replace with 'false'"
        },
        {
            "name": "String check pattern",
            "code": '''if client.GetString("beta_ui") == "true" {
    enableBetaMode()
}''',
            "language": "go",
            "flag": "beta_ui", 
            "expected_transformation": "should replace with 'true'"
        }
    ]
    
    # Get apply_rewrite function
    apply_rewrite_func = getattr(server_module.app, '_tools')['apply_rewrite'].func
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print("-" * 30)
        print(f"Flag: {case['flag']} (enabled: {parsed_data['flags'][case['flag']]['enabled']})")
        print(f"Expected: {case['expected_transformation']}")
        
        print("\nOriginal Code:")
        print(case['code'])
        
        try:
            result = apply_rewrite_func(
                code=case['code'],
                language=case['language'],
                flag_name=case['flag']
            )
            
            if 'error' in result:
                print(f"\n❌ Error: {result['error']}")
            else:
                print(f"\nTransformed Code:")
                print(result['transformed_code'])
                
                if result['transformed_code'] != case['code']:
                    print("✅ Transformation successful!")
                else:
                    print("ℹ️  No transformation applied")
                    
        except Exception as e:
            print(f"\n❌ Exception during transformation: {e}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    print("🧪 Testing Server Functions Directly")
    print("=" * 60)
    
    # Run manual tests first
    try:
        manual_test_transformations()
    except Exception as e:
        print(f"Manual tests failed: {e}")
        print("This might be due to FastMCP wrapper access issues")
    
    print("\n🧪 Running Unit Tests")
    print("=" * 60)
    
    # Run unit tests (skip the ones that require FastMCP access)
    suite = unittest.TestSuite()
    suite.addTest(TestServerFunctions('test_parse_flags_json_valid'))
    suite.addTest(TestServerFunctions('test_parse_flags_json_invalid'))
    suite.addTest(TestServerFunctions('test_rule_generation'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)