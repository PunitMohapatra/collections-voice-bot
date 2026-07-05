package com.collections.api.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.collections.api.dto.CallLogDTO;
import com.collections.api.dto.CallLogRequest;
import com.collections.api.repository.CallLogRepository;
import com.collections.entity.CallLog;

/**
 * CallLogController - Records every call outcome for audit and analytics.
 * 
 * POST /api/v1/call-log      - Create a new call log entry (called by bot)
 * GET  /api/v1/call-log/{id}  - Retrieve call history for an account
 */
@RestController
@RequestMapping("/api/v1/call-log")
public class CallLogController {

    @Autowired
    private CallLogRepository callLogRepository;

    /**
     * Create a new call log entry.
     * Called by the FastAPI bot server when a call starts and when it ends.
     */
    @PostMapping
    public ResponseEntity<CallLogDTO> createCallLog(@RequestBody CallLogRequest request) {
        CallLog callLog = new CallLog();
        callLog.setAccountId(request.getAccountId());
        callLog.setFollowupId(request.getFollowupId());
        callLog.setCallStartTime(request.getCallStartTime());
        callLog.setCallEndTime(request.getCallEndTime());
        callLog.setCallStatus(request.getCallStatus());
        callLog.setLanguageUsed(request.getLanguageUsed());
        callLog.setPtpCaptured(request.getPtpCaptured() != null ? request.getPtpCaptured() : false);
        callLog.setEscalated(request.getEscalated() != null ? request.getEscalated() : false);

        CallLog savedCallLog = callLogRepository.save(callLog);
        return ResponseEntity.ok(CallLogDTO.fromEntity(savedCallLog));
    }

    /**
     * Retrieve all call logs for a given account.
     * Useful for reviewing call history before making a new call.
     */
    @GetMapping("/{accountId}")
    public ResponseEntity<List<CallLogDTO>> getCallLogsByAccount(@PathVariable Long accountId) {
        List<CallLog> callLogs = callLogRepository.findByAccountIdOrderByCallStartTimeDesc(accountId);
        List<CallLogDTO> dtos = callLogs.stream()
            .map(CallLogDTO::fromEntity)
            .toList();
        return ResponseEntity.ok(dtos);
    }
}
