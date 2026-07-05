package com.collections.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "promise_policy")
public class PromisePolicy {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "\"promisePolicyId\"")
    private Long promisePolicyId;

    @Column(name = "\"maxPromiseDays\"", nullable = false)
    private Integer maxPromiseDays = 30;

    @Column(name = "\"minPromisePercent\"", nullable = false, precision = 5, scale = 2)
    private BigDecimal minPromisePercent = BigDecimal.valueOf(25.00);

    public Long getPromisePolicyId() {
        return promisePolicyId;
    }

    public void setPromisePolicyId(Long promisePolicyId) {
        this.promisePolicyId = promisePolicyId;
    }

    public Integer getMaxPromiseDays() {
        return maxPromiseDays;
    }

    public void setMaxPromiseDays(Integer maxPromiseDays) {
        this.maxPromiseDays = maxPromiseDays;
    }

    public BigDecimal getMinPromisePercent() {
        return minPromisePercent;
    }

    public void setMinPromisePercent(BigDecimal minPromisePercent) {
        this.minPromisePercent = minPromisePercent;
    }
}
