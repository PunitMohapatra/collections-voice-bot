package com.collections.api.dto;

import java.math.BigDecimal;

/**
 * PromiseRequest - Request body for POST /api/v1/promise endpoint
 * 
 * This class represents the data sent when creating a new Promise to Pay (PTP).
 * The voice bot sends this after validating the PTP with business rules.
 * 
 * Fields:
 *   accountId: Customer account ID (from database)
 *   followupId: Followup record ID (from current call)
 *   promiseAmount: Amount customer promised to pay
 *   promiseDate: Date customer promised to make payment
 */
public class PromiseRequest {

    private Long accountId;
    private Long followupId;
    private BigDecimal promiseAmount;
    private java.time.LocalDate promiseDate;

    // ============================================================================
    // Getters and Setters
    // ============================================================================

    public Long getAccountId() {
        return accountId;
    }

    public void setAccountId(Long accountId) {
        this.accountId = accountId;
    }

    public Long getFollowupId() {
        return followupId;
    }

    public void setFollowupId(Long followupId) {
        this.followupId = followupId;
    }

    public BigDecimal getPromiseAmount() {
        return promiseAmount;
    }

    public void setPromiseAmount(BigDecimal promiseAmount) {
        this.promiseAmount = promiseAmount;
    }

    public java.time.LocalDate getPromiseDate() {
        return promiseDate;
    }

    public void setPromiseDate(java.time.LocalDate promiseDate) {
        this.promiseDate = promiseDate;
    }
}
