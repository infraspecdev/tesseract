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

    // VIOLATION: Mutating JPQL query without @Modifying annotation. Spring will treat
    // it as a SELECT and the update will not execute. Must add @Modifying (and usually
    // @Transactional on the caller).
    @org.springframework.data.jpa.repository.Query("UPDATE User u SET u.email = :email WHERE u.id = :id")
    int updateEmail(@org.springframework.data.repository.query.Param("id") Long id,
                    @org.springframework.data.repository.query.Param("email") String email);
}
