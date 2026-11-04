package com.example.meetingactions.domain;

import java.util.List;

/**
 * Lifecycle of an action item. The allowed transitions live here, in one place, and the API
 * exposes them to the UI so the frontend never has to duplicate this business rule.
 */
public enum ItemStatus {
    OPEN, IN_PROGRESS, DONE, CANCELLED;

    public List<ItemStatus> allowedTargets() {
        return switch (this) {
            case OPEN -> List.of(IN_PROGRESS, DONE, CANCELLED);
            case IN_PROGRESS -> List.of(OPEN, DONE, CANCELLED);
            case DONE, CANCELLED -> List.of(OPEN); // closed items can only be reopened
        };
    }

    public boolean canTransitionTo(ItemStatus target) {
        return allowedTargets().contains(target);
    }

    public boolean isActive() {
        return this == OPEN || this == IN_PROGRESS;
    }
}
