package com.example.meetingactions.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ActionItemRepository extends JpaRepository<ActionItemEntity, Long> {
}
