package com.example.meetingactions.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import com.example.meetingactions.domain.ActionItemDraft;
import com.example.meetingactions.domain.Analysis;
import com.example.meetingactions.domain.Priority;
import java.time.LocalDate;
import org.junit.jupiter.api.Test;

class HeuristicAnalyzerTest {

    private static final LocalDate MONDAY = LocalDate.of(2026, 11, 2);

    private static final String NOTES = String.join("\n",
            "# Weekly sync",
            "We reviewed the Q4 roadmap. The team is aligned on priorities. Nothing else.",
            "Decision: ship the beta on 2026-11-30",
            "- Action: Ana to send the report by Friday",
            "- [ ] @Bruno fix the login bug urgent",
            "- [x] already finished thing",
            "TODO: book the venue tomorrow low priority",
            "A\u00e7\u00e3o: Carla vai revisar o contrato 2026-12-01");

    private final HeuristicAnalyzer analyzer = new HeuristicAnalyzer();

    @Test
    void extractsSummaryDecisionsAndItems() {
        Analysis analysis = analyzer.analyze("Weekly sync", NOTES, MONDAY);

        assertEquals("heuristic", analysis.source());
        assertEquals("We reviewed the Q4 roadmap. The team is aligned on priorities.", analysis.summary());
        assertEquals(1, analysis.decisions().size());
        assertEquals("ship the beta on 2026-11-30", analysis.decisions().get(0));
        assertEquals(4, analysis.actionItems().size()); // the checked box is ignored
    }

    @Test
    void resolvesOwnersDatesAndPriorities() {
        Analysis analysis = analyzer.analyze("Weekly sync", NOTES, MONDAY);

        ActionItemDraft ana = analysis.actionItems().get(0);
        assertEquals("Ana to send the report by Friday", ana.description());
        assertEquals("Ana", ana.owner());
        assertEquals(LocalDate.of(2026, 11, 6), ana.dueDate());
        assertEquals(Priority.MEDIUM, ana.priority());

        ActionItemDraft bruno = analysis.actionItems().get(1);
        assertEquals("Bruno fix the login bug urgent", bruno.description());
        assertEquals("Bruno", bruno.owner());
        assertEquals(Priority.HIGH, bruno.priority());
        assertNull(bruno.dueDate());

        ActionItemDraft venue = analysis.actionItems().get(2);
        assertNull(venue.owner());
        assertEquals(LocalDate.of(2026, 11, 3), venue.dueDate());
        assertEquals(Priority.LOW, venue.priority());

        ActionItemDraft carla = analysis.actionItems().get(3);
        assertEquals("Carla", carla.owner());
        assertEquals(LocalDate.of(2026, 12, 1), carla.dueDate());
    }

    @Test
    void weekdayOnTheMeetingDayMeansNextWeek() {
        LocalDate friday = LocalDate.of(2026, 11, 6);
        Analysis analysis = analyzer.analyze("t", "Action: Ana to deploy by Friday", friday);
        assertEquals(LocalDate.of(2026, 11, 13), analysis.actionItems().get(0).dueDate());
    }

    @Test
    void notesWithoutStructureProduceOnlyASummary() {
        Analysis analysis = analyzer.analyze("t", "Just a chat about lunch.", MONDAY);
        assertEquals("Just a chat about lunch.", analysis.summary());
        assertEquals(0, analysis.actionItems().size());
        assertEquals(0, analysis.decisions().size());
    }
}
