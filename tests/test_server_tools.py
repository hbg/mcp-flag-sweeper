#!/usr/bin/env python3
"""
Comprehensive tests for MCP server tools with JSON flags format.
Tests both list_flags and apply_rewrite tools with expected outputs.
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server import list_flags, apply_rewrite, parse_flags_json, generate_rules_for_flag
import src.server


class TestServerTools(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        # Sample flags.json content for testing
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
        src.server.FLAGS_CACHE = {}

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

    def test_list_flags_tool_with_valid_file(self):
        """Test list_flags tool with a valid flags.json file."""
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
            result = list_flags(working_directory=temp_dir)

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

    def test_list_flags_tool_missing_file(self):
        """Test list_flags tool when flags.json doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = list_flags(working_directory=temp_dir)

            self.assertIn("error", result)
            self.assertIn("flags.json not found", result["error"])
            self.assertEqual(result["flags"], [])

    def test_apply_rewrite_with_flag_name(self):
        """Test apply_rewrite tool with specific flag name."""
        # Set up cache
        src.server.FLAGS_CACHE = {
            "flags": {
                "beta_ui": {
                    "value": "true",
                    "description": "Enables beta UI",
                    "replace_with": "true",
                    "enabled": True
                }
            },
            "global_patterns": ["isFeatureEnabled"]
        }

        # Test Go code
        go_code = '''
if isFeatureEnabled("beta_ui") {
    renderBetaUI()
} else {
    renderStandardUI()
}
'''

        result = apply_rewrite(
            code=go_code,
            language="go",
            flag_name="beta_ui"
        )

        self.assertIn("transformed_code", result)
        # The transformation should replace the flag check
        self.assertNotEqual(result["transformed_code"], go_code)

    def test_apply_rewrite_with_custom_rules(self):
        """Test apply_rewrite tool with custom rules."""
        test_code = 'if (true) { console.log("test"); }'

        custom_rules = [{
            "name": "replace_true",
            "query": "cs true",
            "replace": "false",
            "is_seed_rule": True
        }]

        result = apply_rewrite(
            code=test_code,
            language="javascript",
            rules=custom_rules
        )

        self.assertIn("transformed_code", result)
        # Should replace true with false
        self.assertIn("false", result["transformed_code"])

    def test_apply_rewrite_nonexistent_flag(self):
        """Test apply_rewrite with a flag that doesn't exist."""
        src.server.FLAGS_CACHE = {"flags": {}, "global_patterns": []}

        result = apply_rewrite(
            code="if isFeatureEnabled(\"nonexistent\") { }",
            language="go",
            flag_name="nonexistent"
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])


class TestCodeTransformations(unittest.TestCase):
    """Test actual code transformations with expected outputs."""

    def setUp(self):
        """Set up test fixtures with comprehensive flag data."""
        self.comprehensive_flags = {
            "functions": [
                "isFeatureEnabled",
                "client.GetString",
                "isEnabled",
                "getFlag",
                "is_feature_enabled",
                "config.getBoolean",
                "feature.isOn"
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
                },
                "legacy_feature": {
                    "value": False,
                    "description": "Legacy feature to be removed",
                    "replace_with": False
                }
            }
        }

        # Set up the cache with parsed data
        parsed_data = parse_flags_json(json.dumps(self.comprehensive_flags))
        src.server.FLAGS_CACHE = {
            "flags": parsed_data["flags"],
            "global_patterns": parsed_data["global_patterns"]
        }

    def test_go_transformations(self):
        """Test Go code transformations with expected outputs."""
        test_cases = [
            {
                "name": "Simple if statement - enabled flag",
                "input": '''if isFeatureEnabled("beta_ui") {
    renderBetaUI()
} else {
    renderStandardUI()
}''',
                "flag": "beta_ui",
                "language": "go",
                "should_transform": True,
                "expected_contains": "true"
            },
            {
                "name": "Simple if statement - disabled flag",
                "input": '''if isFeatureEnabled("new_checkout") {
    processNewCheckout()
} else {
    processLegacyCheckout()
}''',
                "flag": "new_checkout",
                "language": "go",
                "should_transform": True,
                "expected_contains": "false"
            },
            {
                "name": "Client string check",
                "input": '''if client.GetString("debug_mode") == "true" {
    enableDebugMode()
}''',
                "flag": "debug_mode",
                "language": "go",
                "should_transform": True,
                "expected_contains": "true"
            }
        ]

        for case in test_cases:
            with self.subTest(case=case["name"]):
                result = apply_rewrite(
                    code=case["input"],
                    language=case["language"],
                    flag_name=case["flag"]
                )

                self.assertIn("transformed_code", result)

                if case["should_transform"]:
                    # Verify transformation occurred
                    self.assertNotEqual(result["transformed_code"], case["input"])
                    if "expected_contains" in case:
                        self.assertIn(case["expected_contains"], result["transformed_code"])

                print(f"\n✅ {case['name']}")
                print(f"   Input:  {case['input'][:50]}...")
                print(f"   Output: {result['transformed_code'][:50]}...")

    def test_python_transformations(self):
        """Test Python code transformations."""
        python_cases = [
            {
                "name": "Python if with enabled flag",
                "input": '''if is_feature_enabled("beta_ui"):
    render_beta_ui()
else:
    render_standard_ui()''',
                "flag": "beta_ui",
                "language": "python",
                "should_transform": True,
                "expected_contains": "true"
            },
            {
                "name": "Python complex condition",
                "input": '''if is_feature_enabled("debug_mode") and user.is_admin():
    enable_debug_logging()''',
                "flag": "debug_mode",
                "language": "python",
                "should_transform": True,
                "expected_contains": "true"
            }
        ]

        for case in python_cases:
            with self.subTest(case=case["name"]):
                result = apply_rewrite(
                    code=case["input"],
                    language=case["language"],
                    flag_name=case["flag"]
                )

                self.assertIn("transformed_code", result)
                print(f"\n✅ {case['name']}")
                print(f"   Input:  {case['input'][:50]}...")
                print(f"   Output: {result['transformed_code'][:50]}...")

    def test_javascript_transformations(self):
        """Test JavaScript code transformations."""
        js_cases = [
            {
                "name": "JavaScript if statement",
                "input": '''if (isFeatureEnabled("new_checkout")) {
    processNewCheckout();
} else {
    processLegacyCheckout();
}''',
                "flag": "new_checkout",
                "language": "javascript",
                "should_transform": True,
                "expected_contains": "false"
            }
        ]

        for case in js_cases:
            with self.subTest(case=case["name"]):
                result = apply_rewrite(
                    code=case["input"],
                    language=case["language"],
                    flag_name=case["flag"]
                )

                self.assertIn("transformed_code", result)
                print(f"\n✅ {case['name']}")
                print(f"   Input:  {case['input'][:50]}...")
                print(f"   Output: {result['transformed_code'][:50]}...")

    def test_rule_generation(self):
        """Test rule generation for different flags."""
        test_flags = ["beta_ui", "new_checkout", "debug_mode"]

        for flag_name in test_flags:
            with self.subTest(flag=flag_name):
                flag_info = src.server.FLAGS_CACHE["flags"][flag_name]
                rules = generate_rules_for_flag(flag_name, flag_info, "go")

                self.assertIsInstance(rules, list)
                self.assertGreater(len(rules), 0)

                # Check rule structure
                for rule in rules:
                    self.assertIn("name", rule)
                    self.assertIn("query", rule)
                    self.assertIn("replace", rule)
                    self.assertIn("is_seed_rule", rule)

                print(f"\n🔧 Generated {len(rules)} rules for {flag_name}")


