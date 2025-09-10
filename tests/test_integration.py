#!/usr/bin/env python3
"""
Integration tests that demonstrate expected code transformations.
This bypasses FastMCP and tests the core Piranha transformation logic.
"""

import sys
import os
import json

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.server as server_module
from src.server import parse_flags_json, generate_rules_for_flag
from polyglot_piranha import execute_piranha, PiranhaArguments, Rule, RuleGraph


def test_flag_transformations():
    """Test actual code transformations with expected outputs."""
    print("🧪 Integration Test: Code Transformations")
    print("=" * 60)
    
    # Set up comprehensive test flags
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
            },
            "disabled_feature": {
                "value": False,
                "description": "Disabled feature",
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
    
    # Test cases with expected transformations
    test_cases = [
        {
            "name": "Go - Enabled Flag Simple If",
            "code": '''func main() {
    if isFeatureEnabled("beta_ui") {
        renderBetaUI()
    } else {
        renderStandardUI()
    }
}''',
            "language": "go",
            "flag": "beta_ui",
            "expected_contains": ["true"],
            "should_transform": True
        },
        {
            "name": "Go - Disabled Flag Simple If", 
            "code": '''func processAuth() {
    if isFeatureEnabled("legacy_auth") {
        return legacyAuth()
    }
    return modernAuth()
}''',
            "language": "go", 
            "flag": "legacy_auth",
            "expected_contains": ["false"],
            "should_transform": True
        },
        {
            "name": "Python - Enabled Feature",
            "code": '''def handle_request():
    if is_feature_enabled("new_feature"):
        return new_handler()
    return old_handler()''',
            "language": "python",
            "flag": "new_feature", 
            "expected_contains": ["true"],
            "should_transform": True
        },
        {
            "name": "Java - String Comparison",
            "code": '''public void checkFeature() {
    if (getFlag("disabled_feature").equals("true")) {
        enableFeature();
    } else {
        disableFeature();
    }
}''',
            "language": "java",
            "flag": "disabled_feature",
            "expected_contains": ["false"],
            "should_transform": True
        },
        {
            "name": "Go - Complex Condition",
            "code": '''if isFeatureEnabled("beta_ui") && user.hasPermission() {
    showBetaFeatures()
}''',
            "language": "go",
            "flag": "beta_ui",
            "expected_contains": ["true"],
            "should_transform": True
        }
    ]
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {case['name']}")
        print("-" * 40)
        
        flag_info = parsed_data["flags"][case["flag"]]
        print(f"Flag '{case['flag']}': enabled={flag_info['enabled']}, value={flag_info['value']}")
        
        # Generate rules for this flag
        rules = generate_rules_for_flag(case["flag"], flag_info, case["language"])
        print(f"Generated {len(rules)} transformation rules")
        
        if len(rules) == 0:
            print("❌ No rules generated - cannot test transformation")
            results.append({"case": case["name"], "success": False, "reason": "No rules generated"})
            continue
        
        try:
            # Convert to Piranha Rule objects
            rule_objs = []
            for rule_dict in rules:
                rule_objs.append(Rule(**rule_dict))
            
            # Execute transformation
            args = PiranhaArguments(
                code_snippet=case["code"],
                language=case["language"],
                rule_graph=RuleGraph(rules=rule_objs, edges=[])
            )
            
            summaries = execute_piranha(args)
            
            if summaries and len(summaries) > 0:
                transformed_code = summaries[0].content
                
                print("📝 Original Code:")
                for line_num, line in enumerate(case["code"].split('\\n'), 1):
                    print(f"   {line_num:2d}: {line}")
                
                print("\\n🔄 Transformed Code:")
                for line_num, line in enumerate(transformed_code.split('\\n'), 1):
                    print(f"   {line_num:2d}: {line}")
                
                # Check if transformation occurred
                transformation_occurred = transformed_code != case["code"]
                
                if transformation_occurred:
                    print("✅ Code was transformed!")
                    
                    # Check for expected content
                    all_expected_found = True
                    for expected in case.get("expected_contains", []):
                        if expected in transformed_code:
                            print(f"   ✓ Contains expected '{expected}'")
                        else:
                            print(f"   ❌ Missing expected '{expected}'")
                            all_expected_found = False
                    
                    success = all_expected_found
                    results.append({
                        "case": case["name"], 
                        "success": success,
                        "transformed": True,
                        "expected_found": all_expected_found
                    })
                    
                else:
                    print("ℹ️  No transformation applied")
                    success = not case["should_transform"]  # Success if we didn't expect transformation
                    results.append({
                        "case": case["name"],
                        "success": success, 
                        "transformed": False,
                        "reason": "No transformation applied"
                    })
            else:
                print("❌ Piranha returned no results")
                results.append({
                    "case": case["name"],
                    "success": False,
                    "reason": "No Piranha results"
                })
                
        except Exception as e:
            print(f"❌ Error during transformation: {str(e)}")
            results.append({
                "case": case["name"],
                "success": False, 
                "reason": f"Exception: {str(e)}"
            })
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total} ({successful/total*100:.1f}%)")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['case']}")
        if not result["success"] and "reason" in result:
            print(f"   Reason: {result['reason']}")
    
    return results


