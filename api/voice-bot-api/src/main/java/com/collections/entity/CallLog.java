package com.collections.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "call_log")
public class CallLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "\"callId\"")
    private Long callId;

    @Column(name = "\"accountId\"")
    private Long accountId;

    @Column(name = "\"followupId\"")
    private Long followupId;

    @Column(name = "\"callStartTime\"")
    private LocalDateTime callStartTime;

    @Column(name = "\"callEndTime\"")
    private LocalDateTime callEndTime;

    @Column(name = "\"callStatus\"", length = 30)
    private String callStatus;

    @Column(name = "\"languageUsed\"", length = 20)
    private String languageUsed;

    @Column(name = "\"ptpCaptured\"")
    private Boolean ptpCaptured = false;

    @Column(name = "\"escalated\"")
    private Boolean escalated = false;

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
