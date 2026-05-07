package com.example.api;

import com.example.api.service.UserService;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

// VIOLATION: @SpringBootTest pulls full context for every unit test — slow, broad scope.
// Should be a plain unit test (no Spring) or a focused @DataJpaTest / @WebMvcTest slice.
@SpringBootTest
class UserServiceTest {

    // VIOLATION: Mocking the class under test instead of its collaborators.
    // The mock returns a stubbed value, so the test asserts the stub, not the implementation.
    @Test
    void registerUser_returnsUser() {
        UserService mockedService = Mockito.mock(UserService.class);
        Map<String, Object> stub = new HashMap<>();
        stub.put("id", 1L);
        Mockito.when(mockedService.registerUser("a@b.c", "password123", "n", 0.0)).thenReturn(stub);

        Map<String, Object> result = mockedService.registerUser("a@b.c", "password123", "n", 0.0);

        assertEquals(1L, result.get("id"));
    }

    // VIOLATION: Sleep-based timing, flaky.
    @Test
    void waitsAndPasses() throws InterruptedException {
        long start = System.currentTimeMillis();
        Thread.sleep(100);
        long elapsed = System.currentTimeMillis() - start;
        assertTrue(elapsed >= 100); // flakes under load
    }

    // VIOLATION: Test relies on shared mutable state from a prior test run order.
    private static int counter = 0;
    @Test
    void incrementCounter() {
        counter++;
        assertEquals(1, counter); // breaks if any test increments first
    }

    // VIOLATION: Test asserts implementation, not behavior — checks a private map size
    // via reflection-style poke. Behavior assertion (the public contract) would be
    // "registering a user makes them findable".
    @Test
    void implementationDetail_internalMapGrows() {
        UserService svc = new UserService();
        svc.registerUser("a@b.c", "password123", "n", 0.0);
        // hypothetical reflective access — illustration only
        assertNotNull(svc); // weak/no-op assertion
    }

    // VIOLATION: No assertions — passes regardless of behavior.
    @Test
    void noAssertions() {
        UserService svc = new UserService();
        svc.registerUser("a@b.c", "password123", "n", 0.0);
    }
}
