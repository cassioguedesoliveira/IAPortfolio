package com.example.meetingactions.domain;

import java.util.List;

/** Result of analysing meeting notes. {@code source} records how it was produced ("llm" or "heuristic"). */
public record Analysis(String summary, List<String> decisions, List<ActionItemDraft> actionItems, String source) {

    public static final int MAX_SUMMARY = 2000;
    public static final int MAX_DECISION = 500;

    public Analysis {
        summary = summary == null ? "" : Text.truncate(summary.strip(), MAX_SUMMARY);
        decisions = decisions == null
                ? List.of()
                : decisions.stream().map(d -> Text.truncate(d.strip(), MAX_DECISION)).toList();
        actionItems = actionItems == null ? List.of() : List.copyOf(actionItems);
        source = source == null || source.isBlank() ? "unknown" : source;
    }

    public Analysis withSource(String newSource) {
        return new Analysis(summary, decisions, actionItems, newSource);
    }
}
