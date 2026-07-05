package com.collections;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/**
 * VoiceBotApiApplication - Main Spring Boot application class
 * 
 * This class bootstraps the Spring Boot REST API server for the
 * Debt Collections Voice Bot.
 * 
 * Annotations:
 *   @SpringBootApplication: Enables Spring Boot auto-configuration
 *   @ComponentScan: Scans for components (controllers, services)
 *   @EnableJpaRepositories: Enables JPA repository scanning
 * 
 * Scan Base Packages:
 *   com.collections - Main package for controllers and application
 *   com.collections.entity - Entity classes
 *   com.collections.api - API layer (repositories, DTOs)
 */
@SpringBootApplication(scanBasePackages = "com.collections")
@EntityScan(basePackages = "com.collections.entity")
@EnableJpaRepositories(basePackages = "com.collections.api")
public class VoiceBotApiApplication {

    /**
     * Main entry point for the Spring Boot application.
     * Called when running with 'mvn spring-boot:run' or 'java -jar'.
     * 
     * @param args Command line arguments (not used)
     */
    public static void main(String[] args) {
        // Start the Spring Boot application
        SpringApplication.run(VoiceBotApiApplication.class, args);
    }

}
