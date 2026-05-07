package com.example.api.controller;

import com.example.api.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

// VIOLATION: No versioning prefix. URI exposes verbs, not resources.
@RestController
@RequestMapping("/api")
public class UserController {

    @Autowired
    private UserService userService;

    // VIOLATION: GET used for a state-changing operation. Should be POST.
    @GetMapping("/createUser")
    public Map<String, Object> createUser(@RequestParam String email,
                                          @RequestParam String password,
                                          @RequestParam String name) {
        return userService.registerUser(email, password, name, 0.0);
    }

    // VIOLATION: Verb in URI ("getAll"). Should be GET /users with pagination.
    // VIOLATION: No pagination — returns full collection.
    @GetMapping("/getAllUsers")
    public List<Map<String, Object>> getAllUsers() {
        return userService.findUsers(null, null);
    }

    // VIOLATION: Returns 200 OK on a missing resource (should be 404).
    // VIOLATION: Inconsistent error shape — returns Map<String,String> on error,
    // Map<String,Object> on success.
    @GetMapping("/user/{id}")
    public Object getUser(@PathVariable Long id) {
        // simulating a not-found
        if (id < 0) return Map.of("error", "not found");
        return Map.of("id", id, "email", "stub@example.com");
    }

    // VIOLATION: Non-idempotent PUT. PUT must be idempotent; this appends.
    @PutMapping("/user/{id}/append-tag")
    public Map<String, Object> appendTag(@PathVariable Long id, @RequestParam String tag) {
        // appends each call — running twice gives different state
        return Map.of("id", id, "appended", tag);
    }

    // VIOLATION: DELETE returns the deleted resource body (200) instead of 204 No Content.
    @DeleteMapping("/user/{id}")
    public Map<String, Object> deleteUser(@PathVariable Long id) {
        return Map.of("deleted", id, "email", "stub@example.com");
    }
}
