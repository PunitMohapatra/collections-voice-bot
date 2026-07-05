package com.collections.api.repository;

import com.collections.entity.Promise;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Promise Repository - Database access layer for Promise entity
 * 
 * This interface extends JpaRepository to provide CRUD operations
 * and custom query methods for the promise table.
 * 
 * Methods provided:
 *   save() - Saves or updates a promise
 *   findById() - Finds promise by ID
 */
@Repository
public interface PromiseRepository extends JpaRepository<Promise, Long> {

}
