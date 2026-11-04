package com.example.meetingactions;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class MeetingActionsApplication {

    public static void main(String[] args) {
        SpringApplication.run(MeetingActionsApplication.class, args);
    }
}
