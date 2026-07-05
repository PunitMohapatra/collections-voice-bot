package com.collections.api.dto;

import java.time.LocalDateTime;

/**
 * CallLogRequest - Request body for POST /api/v1/call-log endpoint.
 * 
 * Sent by the FastAPI bot server to record call outcomes.
 * Fields mirror the call_log table columns.
 */
public class CallLogRequest {

    private Long accountId;
    private Long followupId;
    private LocalDateTime callStartTime;
    private LocalDateTime callEndTime;
    private String callStatus;
    private String languageUsed;
    private Boolean ptpCaptured;
    private Boolean escalated;

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

    public LocalDateTime getCallStartTime() {
        return callStartTime;
    }

    public void setCallStartTime(LocalDateTime callStartTime) {
        this.callStartTime = callStartTime;
    }

    public LocalDateTime getCallEndTime() {
        return callEndTime;
    }

    public void setCallEndTime(LocalDateTime callEndTime) {
        this.callEndTime = callEndTime;
    }

    public String getCallStatus() {
        return callStatus;
    }

    public void setCallStatus(String callStatus) {
        this.callStatus = callStatus;
    }

    public String getLanguageUsed() {
        return languageUsed;
    }

    public void setLanguageUsed(String languageUsed) {
        this.languageUsed = languageUsed;
    }

    public Boolean getPtpCaptured() {
        return ptpCaptured;
    }

    public void setPtpCaptured(Boolean ptpCaptured) {
        this.ptpCaptured = ptpCaptured;
    }

    public Boolean getEscalated() {
        return escalated;
    }

    public void setEscalated(Boolean escalated) {
        this.escalated = escalated;
    }
}
