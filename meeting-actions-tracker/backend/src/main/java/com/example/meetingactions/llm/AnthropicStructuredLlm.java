package com.example.meetingactions.llm;

import com.example.meetingactions.analysis.InvalidModelOutputException;
import com.example.meetingactions.analysis.LlmException;
import com.example.meetingactions.analysis.StructuredLlm;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

/**
 * Calls the Anthropic Messages API and forces the model to answer through a tool, so the reply is a JSON object
 * that follows the schema below. This is more reliable than asking for JSON in prose and then fishing it out
 * of markdown fences.
 */
public class AnthropicStructuredLlm implements StructuredLlm {

    static final String TOOL_NAME = "record_meeting_analysis";

    private final RestClient client;
    private final String model;
    private final int maxTokens;

    public AnthropicStructuredLlm(RestClient client, String model, int maxTokens) {
        this.client = client;
        this.model = model;
        this.maxTokens = maxTokens;
    }

    @Override
    public Map<String, Object> extract(String system, String user) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("model", model);
        body.put("max_tokens", maxTokens);
        body.put("system", system);
        body.put("tools", List.of(Map.of(
                "name", TOOL_NAME,
                "description", "Record the structured analysis of the meeting notes.",
                "input_schema", inputSchema())));
        body.put("tool_choice", Map.of("type", "tool", "name", TOOL_NAME));
        body.put("messages", List.of(Map.of("role", "user", "content", user)));

        MessagesResponse response;
        try {
            response = client.post()
                    .uri("/v1/messages")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(body)
                    .retrieve()
                    .body(MessagesResponse.class);
        } catch (RestClientException e) {
            // Deliberately not including the request or headers, which contain the API key.
            throw new LlmException("Anthropic API call failed: " + e.getMessage(), e);
        }

        if (response == null || response.content() == null) {
            throw new InvalidModelOutputException("empty response from the model");
        }
        for (ContentBlock block : response.content()) {
            if ("tool_use".equals(block.type()) && TOOL_NAME.equals(block.name()) && block.input() != null) {
                return block.input();
            }
        }
        throw new InvalidModelOutputException("the model did not call the " + TOOL_NAME + " tool");
    }

    private static Map<String, Object> inputSchema() {
        Map<String, Object> actionItem = Map.of(
                "type", "object",
                "properties", Map.of(
                        "description", Map.of("type", "string"),
                        "owner", Map.of("type", "string"),
                        "due_date", Map.of("type", "string", "description", "ISO date YYYY-MM-DD, or empty"),
                        "priority", Map.of("type", "string", "enum", List.of("HIGH", "MEDIUM", "LOW"))),
                "required", List.of("description"));
        return Map.of(
                "type", "object",
                "properties", Map.of(
                        "summary", Map.of("type", "string"),
                        "decisions", Map.of("type", "array", "items", Map.of("type", "string")),
                        "action_items", Map.of("type", "array", "items", actionItem)),
                "required", List.of("summary", "decisions", "action_items"));
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record MessagesResponse(List<ContentBlock> content) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record ContentBlock(String type, String name, Map<String, Object> input) {
    }
}
