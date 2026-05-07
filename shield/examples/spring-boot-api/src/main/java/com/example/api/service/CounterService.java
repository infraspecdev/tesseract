package com.example.api.service;

import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@Service
public class CounterService {

    // VIOLATION: Shared mutable state in a singleton bean accessed without synchronization.
    // Multiple request threads race on these reads/writes.
    private final Map<String, Integer> counters = new HashMap<>();
    private int totalRequests = 0;

    // VIOLATION: Read-modify-write race on totalRequests.
    public int increment(String key) {
        totalRequests++;
        Integer cur = counters.get(key);
        if (cur == null) cur = 0;
        counters.put(key, cur + 1);
        return cur + 1;
    }

    // VIOLATION: Fire-and-forget — exceptions are silently dropped.
    // No tracking of failure, no metric, no retry policy.
    public void chargeAsync(Long userId, double amount) {
        CompletableFuture.runAsync(() -> {
            if (Math.random() < 0.1) {
                throw new RuntimeException("payment failed");
            }
            // success path; result discarded
        });
    }

    // VIOLATION: Retried operation is not idempotent — appends a row each retry.
    // If caller retries on transient failure, side effects multiply.
    public void recordEvent(String key, String event) {
        counters.merge(key + ":" + event, 1, Integer::sum);
    }
}
