package com.example.api.exception;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class GlobalExceptionHandler {

    // VIOLATION: Catch-all that maps every Throwable to 500. Hides 4xx-shaped client
    // errors as 5xx server errors, breaks alerting and client-side handling.
    @ExceptionHandler(Throwable.class)
    public ResponseEntity<String> handleAll(Throwable t) {
        // VIOLATION: Logging via println — no level, no structure, no MDC/correlation ID.
        System.out.println("error: " + t.getMessage());
        // VIOLATION: Returns the raw exception message to clients — leaks internals.
        return ResponseEntity.status(500).body(t.getMessage());
    }
}
