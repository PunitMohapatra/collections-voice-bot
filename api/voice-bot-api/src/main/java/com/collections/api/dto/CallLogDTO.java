package com.collections.api.dto;

import com.collections.entity.CallLog;

import java.time.LocalDateTime;

/**
 * CallLogDTO - Response body for call log endpoints.
 * 
 * Maps from CallLog entity to a clean API response.
 */
public class CallLogDTO {

    private Long callId;
    private Long accountId;
    private Long followupId;
    private LocalDateTime callStartTime;
    private LocalDateTime callEndTime;
    private String callStatus;
    private String languageUsed;
    private Boolean ptpCaptured;
    private Boolean escalated;

    /**
     * Factory method to create DTO from entity.
     */
    public static CallLogDTO fromEntity(CallLog entity) {
        CallLogDTO dto = new CallLogDTO();
        dto.callId = entity.getCallId();
        dto.accountId = entity.getAccountId();
        dto.followupId = entity.getFollowupId();
        dto.callStartTime = entity.getCallStartTime();
        dto.callEndTime = entity.getCallEndTime();
        dto.callStatus = entity.getCallStatus();
        dto.languageUsed = entity.getLanguageUsed();
        dto.ptpCaptured = entity.getPtpCaptured();
        dto.escalated = entity.getEscalated();
        return dto;
    }

    // ============================================================================
    // Getters and Setters
    // ============================================================================

    public Long getCallId() {
        return callId;
    }

    public void setCallId(Long callId) {
        this.callId = callId;
    }

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
