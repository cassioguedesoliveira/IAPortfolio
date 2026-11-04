package com.example.meetingactions.web;

import com.example.meetingactions.domain.ItemStatus;
import com.example.meetingactions.domain.Priority;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

/** API contracts. Entities never leave the service layer. */
public final class MeetingDtos {

    private MeetingDtos() {}

    public record CreateMeetingRequest(
            @NotBlank @Size(max = 200) String title,
            @NotBlank @Size(max = 20000) String notes,
            LocalDate meetingDate) {
    }

    public record UpdateStatusRequest(@NotNull ItemStatus status) {
    }

    /** {@code allowedStatuses} is computed by the server so the UI never duplicates workflow rules. */
    public record ActionItemDto(
            Long id,
            String description,
            String owner,
            LocalDate dueDate,
            Priority priority,
            ItemStatus status,
            List<ItemStatus> allowedStatuses) {
    }

    public record MeetingSummary(
            Long id,
            String title,
            LocalDate meetingDate,
            Instant createdAt,
            String analysisSource,
            int totalItems,
            int openItems) {
    }

    public record MeetingDetail(
            Long id,
            String title,
            LocalDate meetingDate,
            Instant createdAt,
            String analysisSource,
            String summary,
            List<String> decisions,
            List<ActionItemDto> actionItems) {
    }
}
