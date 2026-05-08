package com.example.api.model;

import jakarta.persistence.*;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id")
    private User user;

    private double amount;

    public Long getId() { return id; }
    public User getUser() { return user; }
    public double getAmount() { return amount; }

    // VIOLATION: Public mutable setter on entity field — entity is mutable across the
    // codebase. Prefer constructor + Hibernate-managed state changes via methods that
    // express intent (e.g., `applyDiscount(...)`).
    public void setAmount(double amount) { this.amount = amount; }
}
