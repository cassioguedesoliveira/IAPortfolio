package com.example.meetingactions.analysis;

/** The model answered, but not with something we can use. */
public class InvalidModelOutputException extends LlmException {
    public InvalidModelOutputException(String message) {
        super(message);
    }
}
