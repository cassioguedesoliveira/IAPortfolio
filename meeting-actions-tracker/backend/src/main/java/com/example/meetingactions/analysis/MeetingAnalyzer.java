package com.example.meetingactions.analysis;

import com.example.meetingactions.domain.Analysis;
import java.time.LocalDate;

public interface MeetingAnalyzer {
    /**
     * @param meetingDate used to resolve relative dates such as "by Friday"
     */
    Analysis analyze(String title, String notes, LocalDate meetingDate);
}
