package com.collections.api.repository;

import com.collections.entity.Followup;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Followup Repository - Database access layer for Followup entity
 * 
 * This interface extends JpaRepository to provide CRUD operations
 * and custom query methods for the followup table.
 * 
 * Methods provided:
 *   save() - Saves or updates a followup record
 *   findById() - Finds followup by ID
 */
@Repository
public interface FollowupRepository extends JpaRepository<Followup, Long> {

}
