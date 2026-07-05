package com.collections.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(name = "accounts")
public class Account {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "\"accountId\"")
    private Long accountId;

    @Column(name = "\"accountNumber\"", nullable = false, unique = true, length = 50)
    private String accountNumber;

    @Column(name = "\"customerName\"", nullable = false, length = 200)
    private String customerName;

    @Column(name = "\"loanAmount\"", nullable = false, precision = 15, scale = 2)
    private BigDecimal loanAmount;

    @Column(name = "\"overdueAmount\"", nullable = false, precision = 15, scale = 2)
    private BigDecimal overdueAmount;

    @Column(name = "\"preferredLanguage\"", length = 20)
    private String preferredLanguage = "en";

    @Column(name = "\"lastEmiDate\"")
    private LocalDate lastEmiDate;

    @Column(name = "\"charges\"", nullable = false, precision = 15, scale = 2)
    private BigDecimal charges = BigDecimal.ZERO;

    @Column(name = "\"lastPaymentAmount\"", nullable = false, precision = 15, scale = 2)
    private BigDecimal lastPaymentAmount = BigDecimal.ZERO;

    @Column(name = "\"lastPaymentDate\"")
    private LocalDate lastPaymentDate;

    public Account() {
        this.loanAmount = BigDecimal.ZERO;
        this.overdueAmount = BigDecimal.ZERO;
        this.charges = BigDecimal.ZERO;
        this.lastPaymentAmount = BigDecimal.ZERO;
        this.preferredLanguage = "en";
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
