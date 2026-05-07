package com.example.api.service;

import org.springframework.stereotype.Service;

@Service
public class OrderService {

    // VIOLATION: Throws and catches its own exception to control branching.
    // Exception-as-control-flow — should be a return value or a normal conditional.
    public boolean isValid(double amount) {
        try {
            if (amount <= 0) {
                throw new IllegalArgumentException("non-positive");
            }
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }

    // VIOLATION: Swallows exception silently — no log, no rethrow, no metric.
    // The caller has no visibility into a failure.
    public void chargeCustomer(Long customerId, double amount) {
        try {
            // simulate external call
            if (Math.random() < 0.1) {
                throw new RuntimeException("payment gateway unreachable");
            }
        } catch (Exception ignored) {
            // silently swallow
        }
    }
}
