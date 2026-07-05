package com.collections.api.controller;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Collections;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.collections.api.dto.PromiseRequest;
import com.collections.api.repository.AccountRepository;
import com.collections.api.repository.PromisePolicyRepository;
import com.collections.api.repository.PromiseRepository;
import com.collections.entity.Account;
import com.collections.entity.Promise;
import com.collections.entity.PromisePolicy;

/**
 * PromiseController - Handles Promise to Pay (PTP) creation with validation.
 * 
 * POST /api/v1/promise - Validates and saves a PTP record.
 * Validation rules:
 *   1. promiseDate must not exceed LocalDate.now().plusDays(maxPromiseDays)
 *   2. promiseAmount must be >= overdueAmount * (minPromisePercent / 100)
 * Returns 400 with error message if validation fails.
 * Returns 200 with saved promise if valid.
 */
@RestController
@RequestMapping("/api/v1")
public class PromiseController {

    @Autowired
    private AccountRepository accountRepository;

    @Autowired
    private PromiseRepository promiseRepository;

    @Autowired
    private PromisePolicyRepository promisePolicyRepository;

    @PostMapping("/promise")
    public ResponseEntity<?> savePromise(@RequestBody PromiseRequest promiseRequest) {
        // Validate required fields
        if (promiseRequest.getAccountId() == null || promiseRequest.getPromiseDate() == null || promiseRequest.getPromiseAmount() == null) {
            return ResponseEntity.badRequest()
                .body(Collections.singletonMap("error", "accountId, promiseAmount and promiseDate are required"));
        }

        // Fetch account to get overdue amount for minimum calculation
        Account account = accountRepository.findById(promiseRequest.getAccountId())
            .orElseThrow(() -> new RuntimeException("Account not found"));

        // Fetch promise policy for business rules
        PromisePolicy policy = promisePolicyRepository.findTopBy()
            .orElseThrow(() -> new RuntimeException("Promise policy not found"));

        // Validation 1: Date must be within maxPromiseDays from today
        if (promiseRequest.getPromiseDate().isAfter(java.time.LocalDate.now().plusDays(policy.getMaxPromiseDays()))) {
            return ResponseEntity.badRequest()
                .body(Collections.singletonMap("error", "Promise date must be within " + policy.getMaxPromiseDays() + " days from today"));
        }

        // Validation 2: Amount must be >= overdueAmount * (minPromisePercent / 100)
        BigDecimal overdueAmount = account.getOverdueAmount() == null ? BigDecimal.ZERO : account.getOverdueAmount();
        BigDecimal minAmount = overdueAmount.multiply(policy.getMinPromisePercent().divide(BigDecimal.valueOf(100)))
            .setScale(2, RoundingMode.HALF_UP);

        if (promiseRequest.getPromiseAmount().compareTo(minAmount) < 0) {
            return ResponseEntity.badRequest()
                .body(Collections.singletonMap("error", "Promise amount must be at least " + minAmount + " rupees (minimum " + policy.getMinPromisePercent() + "% of overdue)"));
        }

        // Save the promise
        Promise promise = new Promise();
        promise.setAccountId(promiseRequest.getAccountId());
        promise.setFollowupId(promiseRequest.getFollowupId());
        promise.setPromiseAmount(promiseRequest.getPromiseAmount());
        promise.setPromiseDate(promiseRequest.getPromiseDate());

        Promise savedPromise = promiseRepository.save(promise);

        return ResponseEntity.ok(savedPromise);
    }
}
