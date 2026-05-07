package com.example.api.controller;

import com.example.api.service.UserService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.RequestBody;

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

    // VIOLATION: @RequestMapping with no method attribute — defaults to all methods.
    // Should be @PostMapping for clarity.
    // VIOLATION: Missing @Valid on @RequestBody — incoming payload not validated.
    @org.springframework.web.bind.annotation.RequestMapping("/v2/users")
    public Map<String, Object> createUserV2(@RequestBody Map<String, String> payload) {
        return Map.of("created", payload.getOrDefault("email", ""));
    }

    // VIOLATION: ResponseEntity not used where it should be — handler returns a Map but
    // the spec says return 201 Created with a Location header. Use ResponseEntity.
    // VIOLATION: @ResponseStatus on a method that also returns ResponseEntity-style map
    // (status comes from two sources, ambiguous).
    @org.springframework.web.bind.annotation.PostMapping("/v2/users/{id}/promote")
    @org.springframework.web.bind.annotation.ResponseStatus(HttpStatus.OK)
    public Map<String, Object> promote(@org.springframework.web.bind.annotation.PathVariable Long id) {
        return Map.of("promoted", id);
    }

    // VIOLATION: Mixed-case path segment — Spring is case-sensitive; inconsistent with
    // the kebab-case convention used elsewhere in this controller.
    @org.springframework.web.bind.annotation.GetMapping("/userProfile/{userId}")
    public Map<String, Object> getUserProfile(@org.springframework.web.bind.annotation.PathVariable Long userId) {
        return Map.of("userId", userId);
    }
}
