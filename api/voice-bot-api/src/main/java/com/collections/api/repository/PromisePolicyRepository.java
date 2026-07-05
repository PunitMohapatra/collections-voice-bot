package com.collections.api.repository;

import com.collections.entity.PromisePolicy;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PromisePolicyRepository extends JpaRepository<PromisePolicy, Long> {

    Optional<PromisePolicy> findTopBy();
}
