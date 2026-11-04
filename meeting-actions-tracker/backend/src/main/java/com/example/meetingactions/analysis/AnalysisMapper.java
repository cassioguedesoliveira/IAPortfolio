package com.example.meetingactions.analysis;

import com.example.meetingactions.domain.ActionItemDraft;
import com.example.meetingactions.domain.Analysis;
import com.example.meetingactions.domain.Priority;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Turns the model's raw JSON (as maps and lists) into a validated {@link Analysis}.
 * Model output is untrusted: bad dates, unknown priorities and junk items are dropped or defaulted
 * instead of failing the whole request.
 */
public final class AnalysisMapper {

    static final int MAX_ITEMS = 50;
    static final int MAX_DECISIONS = 30;
    private static final Set<String> EMPTY_OWNERS = Set.of("null", "none", "n/a", "na", "unassigned", "unknown", "-");

    private AnalysisMapper() {}

    public static Analysis fromMap(Map<String, Object> raw, String source) {
        if (raw == null || !(raw.containsKey("summary") || raw.containsKey("decisions") || raw.containsKey("action_items"))) {
            throw new InvalidModelOutputException("model output contains none of the expected fields");
        }

        List<String> decisions = new ArrayList<>();
        for (Object o : asList(raw.get("decisions"))) {
            String text = asString(o);
            if (!text.isEmpty() && decisions.size() < MAX_DECISIONS) {
                decisions.add(text);
            }
        }

        List<ActionItemDraft> items = new ArrayList<>();
        for (Object o : asList(raw.get("action_items"))) {
            if (items.size() >= MAX_ITEMS) {
                break;
            }
            if (!(o instanceof Map<?, ?> map)) {
                continue;
            }
            String description = asString(map.get("description"));
            if (description.isEmpty()) {
                continue;
            }
            items.add(new ActionItemDraft(
                    description,
                    normalizeOwner(asString(map.get("owner"))),
                    parseDate(map.get("due_date")),
                    Priority.parse(map.get("priority"), Priority.MEDIUM)));
        }
        return new Analysis(asString(raw.get("summary")), decisions, items, source);
    }

    private static String asString(Object value) {
        return value == null ? "" : value.toString().strip();
    }

    private static List<?> asList(Object value) {
        return value instanceof List<?> list ? list : List.of();
    }

    private static String normalizeOwner(String owner) {
        return EMPTY_OWNERS.contains(owner.toLowerCase(Locale.ROOT)) ? null : owner;
    }

    private static LocalDate parseDate(Object value) {
        String text = asString(value);
        if (text.isEmpty()) {
            return null;
        }
        try {
            return LocalDate.parse(text);
        } catch (DateTimeParseException e) {
            return null; // an invented or malformed date is worse than no date
        }
    }
}
