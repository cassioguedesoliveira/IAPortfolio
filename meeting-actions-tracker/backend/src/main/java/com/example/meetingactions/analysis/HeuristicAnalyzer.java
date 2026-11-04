package com.example.meetingactions.analysis;

import com.example.meetingactions.domain.ActionItemDraft;
import com.example.meetingactions.domain.Analysis;
import com.example.meetingactions.domain.Priority;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Rule-based analyzer. It needs no network and no API key, so the application works out of the box,
 * and it is the fallback when the LLM is unavailable.
 *
 * <p>Recognised conventions (English and Portuguese prefixes):
 * <pre>
 * Decision: we ship on Friday
 * Action: Ana to send the report by Friday
 * - [ ] @Bruno fix the login bug 2026-11-20 urgent
 * </pre>
 */
public final class HeuristicAnalyzer implements MeetingAnalyzer {

    private static final int CI = Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE;

    private static final Pattern BULLET = Pattern.compile("^[-*\u2022]\\s+(?!\\[)");
    private static final Pattern CHECKED = Pattern.compile("^[-*]\\s*\\[[xX]]");
    private static final Pattern ACTION = Pattern.compile(
            "^(?:[-*]\\s*\\[\\s?]\\s*|(?:action(?: item)?|todo|a\u00e7\u00e3o|acao|tarefa)\\s*[:\\-]\\s*)(.+)$", CI);
    private static final Pattern DECISION = Pattern.compile(
            "^(?:decision|decided|decis\u00e3o|decisao)\\s*[:\\-]\\s*(.+)$", CI);
    private static final Pattern ISO_DATE = Pattern.compile("\\b(\\d{4}-\\d{2}-\\d{2})\\b");
    private static final Pattern WEEKDAY = Pattern.compile(
            "\\b(?:by|until|before|on|due)\\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\\b", CI);
    private static final Pattern TOMORROW = Pattern.compile("\\btomorrow\\b", CI);
    private static final Pattern MENTION = Pattern.compile("@(\\p{L}[\\p{L}'-]*)");
    private static final Pattern SUBJECT = Pattern.compile(
            "^(\\p{Lu}[\\p{L}'-]+)\\s+(?:will|to|should|must|needs to|vai|ir\u00e1)\\s+", Pattern.UNICODE_CASE);
    private static final Pattern HIGH = Pattern.compile("\\b(?:urgent|asap|critical|blocker|urgente|high priority)\\b", CI);
    private static final Pattern LOW = Pattern.compile("\\b(?:low priority|nice to have|when possible)\\b", CI);

    @Override
    public Analysis analyze(String title, String notes, LocalDate meetingDate) {
        LocalDate base = meetingDate != null ? meetingDate : LocalDate.now();
        List<String> prose = new ArrayList<>();
        List<String> decisions = new ArrayList<>();
        List<ActionItemDraft> items = new ArrayList<>();

        for (String rawLine : notes.split("\n")) {
            String line = rawLine.strip();
            if (line.isEmpty() || line.startsWith("#") || CHECKED.matcher(line).find()) {
                continue;
            }
            String unbulleted = BULLET.matcher(line).replaceFirst("");

            Matcher decision = DECISION.matcher(unbulleted);
            if (decision.matches()) {
                decisions.add(decision.group(1).strip());
                continue;
            }
            Matcher action = ACTION.matcher(unbulleted);
            if (action.matches() && !action.group(1).isBlank()) {
                items.add(toDraft(action.group(1).strip(), base));
                continue;
            }
            prose.add(unbulleted);
        }
        return new Analysis(firstSentences(String.join(" ", prose), 2, 300), decisions, items, "heuristic");
    }

    private static ActionItemDraft toDraft(String text, LocalDate base) {
        return new ActionItemDraft(
                MENTION.matcher(text).replaceAll("$1"),
                findOwner(text),
                findDueDate(text, base),
                findPriority(text));
    }

    private static String findOwner(String text) {
        Matcher mention = MENTION.matcher(text);
        if (mention.find()) {
            return mention.group(1);
        }
        Matcher subject = SUBJECT.matcher(text);
        return subject.find() ? subject.group(1) : null;
    }

    private static LocalDate findDueDate(String text, LocalDate base) {
        Matcher iso = ISO_DATE.matcher(text);
        if (iso.find()) {
            try {
                return LocalDate.parse(iso.group(1));
            } catch (DateTimeParseException ignored) {
                // fall through to the other rules
            }
        }
        Matcher weekday = WEEKDAY.matcher(text);
        if (weekday.find()) {
            DayOfWeek day = DayOfWeek.valueOf(weekday.group(1).toUpperCase(Locale.ROOT));
            return base.with(TemporalAdjusters.next(day)); // always strictly after the meeting day
        }
        if (TOMORROW.matcher(text).find()) {
            return base.plusDays(1);
        }
        return null;
    }

    private static Priority findPriority(String text) {
        if (HIGH.matcher(text).find()) {
            return Priority.HIGH;
        }
        return LOW.matcher(text).find() ? Priority.LOW : Priority.MEDIUM;
    }

    private static String firstSentences(String text, int count, int maxChars) {
        if (text.isBlank()) {
            return "";
        }
        String[] sentences = text.split("(?<=[.!?])\\s+");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < Math.min(count, sentences.length); i++) {
            if (i > 0) {
                sb.append(' ');
            }
            sb.append(sentences[i]);
        }
        String result = sb.toString();
        return result.length() <= maxChars ? result : result.substring(0, maxChars - 3).stripTrailing() + "...";
    }
}
