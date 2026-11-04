package com.example.meetingactions.domain;

import java.time.LocalDate;

/** An action item as extracted from the notes, before it is persisted. */
public record ActionItemDraft(String description, String owner, LocalDate dueDate, Priority priority) {

    public static final int MAX_DESCRIPTION = 500;
    public static final int MAX_OWNER = 100;

    public ActionItemDraft {
        description = description == null ? "" : description.strip();
        if (description.isEmpty()) {
            throw new IllegalArgumentException("description must not be blank");
        }
        description = Text.truncate(description, MAX_DESCRIPTION);
        owner = owner == null || owner.isBlank() ? null : Text.truncate(owner.strip(), MAX_OWNER);
        priority = priority == null ? Priority.MEDIUM : priority;
    }
}
