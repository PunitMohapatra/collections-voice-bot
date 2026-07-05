package com.collections.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(name = "promise")
public class Promise {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "\"promiseId\"")
    private Long promiseId;

    @Column(name = "\"followupId\"")
    private Long followupId;

    @Column(name = "\"accountId\"")
    private Long accountId;

    @Column(name = "\"promiseAmount\"", nullable = false, precision = 15, scale = 2)
    private BigDecimal promiseAmount;

    @Column(name = "\"promiseDate\"", nullable = false)
    private LocalDate promiseDate;

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

    public LocalDate getPromiseDate() {
        return promiseDate;
    }

    public void setPromiseDate(LocalDate promiseDate) {
        this.promiseDate = promiseDate;
    }
}
