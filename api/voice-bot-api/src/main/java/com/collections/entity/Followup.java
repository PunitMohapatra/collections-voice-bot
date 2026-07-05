package com.collections.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "followup")
public class Followup {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "\"followupId\"")
    private Long followupId;

    @Column(name = "\"accountId\"", nullable = false)
    private Long accountId;

    @Column(name = "\"remarks\"", length = 1000)
    private String remarks;

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

    public String getRemarks() {
        return remarks;
    }

    public void setRemarks(String remarks) {
        this.remarks = remarks;
    }
}
