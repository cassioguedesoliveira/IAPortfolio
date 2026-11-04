package com.example.meetingactions.config;

import com.example.meetingactions.analysis.HeuristicAnalyzer;
import com.example.meetingactions.analysis.LlmMeetingAnalyzer;
import com.example.meetingactions.analysis.MeetingAnalyzer;
import com.example.meetingactions.analysis.ResilientAnalyzer;
import com.example.meetingactions.llm.AnthropicStructuredLlm;
import java.net.http.HttpClient;
import java.time.Clock;
import java.time.Duration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
public class AppConfig {

    @Bean
    Clock clock() {
        return Clock.systemDefaultZone();
    }

    /**
     * Picks the analyzer from configuration. With {@code app.llm.provider=anthropic} the LLM is used and the
     * rule-based analyzer takes over if a call fails; otherwise only the rule-based analyzer runs.
     */
    @Bean
    MeetingAnalyzer meetingAnalyzer(LlmProperties props, RestClient.Builder builder) {
        HeuristicAnalyzer heuristic = new HeuristicAnalyzer();
        if (!"anthropic".equalsIgnoreCase(props.provider())) {
            return heuristic;
        }
        if (props.apiKey() == null || props.apiKey().isBlank()) {
            throw new IllegalStateException(
                    "ANTHROPIC_API_KEY (app.llm.api-key) is required when app.llm.provider=anthropic");
        }

        HttpClient httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
        JdkClientHttpRequestFactory requestFactory = new JdkClientHttpRequestFactory(httpClient);
        requestFactory.setReadTimeout(props.timeout());

        RestClient client = builder
                .baseUrl(props.baseUrl())
                .requestFactory(requestFactory)
                .defaultHeader("x-api-key", props.apiKey())
                .defaultHeader("anthropic-version", "2023-06-01")
                .build();

        return new ResilientAnalyzer(
                new LlmMeetingAnalyzer(new AnthropicStructuredLlm(client, props.model(), props.maxTokens())),
                heuristic);
    }
}
