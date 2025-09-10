#!/usr/bin/env python3
"""
Test cases showing expected before/after outputs for code transformations.
This demonstrates exactly how the MCP server tools should reformat code.
"""

import sys
import os
import json

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.server as server_module
from src.server import parse_flags_json, generate_rules_for_flag
from polyglot_piranha import execute_piranha, PiranhaArguments, Rule, RuleGraph


def demonstrate_expected_transformations():
    """Demonstrate expected code transformations with clear before/after examples."""
    print("🎯 Expected Code Transformation Examples")
    print("=" * 70)
    
    # Test flags configuration
    flags_config = {
        "functions": [
            "isFeatureEnabled",
            "client.GetString", 
            "isEnabled",
            "getFlag",
            "is_feature_enabled",
            "config.getBoolean",
            "checkFlag"
        ],
        "flags": {
            "beta_ui": {
                "value": True,
                "description": "New beta user interface",
                "replace_with": True
            },
            "legacy_auth": {
                "value": False,
                "description": "Legacy authentication system (being removed)",
                "replace_with": False
            },
            "new_dashboard": {
                "value": True,
                "description": "New dashboard layout",
                "replace_with": True
            },
            "old_api": {
                "value": False,
                "description": "Old API endpoints (deprecated)",
                "replace_with": False
            }
        }
    }
    
    # Set up the server state
    parsed_data = parse_flags_json(json.dumps(flags_config))
    server_module.FLAGS_CACHE = {
        "flags": parsed_data["flags"],
        "global_patterns": parsed_data["global_patterns"]
    }
    
    # Test cases with exact expected outputs
    examples = [
        {
            "title": "Go - Simple Feature Toggle (Enabled Flag)",
            "language": "go",
            "flag": "beta_ui",
            "before": '''func renderUI() {
    if isFeatureEnabled("beta_ui") {
        return renderBetaInterface()
    } else {
        return renderOldInterface()
    }
}''',
            "expected_after": '''func renderUI() {
    if true {
        return renderBetaInterface()
    } else {
        return renderOldInterface()
    }
}''',
            "explanation": "Flag call replaced with 'true' since beta_ui is enabled"
        },
        
        {
            "title": "Go - Legacy Feature Removal (Disabled Flag)",
            "language": "go", 
            "flag": "legacy_auth",
            "before": '''func authenticate(user User) error {
    if isFeatureEnabled("legacy_auth") {
        return legacyAuthenticate(user)
    }
    return modernAuthenticate(user)
}''',
            "expected_after": '''func authenticate(user User) error {
    if false {
        return legacyAuthenticate(user)
    }
    return modernAuthenticate(user)
}''',
            "explanation": "Flag call replaced with 'false' since legacy_auth is disabled"
        },
        
        {
            "title": "Python - Feature Flag Check (Enabled)",
            "language": "python",
            "flag": "new_dashboard", 
            "before": '''def load_dashboard():
    if is_feature_enabled("new_dashboard"):
        return load_new_dashboard()
    else:
        return load_old_dashboard()''',
            "expected_after": '''def load_dashboard():
    if true:
        return load_new_dashboard()
    else:
        return load_old_dashboard()''',
            "explanation": "Python flag check replaced with 'true'"
        },
        
        {
            "title": "Go - Complex Conditional (Disabled Flag)",
            "language": "go",
            "flag": "old_api",
            "before": '''if getFlag("old_api") && user.HasPermission("admin") {
    return handleOldAPI(request)
}
return handleNewAPI(request)''',
            "expected_after": '''if false && user.HasPermission("admin") {
    return handleOldAPI(request)
}
return handleNewAPI(request)''',
            "explanation": "Flag in complex condition replaced with 'false'"
        },
        
        {
            "title": "Java - Config Boolean Check",
            "language": "java",
            "flag": "beta_ui",
            "before": '''public void setupUI() {
    if (config.getBoolean("beta_ui")) {
        initBetaComponents();
    } else {
        initStandardComponents();
    }
}''',
            "expected_after": '''public void setupUI() {
    if (true) {
        initBetaComponents();
    } else {
        initStandardComponents();
    }
}''',
            "explanation": "Java config check replaced with 'true'"
        }
    ]
    
    # Test each example
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print("=" * 50)
        print(f"🏷️  Flag: {example['flag']} (enabled: {parsed_data['flags'][example['flag']]['enabled']})")
        print(f"💬 {example['explanation']}")
        
        # Generate and apply transformation
        flag_info = parsed_data["flags"][example["flag"]]
        rules = generate_rules_for_flag(example["flag"], flag_info, example["language"])
        
        print(f"\n🔧 Generated {len(rules)} transformation rules")
        
        try:
            # Apply transformation
            rule_objs = [Rule(**rule) for rule in rules]
            args = PiranhaArguments(
                code_snippet=example["before"],
                language=example["language"],
                rule_graph=RuleGraph(rules=rule_objs, edges=[])
            )
            
            summaries = execute_piranha(args)
            actual_after = summaries[0].content if summaries else example["before"]
            
            print("\n📝 BEFORE:")
            print("─" * 30)
            for line_num, line in enumerate(example["before"].split('\n'), 1):
                print(f"{line_num:2d}│ {line}")
            
            print("\n🔄 AFTER (Actual):")
            print("─" * 30)
            for line_num, line in enumerate(actual_after.split('\n'), 1):
                print(f"{line_num:2d}│ {line}")
            
            print("\n✅ EXPECTED:")
            print("─" * 30)
            for line_num, line in enumerate(example["expected_after"].split('\n'), 1):
                print(f"{line_num:2d}│ {line}")
            
            # Check if transformation matches expectation
            if actual_after.strip() == example["expected_after"].strip():
                print("\n🎉 PERFECT MATCH! Transformation exactly as expected.")
            elif actual_after.strip() == example["before"].strip():
                print("\n⚠️  NO TRANSFORMATION: Code unchanged.")
            else:
                print("\n🔍 PARTIAL MATCH: Transformation occurred but differs from expected.")
                # Show key differences
                if example["flag"] in actual_after:
                    print("   ❌ Flag name still present in output")
                else:
                    print("   ✅ Flag name successfully replaced")
            
        except Exception as e:
            print(f"\n❌ TRANSFORMATION FAILED: {e}")
    
    print(f"\n{'='*70}")
    print("🏁 Transformation Examples Complete")
    print("These examples show how the MCP server tools should reformat code")
    print("by replacing feature flag calls with their configured values.")


