package com.example.meetingactions.analysis;

public final class NotesSanitizer {

    public static final int MAX_LENGTH = 20_000;

    private NotesSanitizer() {}

    /** Normalises line endings, drops control characters and enforces size limits. */
    public static String clean(String raw) {
        if (raw == null) {
            throw new IllegalArgumentException("notes must not be empty");
        }
        String normalized = raw.replace("\r\n", "\n").replace('\r', '\n');
        StringBuilder sb = new StringBuilder(normalized.length());
        normalized.codePoints()
                .filter(cp -> cp == '\n' || cp == '\t' || !Character.isISOControl(cp))
                .forEach(sb::appendCodePoint);
        String cleaned = sb.toString().strip();
        if (cleaned.isEmpty()) {
            throw new IllegalArgumentException("notes must not be empty");
        }
        if (cleaned.length() > MAX_LENGTH) {
            throw new IllegalArgumentException("notes must not exceed " + MAX_LENGTH + " characters");
        }
        return cleaned;
    }
}
