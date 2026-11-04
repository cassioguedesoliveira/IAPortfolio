package com.example.meetingactions.persistence;

import jakarta.persistence.CascadeType;
import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.OrderColumn;
import jakarta.persistence.Table;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "meetings")
public class MeetingEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, length = 20000)
    private String notes;

    @Column(nullable = false)
    private LocalDate meetingDate;

    @Column(length = 2000)
    private String summary;

    @ElementCollection
    @CollectionTable(name = "meeting_decisions", joinColumns = @JoinColumn(name = "meeting_id"))
    @OrderColumn(name = "decision_order")
    @Column(name = "decision", length = 500)
    private List<String> decisions = new ArrayList<>();

    @Column(nullable = false, length = 20)
    private String analysisSource;

    @Column(nullable = false)
    private Instant createdAt;

    @OneToMany(mappedBy = "meeting", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("id ASC")
    private List<ActionItemEntity> actionItems = new ArrayList<>();

    protected MeetingEntity() {
        // required by JPA
    }

    public MeetingEntity(String title, String notes, LocalDate meetingDate, String summary,
                         List<String> decisions, String analysisSource, Instant createdAt) {
        this.title = title;
        this.notes = notes;
        this.meetingDate = meetingDate;
        this.summary = summary;
        this.decisions = new ArrayList<>(decisions);
        this.analysisSource = analysisSource;
        this.createdAt = createdAt;
    }

    public void addActionItem(ActionItemEntity item) {
        actionItems.add(item);
        item.setMeeting(this);
    }

    public Long getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getNotes() {
        return notes;
    }

    public LocalDate getMeetingDate() {
        return meetingDate;
    }

    public String getSummary() {
        return summary;
    }

    public List<String> getDecisions() {
        return decisions;
    }

    public String getAnalysisSource() {
        return analysisSource;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public List<ActionItemEntity> getActionItems() {
        return actionItems;
    }
}
