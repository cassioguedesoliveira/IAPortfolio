package com.example.meetingactions.domain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class ActionItemDraftTest {

    @Test
    void blankDescriptionIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> new ActionItemDraft("   ", null, null, null));
    }

    @Test
    void valuesAreNormalised() {
        ActionItemDraft draft = new ActionItemDraft("  Send report  ", "   ", null, null);
        assertEquals("Send report", draft.description());
        assertNull(draft.owner());
        assertEquals(Priority.MEDIUM, draft.priority());
    }

    @Test
    void overlongDescriptionIsTruncated() {
        ActionItemDraft draft = new ActionItemDraft("x".repeat(900), null, null, Priority.HIGH);
        assertEquals(ActionItemDraft.MAX_DESCRIPTION, draft.description().length());
        assertTrue(draft.description().endsWith("..."));
    }
}
