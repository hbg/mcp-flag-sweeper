package main

import (
	"fmt"
	"log"
	"os"
)

// Feature flags
const (
	NewCheckoutFlow = "new_checkout_flow"
	BetaUI         = "beta_ui"
	FeatureFlag    = "feature_flag"
)

func main() {
	// Simulate feature flag checks
	if isFeatureEnabled(NewCheckoutFlow) {
		fmt.Println("Using new checkout flow")
		processNewCheckout()
	} else {
		fmt.Println("Using legacy checkout flow")
		processLegacyCheckout()
	}

	if isFeatureEnabled(BetaUI) {
		fmt.Println("Rendering beta UI")
		renderBetaUI()
	} else {
		fmt.Println("Rendering standard UI")
		renderStandardUI()
	}

	// Nested feature flag logic
	if isFeatureEnabled(FeatureFlag) {
		if isFeatureEnabled(NewCheckoutFlow) {
			fmt.Println("Both flags enabled - special case")
		} else {
			fmt.Println("Only feature flag enabled")
		}
	}

	// Feature flag in error handling
	if err := processPayment(); err != nil {
		if isFeatureEnabled(NewCheckoutFlow) {
			log.Printf("New checkout error: %v", err)
		} else {
			log.Printf("Legacy checkout error: %v", err)
		}
	}
}

func isFeatureEnabled(flag string) bool {
	// Simulate feature flag check
	return os.Getenv("FEATURE_"+flag) == "true"
}

func processNewCheckout() {
	fmt.Println("Processing payment with new checkout flow...")
}

func processLegacyCheckout() {
	fmt.Println("Processing payment with legacy checkout flow...")
}

func renderBetaUI() {
	fmt.Println("Rendering modern beta interface...")
}

func renderStandardUI() {
	fmt.Println("Rendering standard interface...")
}

func processPayment() error {
	// Simulate payment processing
	return nil
}

