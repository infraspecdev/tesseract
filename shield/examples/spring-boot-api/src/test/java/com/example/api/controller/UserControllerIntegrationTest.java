package com.example.api.controller;

import com.example.api.repository.UserRepository;
import com.example.api.service.UserService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

// VIOLATION: Full @SpringBootTest for a controller-only test. @WebMvcTest(UserController.class)
// would load only the web layer — much faster, focused.
// VIOLATION: @DirtiesContext per-method causes context recreation between tests; very slow.
// Use only when state mutation requires it AND no test-isolation alternative exists.
@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.BEFORE_EACH_TEST_METHOD)
class UserControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    // VIOLATION: @MockBean on a class that the controller doesn't directly call.
    // The test mocks the entire layer instead of using the slice's auto-config.
    @MockBean
    private UserService userService;

    @MockBean
    private UserRepository userRepository;

    // VIOLATION: Test relies on H2 schema state from prior tests (no @BeforeEach reset,
    // no @Sql to seed). Order-dependent.
    @Test
    void getUser_returns200() throws Exception {
        mockMvc.perform(get("/api/user/1"));
        // No assertions chained on the result — test passes regardless.
    }
}
