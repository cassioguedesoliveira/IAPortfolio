package com.example.meetingactions.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties(prefix = "app.llm")
public record LlmProperties(
        @DefaultValue("heuristic") String provider,
        String apiKey,
        @DefaultValue("claude-sonnet-5-5") String model,
        @DefaultValue("https://api.anthropic.com") String baseUrl,
        @DefaultValue("1024") int maxTokens,
        @DefaultValue("30s") Duration timeout) {
}
