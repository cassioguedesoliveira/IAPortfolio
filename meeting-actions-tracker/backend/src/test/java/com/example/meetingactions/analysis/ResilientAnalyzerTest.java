package com.example.meetingactions.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.example.meetingactions.domain.Analysis;
import java.time.LocalDate;
import org.junit.jupiter.api.Test;

class ResilientAnalyzerTest {

    private static final LocalDate DATE = LocalDate.of(2026, 11, 2);

    @Test
    void fallsBackToHeuristicsWhenTheLlmFails() {
        MeetingAnalyzer failing = (title, notes, date) -> {
            throw new LlmException("API down");
        };
        Analysis analysis = new ResilientAnalyzer(failing, new HeuristicAnalyzer())
                .analyze("t", "Action: Ana to ship it", DATE);

        assertEquals("heuristic", analysis.source());
        assertEquals(1, analysis.actionItems().size());
    }

    @Test
    void programmingErrorsAreNotSwallowed() {
        MeetingAnalyzer buggy = (title, notes, date) -> {
            throw new IllegalStateException("bug");
        };
        ResilientAnalyzer analyzer = new ResilientAnalyzer(buggy, new HeuristicAnalyzer());
        assertThrows(IllegalStateException.class, () -> analyzer.analyze("t", "n", DATE));
    }
}
