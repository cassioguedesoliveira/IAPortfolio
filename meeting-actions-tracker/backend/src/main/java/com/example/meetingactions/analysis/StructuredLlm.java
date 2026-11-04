package com.example.meetingactions.analysis;

import java.util.Map;

/**
 * Port to a language model that returns a JSON object (already parsed into maps and lists).
 * Keeping it this small makes the analysis logic testable without a network and without a JSON library.
 */
public interface StructuredLlm {
    Map<String, Object> extract(String system, String user);
}
