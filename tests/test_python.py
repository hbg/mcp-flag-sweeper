import os
from typing import Dict, Any

class FeatureFlagManager:
    def __init__(self):
        self.flags = {
            "new_checkout_flow": False,
            "beta_ui": False,
            "feature_flag": False
        }

    def is_feature_enabled(self, flag: str) -> bool:
        """Check if a feature flag is enabled"""
        return os.getenv(f"FEATURE_{flag.upper()}", "false").lower() == "true"

    def set_flag(self, flag: str, enabled: bool):
        """Set a feature flag value"""
        self.flags[flag] = enabled

def main():
    flag_manager = FeatureFlagManager()

    # Feature flag checks
    if flag_manager.is_feature_enabled("new_checkout_flow"):
        print("Using new checkout flow")
        process_new_checkout()
    else:
        print("Using legacy checkout flow")
        process_legacy_checkout()

    if flag_manager.is_feature_enabled("beta_ui"):
        print("Rendering beta UI")
        render_beta_ui()
    else:
        print("Rendering standard UI")
        render_standard_ui()

    # Complex nested logic
    if flag_manager.is_feature_enabled("feature_flag"):
        if flag_manager.is_feature_enabled("new_checkout_flow"):
            print("Both flags enabled - special case")
            handle_special_case()
        else:
            print("Only feature flag enabled")
            handle_feature_flag_only()

    # Feature flag in error handling
    try:
        process_payment()
    except Exception as e:
        if flag_manager.is_feature_enabled("new_checkout_flow"):
            print(f"New checkout error: {e}")
        else:
            print(f"Legacy checkout error: {e}")

def process_new_checkout():
    print("Processing payment with new checkout flow...")

def process_legacy_checkout():
    print("Processing payment with legacy checkout flow...")

def render_beta_ui():
    print("Rendering modern beta interface...")

def render_standard_ui():
    print("Rendering standard interface...")

def handle_special_case():
    print("Handling special case with both flags...")

def handle_feature_flag_only():
    print("Handling feature flag only case...")

def process_payment():
    # Simulate payment processing
    pass

if __name__ == "__main__":
    main()

