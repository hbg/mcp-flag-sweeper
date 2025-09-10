public class FeatureFlagExample {

    private static final String NEW_CHECKOUT_FLOW = "new_checkout_flow";
    private static final String BETA_UI = "beta_ui";
    private static final String FEATURE_FLAG = "feature_flag";

    public static void main(String[] args) {
        FeatureFlagExample example = new FeatureFlagExample();
        example.runExample();
    }

    public void runExample() {
        // Feature flag checks
        if (isFeatureEnabled(NEW_CHECKOUT_FLOW)) {
            System.out.println("Using new checkout flow");
            processNewCheckout();
        } else {
            System.out.println("Using legacy checkout flow");
            processLegacyCheckout();
        }

        if (isFeatureEnabled(BETA_UI)) {
            System.out.println("Rendering beta UI");
            renderBetaUI();
        } else {
            System.out.println("Rendering standard UI");
            renderStandardUI();
        }

        // Complex nested logic
        if (isFeatureEnabled(FEATURE_FLAG)) {
            if (isFeatureEnabled(NEW_CHECKOUT_FLOW)) {
                System.out.println("Both flags enabled - special case");
                handleSpecialCase();
            } else {
                System.out.println("Only feature flag enabled");
                handleFeatureFlagOnly();
            }
        }

        // Feature flag in exception handling
        try {
            processPayment();
        } catch (Exception e) {
            if (isFeatureEnabled(NEW_CHECKOUT_FLOW)) {
                System.err.println("New checkout error: " + e.getMessage());
            } else {
                System.err.println("Legacy checkout error: " + e.getMessage());
            }
        }
    }

    private boolean isFeatureEnabled(String flag) {
        // Simulate feature flag check
        return "true".equals(System.getProperty("feature." + flag));
    }

    private void processNewCheckout() {
        System.out.println("Processing payment with new checkout flow...");
    }

    private void processLegacyCheckout() {
        System.out.println("Processing payment with legacy checkout flow...");
    }

    private void renderBetaUI() {
        System.out.println("Rendering modern beta interface...");
    }

    private void renderStandardUI() {
        System.out.println("Rendering standard interface...");
    }

    private void handleSpecialCase() {
        System.out.println("Handling special case with both flags...");
    }

    private void handleFeatureFlagOnly() {
        System.out.println("Handling feature flag only case...");
    }

    private void processPayment() throws Exception {
        // Simulate payment processing
    }
}

