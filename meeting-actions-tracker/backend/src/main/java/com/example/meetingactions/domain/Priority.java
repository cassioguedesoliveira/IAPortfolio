package com.example.meetingactions.domain;

import java.util.Locale;

public enum Priority {
    HIGH, MEDIUM, LOW;

    /** Lenient parser for untrusted input (LLM output). Unknown values fall back instead of failing. */
    public static Priority parse(Object raw, Priority fallback) {
        if (raw == null) {
            return fallback;
        }
        String normalized = raw.toString().strip().toUpperCase(Locale.ROOT);
        for (Priority p : values()) {
            if (p.name().equals(normalized)) {
                return p;
            }
        }
        return fallback;
    }
}
