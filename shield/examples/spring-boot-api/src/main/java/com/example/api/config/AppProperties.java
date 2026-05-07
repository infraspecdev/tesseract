package com.example.api.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

// VIOLATION: @Component + @ConfigurationProperties without prefix attribute. Properties
// won't bind correctly. Should use @ConfigurationProperties(prefix = "app").
// VIOLATION: Missing @Validated — invalid config (negative timeouts, empty URLs) won't
// fail at startup; will surface as runtime failures.
@Component
@ConfigurationProperties
public class AppProperties {

    // VIOLATION: Mutable field with public setter. @ConfigurationProperties beans should
    // be immutable (records or constructor binding via @ConfigurationPropertiesScan).
    private String apiUrl;
    private int timeoutSeconds;

    public String getApiUrl() { return apiUrl; }
    public void setApiUrl(String apiUrl) { this.apiUrl = apiUrl; }
    public int getTimeoutSeconds() { return timeoutSeconds; }
    public void setTimeoutSeconds(int timeoutSeconds) { this.timeoutSeconds = timeoutSeconds; }
}
