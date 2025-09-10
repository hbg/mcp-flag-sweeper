#!/usr/bin/env python3
"""
Multilayered test case with many different feature flags referenced in various ways.
This test demonstrates the flexibility of the MCP Piranha server.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server import parse_flags_md, generate_rules_for_flag
from polyglot_piranha import execute_piranha, PiranhaArguments, Rule, RuleGraph, OutgoingEdges

def test_multilayered_scenario():
    """Test a complex scenario with multiple flags and function patterns."""

    # Create a comprehensive flags.md content
    flags_content = """# Feature Flags

## Functions
isFeatureEnabled,client.GetString,isEnabled,getFlag,is_feature_enabled,get_flag,flag_manager.is_feature_enabled,config.getBoolean,settings.isEnabled,feature.isOn,checkFlag,hasFeature

## Flags
beta_ui:true:Enables the new beta user interface:true
new_checkout:false:New payment processing flow:false
debug_mode:true:Enables debug logging:true
legacy_auth:false:Legacy authentication system:false
premium_features:true:Premium user features:true
analytics_tracking:false:User analytics tracking:false
dark_mode:true:Dark theme support:true
mobile_optimized:false:Mobile-specific optimizations:false
"""

    # Parse the flags
    parsed_data = parse_flags_md(flags_content)
    flags = parsed_data['flags']
    global_patterns = parsed_data['global_patterns']

    print(f"✅ Loaded {len(flags)} flags and {len(global_patterns)} patterns")

    # Set up the cache
    import src.server
    src.server.FLAGS_CACHE = {
        'flags': flags,
        'global_patterns': global_patterns
    }

    # Complex multilayered test code
    test_code = '''
package main

import (
    "fmt"
    "log"
    "net/http"
)

func main() {
    // Multiple flag checks in different contexts
    if isFeatureEnabled("beta_ui") {
        fmt.Println("Rendering beta UI")
        renderBetaInterface()
    } else {
        fmt.Println("Rendering standard UI")
        renderStandardInterface()
    }

    // Nested conditions
    if client.GetString("debug_mode") == "true" {
        log.SetLevel(log.DebugLevel)
        if isEnabled("analytics_tracking") {
            enableAnalytics()
        }
    }

    // Function calls with multiple parameters
    if getFlag("premium_features", "user123") {
        enablePremiumFeatures()
    }

    // Different function patterns
    if flag_manager.is_feature_enabled("dark_mode") {
        applyDarkTheme()
    }

    if config.getBoolean("mobile_optimized", false) {
        optimizeForMobile()
    }

    // Complex conditional logic
    if settings.isEnabled("legacy_auth") {
        useLegacyAuth()
    } else if feature.isOn("new_checkout") {
        useNewCheckout()
    } else {
        useDefaultFlow()
    }

    // Method chaining and complex expressions
    if checkFlag("beta_ui") && hasFeature("premium_features") {
        enableBetaPremiumMode()
    }

    // Multiple flags in one condition
    if isFeatureEnabled("beta_ui") || isFeatureEnabled("dark_mode") {
        applyModernStyling()
    }
}

func renderBetaInterface() {
    fmt.Println("Beta interface rendered")
}

func renderStandardInterface() {
    fmt.Println("Standard interface rendered")
}

func enableAnalytics() {
    fmt.Println("Analytics enabled")
}

func enablePremiumFeatures() {
    fmt.Println("Premium features enabled")
}

func applyDarkTheme() {
    fmt.Println("Dark theme applied")
}

func optimizeForMobile() {
    fmt.Println("Mobile optimization applied")
}

func useLegacyAuth() {
    fmt.Println("Using legacy authentication")
}

func useNewCheckout() {
    fmt.Println("Using new checkout flow")
}

func useDefaultFlow() {
    fmt.Println("Using default flow")
}

func enableBetaPremiumMode() {
    fmt.Println("Beta premium mode enabled")
}

func applyModernStyling() {
    fmt.Println("Modern styling applied")
}
'''

    print("\n🧪 Testing multilayered scenario...")
    print("=" * 50)

    # Test each flag individually
    test_flags = ['beta_ui', 'new_checkout', 'debug_mode', 'legacy_auth', 'premium_features', 'analytics_tracking', 'dark_mode', 'mobile_optimized']

    for flag_name in test_flags:
        if flag_name in flags:
            print(f"\n🔧 Testing flag: {flag_name}")
            flag_info = flags[flag_name]
            rules = generate_rules_for_flag(flag_name, flag_info, 'go')

            print(f"   Generated {len(rules)} rules")

            try:
                rule_objs = []
                for r in rules:
                    rule_objs.append(Rule(**r))

                args = PiranhaArguments(
                    code_snippet=test_code,
                    language='go',
                    rule_graph=RuleGraph(rules=rule_objs, edges=[]),
                )

                summaries = execute_piranha(args)
                if summaries and len(summaries) > 0:
                    print(f"   ✅ SUCCESS! Transformed code for {flag_name}")
                    # Show a snippet of the transformation
                    lines = summaries[0].content.split('\n')
                    for i, line in enumerate(lines):
                        if f'"{flag_name}"' in line:
                            print(f"   Before: {line.strip()}")
                            if i < len(lines) - 1:
                                print(f"   After:  {lines[i+1].strip()}")
                            break
                else:
                    print(f"   ❌ No transformations applied for {flag_name}")

            except Exception as e:
                print(f"   ❌ Error transforming {flag_name}: {str(e)}")

    print("\n" + "=" * 50)
    print("🎉 Multilayered test completed!")

if __name__ == "__main__":
    test_multilayered_scenario()
