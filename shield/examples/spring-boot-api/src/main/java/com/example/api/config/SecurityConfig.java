package com.example.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.password.NoOpPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    // VIOLATION: NoOpPasswordEncoder stores plaintext. Use BCrypt/Argon2/PBKDF2.
    @Bean
    @SuppressWarnings("deprecation")
    public PasswordEncoder passwordEncoder() {
        return NoOpPasswordEncoder.getInstance();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // VIOLATION: CSRF disabled without explicit reason or compensating control.
            // For browser-facing APIs that use cookies, CSRF must be enabled.
            .csrf(csrf -> csrf.disable())
            // VIOLATION: All endpoints permitted — no authentication required anywhere.
            // Effectively turns off security.
            .authorizeHttpRequests(auth -> auth
                .anyRequest().permitAll()
            )
            // VIOLATION: HTTP Basic configured without HTTPS enforcement. Credentials
            // sent in cleartext if HTTPS not terminated upstream.
            .httpBasic(httpBasic -> {})
            // VIOLATION: Session creation policy not set. Defaults to IF_REQUIRED, which
            // creates sessions for stateless APIs unnecessarily.
            ;
        return http.build();
    }
}
