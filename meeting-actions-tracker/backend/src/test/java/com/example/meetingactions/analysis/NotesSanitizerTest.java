package com.example.meetingactions.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.Test;

class NotesSanitizerTest {

    @Test
    void normalisesLineEndingsAndDropsControlCharacters() {
        assertEquals("a\nb\tc", NotesSanitizer.clean("  a\r\nb\u0000\tc\u0007 "));
    }

    @Test
    void blankNotesAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> NotesSanitizer.clean("  \n\t "));
        assertThrows(IllegalArgumentException.class, () -> NotesSanitizer.clean(null));
    }

    @Test
    void oversizedNotesAreRejected() {
        String tooLong = "x".repeat(NotesSanitizer.MAX_LENGTH + 1);
        assertThrows(IllegalArgumentException.class, () -> NotesSanitizer.clean(tooLong));
    }
}
