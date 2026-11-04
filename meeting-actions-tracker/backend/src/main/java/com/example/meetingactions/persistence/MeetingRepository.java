package com.example.meetingactions.persistence;

import java.util.List;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MeetingRepository extends JpaRepository<MeetingEntity, Long> {

    /** Fetches items in the same query, avoiding an N+1 when the list view counts open items. */
    @EntityGraph(attributePaths = "actionItems")
    List<MeetingEntity> findAllByOrderByCreatedAtDesc();
}
