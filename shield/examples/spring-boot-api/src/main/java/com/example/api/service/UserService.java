package com.example.api.service;

import org.springframework.stereotype.Service;
import java.util.*;

// VIOLATION: God class — service handles users, orders, emails, payments, audit logs.
// Should be split into UserService, OrderService, NotificationService, PaymentService,
// AuditService. Each method below couples user logic to unrelated concerns.
@Service
public class UserService {

    private final Map<Long, Map<String, Object>> users = new HashMap<>();
    private final Map<Long, List<Map<String, Object>>> orders = new HashMap<>();

    // VIOLATION: Method does five things — validate, persist, send email, log audit, charge fee.
    // Single Responsibility violation. Should delegate to focused collaborators.
    public Map<String, Object> registerUser(String email, String password, String name, double signupFee) {
        if (email == null || !email.contains("@")) throw new RuntimeException("bad email");
        if (password == null || password.length() < 8) throw new RuntimeException("weak password");
        Long id = (long) (users.size() + 1);
        Map<String, Object> u = new HashMap<>();
        u.put("id", id);
        u.put("email", email);
        u.put("password", password); // plaintext — flagged elsewhere too
        u.put("name", name);
        users.put(id, u);
        // sends email (should be a NotificationService)
        System.out.println("Sending welcome email to " + email);
        // charges fee (should be a PaymentService)
        System.out.println("Charging $" + signupFee + " to " + email);
        // writes audit log (should be an AuditService)
        System.out.println("AUDIT: user " + id + " created");
        return u;
    }

    // VIOLATION: Copy-paste of registerUser logic with minor variation. DRY violation.
    public Map<String, Object> registerAdmin(String email, String password, String name, double signupFee) {
        if (email == null || !email.contains("@")) throw new RuntimeException("bad email");
        if (password == null || password.length() < 8) throw new RuntimeException("weak password");
        Long id = (long) (users.size() + 1);
        Map<String, Object> u = new HashMap<>();
        u.put("id", id);
        u.put("email", email);
        u.put("password", password);
        u.put("name", name);
        u.put("role", "ADMIN");
        users.put(id, u);
        System.out.println("Sending welcome email to " + email);
        System.out.println("Charging $" + signupFee + " to " + email);
        System.out.println("AUDIT: admin " + id + " created");
        return u;
    }

    // VIOLATION: Speculative generality / YAGNI — accepts a "strategy" param and a
    // "transformOptions" map that no caller uses. Premature flexibility.
    public List<Map<String, Object>> findUsers(String strategy, Map<String, Object> transformOptions) {
        return new ArrayList<>(users.values());
    }

    // VIOLATION: Deep nesting (5 levels), poor naming (`x`, `tmp`, `do2`), no early returns.
    public boolean doStuff(Long id, String x, boolean tmp, int do2) {
        if (id != null) {
            if (users.containsKey(id)) {
                Map<String, Object> u = users.get(id);
                if (u != null) {
                    if (x != null && !x.isEmpty()) {
                        if (tmp) {
                            u.put("flag", do2);
                            return true;
                        }
                    }
                }
            }
        }
        return false;
    }
}
