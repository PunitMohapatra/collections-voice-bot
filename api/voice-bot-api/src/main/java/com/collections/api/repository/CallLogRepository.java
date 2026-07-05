package com.collections.api.repository;

import com.collections.entity.CallLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * CallLogRepository - JPA repository for call_log table.
 * 
 * Provides CRUD operations and custom query for retrieving
 * call history by account, ordered by most recent first.
 */
@Repository
public interface CallLogRepository extends JpaRepository<CallLog, Long> {

    /**
     * Find all call logs for a given account, ordered by call start time descending.
     * Used to review call history before making a new collection call.
     */
    List<CallLog> findByAccountIdOrderByCallStartTimeDesc(Long accountId);
}
