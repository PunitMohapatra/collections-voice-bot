package com.collections.api.dto;

import com.collections.entity.Account;
import java.math.BigDecimal;
import java.time.LocalDate;

public class AccountDTO {
    private Long accountId;
    private String accountNumber;
    private String customerName;
    private BigDecimal loanAmount;
    private BigDecimal overdueAmount;
    private String preferredLanguage;
    private LocalDate lastEmiDate;
    private BigDecimal charges;
    private BigDecimal lastPaymentAmount;
    private LocalDate lastPaymentDate;

    public static AccountDTO fromEntity(Account account) {
        AccountDTO dto = new AccountDTO();
        dto.accountId = account.getAccountId();
        dto.accountNumber = account.getAccountNumber();
        dto.customerName = account.getCustomerName();
        dto.loanAmount = account.getLoanAmount();
        dto.overdueAmount = account.getOverdueAmount();
        dto.preferredLanguage = account.getPreferredLanguage();
        dto.lastEmiDate = account.getLastEmiDate();
        dto.charges = account.getCharges();
        dto.lastPaymentAmount = account.getLastPaymentAmount();
        dto.lastPaymentDate = account.getLastPaymentDate();
        return dto;
    }

    public Long getAccountId() {
        return accountId;
    }

    public void setAccountId(Long accountId) {
        this.accountId = accountId;
    }

    public String getAccountNumber() {
        return accountNumber;
    }

    public void setAccountNumber(String accountNumber) {
        this.accountNumber = accountNumber;
    }

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = customerName;
    }

    public BigDecimal getLoanAmount() {
        return loanAmount;
    }

    public void setLoanAmount(BigDecimal loanAmount) {
        this.loanAmount = loanAmount;
    }

    public BigDecimal getOverdueAmount() {
        return overdueAmount;
    }

    public void setOverdueAmount(BigDecimal overdueAmount) {
        this.overdueAmount = overdueAmount;
    }

    public String getPreferredLanguage() {
        return preferredLanguage;
    }

    public void setPreferredLanguage(String preferredLanguage) {
        this.preferredLanguage = preferredLanguage;
    }

    public LocalDate getLastEmiDate() {
        return lastEmiDate;
    }

    public void setLastEmiDate(LocalDate lastEmiDate) {
        this.lastEmiDate = lastEmiDate;
    }

    public BigDecimal getCharges() {
        return charges;
    }

    public void setCharges(BigDecimal charges) {
        this.charges = charges;
    }

    public BigDecimal getLastPaymentAmount() {
        return lastPaymentAmount;
    }

    public void setLastPaymentAmount(BigDecimal lastPaymentAmount) {
        this.lastPaymentAmount = lastPaymentAmount;
    }

    public LocalDate getLastPaymentDate() {
        return lastPaymentDate;
    }

    public void setLastPaymentDate(LocalDate lastPaymentDate) {
        this.lastPaymentDate = lastPaymentDate;
    }
}