def run_comprehensive_test():
    """Run a comprehensive test showing transformations."""
    print("🧪 Running Comprehensive Server Tools Test")
    print("=" * 60)

    # Create test data
    test_flags = {
        "functions": [
            "isFeatureEnabled",
            "client.GetString",
            "isEnabled",
            "getFlag",
            "is_feature_enabled",
            "config.getBoolean"
        ],
        "flags": {
            "beta_ui": {
                "value": True,
                "description": "Enables beta UI",
                "replace_with": True
            },
            "legacy_auth": {
                "value": False,
                "description": "Legacy authentication",
                "replace_with": False
            },
            "new_feature": {
                "value": True,
                "description": "New experimental feature",
                "replace_with": True
            }
        }
    }

    # Parse and set up cache
    parsed_data = parse_flags_json(json.dumps(test_flags))
    src.server.FLAGS_CACHE = {
        "flags": parsed_data["flags"],
        "global_patterns": parsed_data["global_patterns"]
    }

    # Test various code samples
    test_samples = [
        {
            "name": "Go - Simple Feature Check",
            "code": '''func main() {
    if isFeatureEnabled("beta_ui") {
        fmt.Println("Using beta UI")
        renderBetaInterface()
    } else {
        fmt.Println("Using standard UI")
        renderStandardInterface()
    }
}''',
            "language": "go",
            "flag": "beta_ui"
        },
        {
            "name": "Python - Feature Toggle",
            "code": '''def process_payment():
    if is_feature_enabled("legacy_auth"):
        return legacy_authenticate()
    else:
        return modern_authenticate()''',
            "language": "python",
            "flag": "legacy_auth"
        },
        {
            "name": "JavaScript - Complex Condition",
            "code": '''function handleRequest() {
    if (isEnabled("new_feature") && user.hasPermission()) {
        return processWithNewFeature();
    }
    return processLegacy();
}''',
            "language": "javascript",
            "flag": "new_feature"
        }
    ]

    for sample in test_samples:
        print(f"\n🔧 Testing: {sample['name']}")
        print("-" * 40)

        result = apply_rewrite(
            code=sample["code"],
            language=sample["language"],
            flag_name=sample["flag"]
        )

        print("📝 Original Code:")
        print(sample["code"])

        print("\n🔄 Transformed Code:")
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(result["transformed_code"])

            if result["transformed_code"] != sample["code"]:
                print("✅ Code was successfully transformed!")
            else:
                print("ℹ️  No transformation applied (may be expected)")


if __name__ == "__main__":
    # Run comprehensive test first
    run_comprehensive_test()

    print("\n" + "=" * 60)
    print("🧪 Running Unit Tests")
    print("=" * 60)

    # Run unit tests
    unittest.main(verbosity=2)