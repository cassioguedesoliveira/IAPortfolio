package com.example.meetingactions.web;

import com.example.meetingactions.service.MeetingService;
import com.example.meetingactions.web.MeetingDtos.ActionItemDto;
import com.example.meetingactions.web.MeetingDtos.CreateMeetingRequest;
import com.example.meetingactions.web.MeetingDtos.MeetingDetail;
import com.example.meetingactions.web.MeetingDtos.MeetingSummary;
import com.example.meetingactions.web.MeetingDtos.UpdateStatusRequest;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class MeetingController {

    private final MeetingService service;

    public MeetingController(MeetingService service) {
        this.service = service;
    }

    @PostMapping("/meetings")
    public ResponseEntity<MeetingDetail> create(@Valid @RequestBody CreateMeetingRequest request) {
        MeetingDetail created = service.create(request);
        return ResponseEntity.created(URI.create("/api/meetings/" + created.id())).body(created);
    }

    @GetMapping("/meetings")
    public List<MeetingSummary> list() {
        return service.list();
    }

    @GetMapping("/meetings/{id}")
    public MeetingDetail get(@PathVariable Long id) {
        return service.get(id);
    }

    @DeleteMapping("/meetings/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        service.delete(id);
    }

    @PatchMapping("/action-items/{id}/status")
    public ActionItemDto updateStatus(@PathVariable Long id, @Valid @RequestBody UpdateStatusRequest request) {
        return service.updateStatus(id, request.status());
    }
}
