package com.example.meetingactions.analysis;

import com.example.meetingactions.domain.Analysis;
import java.time.LocalDate;

/** Tries the primary analyzer (LLM) and degrades gracefully to a fallback (heuristics) if it fails. */
public final class ResilientAnalyzer implements MeetingAnalyzer {

    private static final System.Logger LOG = System.getLogger(ResilientAnalyzer.class.getName());

    private final MeetingAnalyzer primary;
    private final MeetingAnalyzer fallback;

    public ResilientAnalyzer(MeetingAnalyzer primary, MeetingAnalyzer fallback) {
        this.primary = primary;
        this.fallback = fallback;
    }

    @Override
    public Analysis analyze(String title, String notes, LocalDate meetingDate) {
        try {
            return primary.analyze(title, notes, meetingDate);
        } catch (LlmException e) {
            LOG.log(System.Logger.Level.WARNING, "LLM analysis failed, using heuristic fallback: {0}", e.getMessage());
            return fallback.analyze(title, notes, meetingDate);
        }
    }
}
