package com.collections.api.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.collections.api.dto.FollowupRequest;
import com.collections.api.repository.FollowupRepository;
import com.collections.entity.Followup;

/**
 * FollowupController - Handles followup record creation.
 * 
 * POST /api/v1/followup - Creates a new followup record with remarks.
 * Called by Rasa action_save_followup at the end of each call.
 */
@RestController
@RequestMapping("/api/v1")
public class FollowupController {

    @Autowired
    private FollowupRepository followupRepository;

    @PostMapping("/followup")
    public ResponseEntity<Followup> createFollowup(@RequestBody FollowupRequest followupRequest) {
        Followup followup = new Followup();
        followup.setAccountId(followupRequest.getAccountId());
        followup.setRemarks(followupRequest.getRemarks());
        Followup savedFollowup = followupRepository.save(followup);
        return ResponseEntity.ok(savedFollowup);
    }
}