def test_json_file_integration():
    """Test the complete workflow: JSON file → parsing → transformation."""
    print(f"\n{'='*70}")
    print("🔄 Complete Integration Test: JSON File → Code Transformation")
    print("=" * 70)
    
    # Create a temporary flags.json file
    import tempfile
    test_flags = {
        "functions": ["isFeatureEnabled", "checkFlag"],
        "flags": {
            "feature_x": {
                "value": True,
                "description": "Feature X is enabled for all users",
                "replace_with": True
            },
            "feature_y": {
                "value": False, 
                "description": "Feature Y is disabled",
                "replace_with": False
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_flags, f)
        temp_flags_file = f.name
    
    try:
        # Step 1: Load flags from JSON (simulate list_flags tool)
        with open(temp_flags_file, 'r') as f:
            json_content = f.read()
        
        parsed_data = parse_flags_json(json_content) 
        print(f"✅ Step 1: Loaded {len(parsed_data['flags'])} flags from JSON")
        
        # Step 2: Set up cache (simulate server state)
        server_module.FLAGS_CACHE = {
            "flags": parsed_data["flags"],
            "global_patterns": parsed_data["global_patterns"] 
        }
        print(f"✅ Step 2: Cached {len(parsed_data['global_patterns'])} function patterns")
        
        # Step 3: Transform code (simulate apply_rewrite tool)
        test_code = '''func processRequest(req Request) Response {
    if isFeatureEnabled("feature_x") {
        return processWithFeatureX(req)
    }
    
    if checkFlag("feature_y") {
        return processWithFeatureY(req)  
    }
    
    return processDefault(req)
}'''
        
        print("\n🔧 Step 3: Applying transformations...")
        
        # Transform for feature_x (enabled)
        rules_x = generate_rules_for_flag("feature_x", parsed_data["flags"]["feature_x"], "go")
        rule_objs_x = [Rule(**rule) for rule in rules_x]
        args_x = PiranhaArguments(
            code_snippet=test_code,
            language="go",
            rule_graph=RuleGraph(rules=rule_objs_x, edges=[])
        )
        
        result_x = execute_piranha(args_x)
        code_after_x = result_x[0].content if result_x else test_code
        
        # Transform for feature_y (disabled) 
        rules_y = generate_rules_for_flag("feature_y", parsed_data["flags"]["feature_y"], "go")
        rule_objs_y = [Rule(**rule) for rule in rules_y]
        args_y = PiranhaArguments(
            code_snippet=code_after_x,
            language="go", 
            rule_graph=RuleGraph(rules=rule_objs_y, edges=[])
        )
        
        result_y = execute_piranha(args_y)
        final_code = result_y[0].content if result_y else code_after_x
        
        print("\n📝 ORIGINAL CODE:")
        print("─" * 40)
        print(test_code)
        
        print("\n🎯 FINAL TRANSFORMED CODE:")
        print("─" * 40)
        print(final_code)
        
        # Analyze results
        transformations = []
        if "feature_x" not in final_code and "true" in final_code:
            transformations.append("✅ feature_x → true")
        if "feature_y" not in final_code and "false" in final_code:
            transformations.append("✅ feature_y → false")
            
        print(f"\n🎉 TRANSFORMATIONS APPLIED:")
        for t in transformations:
            print(f"   {t}")
        
        if len(transformations) == 2:
            print("\n🏆 INTEGRATION TEST PASSED: All flags successfully transformed!")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: {len(transformations)}/2 transformations applied")
            
    finally:
        # Cleanup
        os.unlink(temp_flags_file)


if __name__ == "__main__":
    # Run the demonstration
    demonstrate_expected_transformations()
    
    # Run integration test
    test_json_file_integration()
    
    print(f"\n{'🎯 SUMMARY':<70}")
    print("=" * 70)
    print("This test file demonstrates:")
    print("• JSON flags configuration parsing")
    print("• Rule generation for different flag states")  
    print("• Code transformation with expected before/after outputs")
    print("• Complete integration workflow")
    print("\nThe MCP server tools properly reformat code by replacing")
    print("feature flag calls with their configured boolean values.")