package com.example.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class AppConfig {

    // VIOLATION: In-memory cache held in a singleton bean.
    // Multi-instance deployments diverge — instance A caches X, instance B does not.
    // Should use a distributed cache (Redis, etc.) or scope explicitly per-instance.
    @Bean
    public Map<String, Object> sharedCache() {
        return new HashMap<>();
    }

    // VIOLATION: Feature is launched fully on/off via this static toggle.
    // No feature flag, no gradual rollout, no kill switch.
    // Risky changes should be behind a runtime flag.
    public static final boolean NEW_PRICING_ENABLED = true;

    // VIOLATION: @Value for a typed config value. Should be in @ConfigurationProperties
    // for type safety, default handling, and validation.
    @org.springframework.beans.factory.annotation.Value("${app.timeout-seconds:30}")
    private int timeoutSeconds;
}
