package com.example.meetingactions.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.example.meetingactions.domain.Analysis;
import com.example.meetingactions.domain.Priority;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class AnalysisMapperTest {

    @Test
    void mapsValidOutput() {
        Map<String, Object> raw = Map.of(
                "summary", " Roadmap reviewed. ",
                "decisions", List.of("Ship beta"),
                "action_items", List.of(Map.of(
                        "description", "Send report", "owner", "Ana", "due_date", "2026-11-06", "priority", "high")));

        Analysis analysis = AnalysisMapper.fromMap(raw, "llm");

        assertEquals("Roadmap reviewed.", analysis.summary());
        assertEquals(List.of("Ship beta"), analysis.decisions());
        assertEquals("llm", analysis.source());
        assertEquals(1, analysis.actionItems().size());
        assertEquals("Ana", analysis.actionItems().get(0).owner());
        assertEquals(LocalDate.of(2026, 11, 6), analysis.actionItems().get(0).dueDate());
        assertEquals(Priority.HIGH, analysis.actionItems().get(0).priority());
    }

    @Test
    void badValuesAreDefaultedAndJunkIsDropped() {
        Map<String, Object> noDescription = new HashMap<>();
        noDescription.put("owner", "Zed");
        Map<String, Object> messy = new HashMap<>();
        messy.put("description", "Fix bug");
        messy.put("owner", "None");
        messy.put("due_date", "next friday");
        messy.put("priority", "URGENT!!");
        Map<String, Object> raw = Map.of(
                "summary", "s",
                "decisions", List.of("", "  "),
                "action_items", List.of(messy, noDescription, "not an object"));

        Analysis analysis = AnalysisMapper.fromMap(raw, "llm");

        assertEquals(0, analysis.decisions().size());
        assertEquals(1, analysis.actionItems().size());
        assertNull(analysis.actionItems().get(0).owner());
        assertNull(analysis.actionItems().get(0).dueDate());
        assertEquals(Priority.MEDIUM, analysis.actionItems().get(0).priority());
    }

    @Test
    void outputWithoutExpectedFieldsIsRejected() {
        assertThrows(InvalidModelOutputException.class, () -> AnalysisMapper.fromMap(Map.of("foo", "bar"), "llm"));
        assertThrows(InvalidModelOutputException.class, () -> AnalysisMapper.fromMap(null, "llm"));
    }

    @Test
    void itemCountIsBounded() {
        List<Object> many = new ArrayList<>();
        for (int i = 0; i < 80; i++) {
            many.add(Map.of("description", "task " + i));
        }
        Analysis analysis = AnalysisMapper.fromMap(Map.of("action_items", many), "llm");
        assertEquals(AnalysisMapper.MAX_ITEMS, analysis.actionItems().size());
    }
}
