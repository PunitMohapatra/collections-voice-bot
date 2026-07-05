package com.collections.api.dto;

/**
 * FollowupRequest - Request body for POST /api/v1/followup endpoint
 * 
 * This class represents the data sent when creating a new followup record.
 * The voice bot sends this after each call to log the interaction.
 * 
 * Fields:
 *   accountId: Customer account ID (from database)
 *   remarks: Text notes from the call (captured by voice bot)
 */
public class FollowupRequest {

    private Long accountId;
    private String remarks;

    // ============================================================================
    // Getters and Setters
    // ============================================================================

    public Long getAccountId() {
        return accountId;
    }

    public void setAccountId(Long accountId) {
        this.accountId = accountId;
    }

    public String getRemarks() {
        return remarks;
    }

    public void setRemarks(String remarks) {
        this.remarks = remarks;
    }
}
