package com.example.meetingactions.domain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class ItemStatusTest {

    @Test
    void closedItemsCanOnlyBeReopened() {
        assertEquals(List.of(ItemStatus.OPEN), ItemStatus.DONE.allowedTargets());
        assertEquals(List.of(ItemStatus.OPEN), ItemStatus.CANCELLED.allowedTargets());
        assertFalse(ItemStatus.DONE.canTransitionTo(ItemStatus.IN_PROGRESS));
    }

    @Test
    void openItemsCanMoveForward() {
        assertTrue(ItemStatus.OPEN.canTransitionTo(ItemStatus.IN_PROGRESS));
        assertTrue(ItemStatus.IN_PROGRESS.canTransitionTo(ItemStatus.DONE));
    }

    @Test
    void sameStatusIsNotATransition() {
        for (ItemStatus status : ItemStatus.values()) {
            assertFalse(status.canTransitionTo(status));
        }
    }

    @Test
    void onlyOpenAndInProgressAreActive() {
        assertTrue(ItemStatus.OPEN.isActive());
        assertTrue(ItemStatus.IN_PROGRESS.isActive());
        assertFalse(ItemStatus.DONE.isActive());
        assertFalse(ItemStatus.CANCELLED.isActive());
    }
}
