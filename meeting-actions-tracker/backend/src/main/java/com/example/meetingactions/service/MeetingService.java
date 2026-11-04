package com.example.meetingactions.service;

import com.example.meetingactions.analysis.MeetingAnalyzer;
import com.example.meetingactions.analysis.NotesSanitizer;
import com.example.meetingactions.domain.ActionItemDraft;
import com.example.meetingactions.domain.Analysis;
import com.example.meetingactions.domain.ItemStatus;
import com.example.meetingactions.persistence.ActionItemEntity;
import com.example.meetingactions.persistence.ActionItemRepository;
import com.example.meetingactions.persistence.MeetingEntity;
import com.example.meetingactions.persistence.MeetingRepository;
import com.example.meetingactions.web.MeetingDtos.ActionItemDto;
import com.example.meetingactions.web.MeetingDtos.CreateMeetingRequest;
import com.example.meetingactions.web.MeetingDtos.MeetingDetail;
import com.example.meetingactions.web.MeetingDtos.MeetingSummary;
import java.time.Clock;
import java.time.LocalDate;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class MeetingService {

    private final MeetingRepository meetings;
    private final ActionItemRepository items;
    private final MeetingAnalyzer analyzer;
    private final Clock clock;

    public MeetingService(MeetingRepository meetings, ActionItemRepository items,
                          MeetingAnalyzer analyzer, Clock clock) {
        this.meetings = meetings;
        this.items = items;
        this.analyzer = analyzer;
        this.clock = clock;
    }

    /**
     * Deliberately NOT @Transactional: the analysis may call an external LLM for several seconds and
     * must not hold a database connection while it waits. Only the final save is transactional.
     */
    public MeetingDetail create(CreateMeetingRequest request) {
        String title = request.title().strip();
        String notes = NotesSanitizer.clean(request.notes());
        LocalDate date = request.meetingDate() != null ? request.meetingDate() : LocalDate.now(clock);

        Analysis analysis = analyzer.analyze(title, notes, date);

        MeetingEntity meeting = new MeetingEntity(
                title, notes, date, analysis.summary(), analysis.decisions(), analysis.source(), clock.instant());
        for (ActionItemDraft draft : analysis.actionItems()) {
            meeting.addActionItem(new ActionItemEntity(draft.description(), draft.owner(), draft.dueDate(), draft.priority()));
        }
        return toDetail(meetings.save(meeting));
    }

    @Transactional(readOnly = true)
    public List<MeetingSummary> list() {
        return meetings.findAllByOrderByCreatedAtDesc().stream().map(this::toSummary).toList();
    }

    @Transactional(readOnly = true)
    public MeetingDetail get(Long id) {
        return toDetail(find(id));
    }

    @Transactional
    public void delete(Long id) {
        meetings.delete(find(id));
    }

    @Transactional
    public ActionItemDto updateStatus(Long itemId, ItemStatus target) {
        ActionItemEntity item = items.findById(itemId)
                .orElseThrow(() -> new NotFoundException("Action item " + itemId + " not found"));
        if (item.getStatus() != target) { // asking for the current status is a harmless no-op
            if (!item.getStatus().canTransitionTo(target)) {
                throw new InvalidTransitionException(
                        "Cannot move an item from " + item.getStatus() + " to " + target
                                + ". Allowed: " + item.getStatus().allowedTargets());
            }
            item.setStatus(target);
        }
        return toDto(item);
    }

    private MeetingEntity find(Long id) {
        return meetings.findById(id).orElseThrow(() -> new NotFoundException("Meeting " + id + " not found"));
    }

    private MeetingSummary toSummary(MeetingEntity m) {
        int open = (int) m.getActionItems().stream().filter(i -> i.getStatus().isActive()).count();
        return new MeetingSummary(m.getId(), m.getTitle(), m.getMeetingDate(), m.getCreatedAt(),
                m.getAnalysisSource(), m.getActionItems().size(), open);
    }

    private MeetingDetail toDetail(MeetingEntity m) {
        return new MeetingDetail(m.getId(), m.getTitle(), m.getMeetingDate(), m.getCreatedAt(),
                m.getAnalysisSource(), m.getSummary(), List.copyOf(m.getDecisions()),
                m.getActionItems().stream().map(this::toDto).toList());
    }

    private ActionItemDto toDto(ActionItemEntity i) {
        return new ActionItemDto(i.getId(), i.getDescription(), i.getOwnerName(), i.getDueDate(),
                i.getPriority(), i.getStatus(), i.getStatus().allowedTargets());
    }
}