def test_json_parsing_comprehensive():
    """Test comprehensive JSON parsing functionality."""
    print("\\n🧪 JSON Parsing Tests")
    print("=" * 30)
    
    # Test various JSON structures
    test_cases = [
        {
            "name": "Complete JSON structure",
            "json": {
                "functions": ["func1", "func2"],
                "flags": {
                    "flag1": {"value": True, "description": "Test", "replace_with": True},
                    "flag2": {"value": False, "description": "Test2", "replace_with": False}
                }
            },
            "expected_flags": 2,
            "expected_functions": 2
        },
        {
            "name": "Minimal JSON structure",
            "json": {
                "functions": ["test"],
                "flags": {
                    "minimal": {"value": True}
                }
            },
            "expected_flags": 1,
            "expected_functions": 1
        },
        {
            "name": "Mixed boolean/string values",
            "json": {
                "functions": ["check"],
                "flags": {
                    "bool_true": {"value": True, "replace_with": True},
                    "bool_false": {"value": False, "replace_with": False},
                    "str_true": {"value": "true", "replace_with": "true"},
                    "str_false": {"value": "false", "replace_with": "false"}
                }
            },
            "expected_flags": 4,
            "expected_functions": 1
        }
    ]
    
    for case in test_cases:
        print(f"\\n📋 {case['name']}")
        
        try:
            json_str = json.dumps(case["json"])
            result = parse_flags_json(json_str)
            
            print(f"   Flags parsed: {len(result['flags'])}/{case['expected_flags']}")
            print(f"   Functions parsed: {len(result['global_patterns'])}/{case['expected_functions']}")
            
            # Verify flag parsing
            for flag_name, flag_data in result["flags"].items():
                enabled_status = "✅" if flag_data["enabled"] else "❌"
                print(f"   {enabled_status} {flag_name}: {flag_data['value']} -> {flag_data['replace_with']}")
            
            assert len(result['flags']) == case['expected_flags']
            assert len(result['global_patterns']) == case['expected_functions']
            print("   ✅ Parsing successful")
            
        except Exception as e:
            print(f"   ❌ Parsing failed: {e}")


if __name__ == "__main__":
    # Run JSON parsing tests
    test_json_parsing_comprehensive()
    
    # Run transformation tests
    transformation_results = test_flag_transformations()
    
    # Final summary
    print("\\n🎯 Overall Test Summary")
    print("=" * 60)
    
    successful_transformations = sum(1 for r in transformation_results if r["success"])
    total_transformations = len(transformation_results)
    
    if successful_transformations == total_transformations:
        print("🎉 All tests passed! The server tools are working correctly.")
    else:
        print(f"⚠️  {total_transformations - successful_transformations} tests failed.")
        print("   This might indicate issues with rule generation or Piranha integration.")
    
    print("\\nTest completed. Check the detailed output above for specific transformation examples.")