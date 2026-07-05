package com.collections.api.dto;

import java.math.BigDecimal;

/**
 * PromiseDTO - Data Transfer Object for promise data returned by API
 * 
 * This class represents the structure of a saved promise returned by
 * POST /api/v1/promise endpoint.
 * 
 * Fields:
 *   promiseId: Primary key (auto-generated)
 *   followupId: Followup record ID
 *   accountId: Customer account ID
 *   promiseAmount: Amount customer promised to pay
 *   promiseDate: Date customer promised to make payment
 */
public class PromiseDTO {

    private Long promiseId;
    private Long followupId;
    private Long accountId;
    private BigDecimal promiseAmount;
    private java.time.LocalDate promiseDate;

    // ============================================================================
    // Getters and Setters
    // ============================================================================

    public Long getPromiseId() {
        return promiseId;
    }

    public void setPromiseId(Long promiseId) {
        this.promiseId = promiseId;
    }

    public Long getFollowupId() {
        return followupId;
    }

    public void setFollowupId(Long followupId) {
        this.followupId = followupId;
    }

    public Long getAccountId() {
        return accountId;
    }

    public void setAccountId(Long accountId) {
        this.accountId = accountId;
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
