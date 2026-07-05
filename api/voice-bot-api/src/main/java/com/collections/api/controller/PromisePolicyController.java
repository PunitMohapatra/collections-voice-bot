package com.collections.api.controller;

import com.collections.api.dto.PromisePolicyDTO;
import com.collections.api.repository.PromisePolicyRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/promise-policy")
public class PromisePolicyController {

    @Autowired
    private PromisePolicyRepository promisePolicyRepository;

    @GetMapping
    public ResponseEntity<PromisePolicyDTO> getPromisePolicy() {
        return promisePolicyRepository.findTopBy()
            .map(PromisePolicyDTO::fromEntity)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
