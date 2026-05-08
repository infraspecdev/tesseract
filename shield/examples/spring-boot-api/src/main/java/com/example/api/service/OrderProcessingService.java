package com.example.api.service;

import com.example.api.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderProcessingService {

    private final UserRepository userRepository;

    public OrderProcessingService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    // VIOLATION: @Transactional on private method — Spring proxies are class-level;
    // private methods are NOT transactional.
    @Transactional
    private void persistOrder(Long userId) {
        userRepository.findById(userId);
    }

    // VIOLATION: Self-invocation problem — calling `persistOrder` from within the same
    // class bypasses the proxy, so @Transactional doesn't apply. Call from a separate
    // bean OR refactor.
    public void processOrder(Long userId) {
        persistOrder(userId);
    }

    // VIOLATION: Read method without `readOnly = true`. Skips JPA flush optimization
    // and signals intent incorrectly to other developers.
    @Transactional
    public Long countOrders(Long userId) {
        return userRepository.findById(userId).map(u -> 1L).orElse(0L);
    }

    // VIOLATION: REQUIRES_NEW propagation without explicit reason. Forks a new tx for
    // every call; almost always a mistake unless documenting why (e.g., "must commit
    // even if outer tx fails").
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordAuditEntry(Long userId, String action) {
        userRepository.findById(userId);
    }
}
