package com.example.meetingactions.domain;

/** Small text helpers shared by the domain records. */
final class Text {
    private Text() {}

    static String truncate(String value, int max) {
        if (value.length() <= max) {
            return value;
        }
        return value.substring(0, max - 3).stripTrailing() + "...";
    }
}
