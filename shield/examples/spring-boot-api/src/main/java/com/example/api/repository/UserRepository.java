package com.example.api.repository;

import com.example.api.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface UserRepository extends JpaRepository<User, Long> {

    // VIOLATION: SELECT N+1 — calling getOrders() on each User triggers an extra query.
    // Should use a fetch join or @EntityGraph.
    List<User> findAll();

    // VIOLATION: Custom JPQL with no pagination on potentially huge result.
    @Query("SELECT u FROM User u WHERE u.email LIKE :pattern")
    List<User> findByEmailPattern(String pattern);
}
