package com.example.api.model;

import jakarta.persistence.*;
import java.util.List;

// VIOLATION: No explicit table name; relies on default lowercase-singular convention
// VIOLATION: No index on email despite frequent lookup
@Entity
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // VIOLATION: No @Column constraints — nullable=true, unique not enforced, length default
    private String email;
    private String passwordHash;

    // VIOLATION: Default LAZY would be safe, but EAGER on a 1-N relationship loads
    // every order whenever a User is fetched. N+1 risk.
    @OneToMany(mappedBy = "user", fetch = FetchType.EAGER)
    private List<Order> orders;

    public Long getId() { return id; }
    public String getEmail() { return email; }
    public String getPasswordHash() { return passwordHash; }
    public List<Order> getOrders() { return orders; }

    // VIOLATION: Returns the internal mutable List directly. Callers can mutate the
    // entity's state through the returned reference. Should return an unmodifiable view
    // or a defensive copy.
    public List<Order> getOrdersMutable() { return orders; }

    // VIOLATION: No equals/hashCode override on entity. Default Object identity breaks
    // HashSet semantics and Hibernate session-cache lookups in some cases.
    // (Already partially in database-review D10; jvm-language flags it as immutability/
    // value-equality concern.)
}
