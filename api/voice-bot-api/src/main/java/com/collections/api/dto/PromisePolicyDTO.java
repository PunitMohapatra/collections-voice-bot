package com.collections.api.dto;

import com.collections.entity.PromisePolicy;
import java.math.BigDecimal;

public class PromisePolicyDTO {
    private Long promisePolicyId;
    private Integer maxPromiseDays;
    private BigDecimal minPromisePercent;

    public static PromisePolicyDTO fromEntity(PromisePolicy policy) {
        PromisePolicyDTO dto = new PromisePolicyDTO();
        dto.promisePolicyId = policy.getPromisePolicyId();
        dto.maxPromiseDays = policy.getMaxPromiseDays();
        dto.minPromisePercent = policy.getMinPromisePercent();
        return dto;
    }

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
