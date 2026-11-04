package com.example.meetingactions.web;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.jayway.jsonpath.JsonPath;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:meetings-test;DB_CLOSE_DELAY=-1",
        "app.llm.provider=heuristic"
})
@AutoConfigureMockMvc
class MeetingApiIntegrationTest {

    private static final String NOTES =
            "Weekly sync. We aligned on the roadmap.\\nDecision: ship the beta\\n"
                    + "Action: Ana to send the report 2026-11-20 urgent";

    @Autowired
    private MockMvc mvc;

    private static String json(String title, String notes) {
        return "{\"title\":\"" + title + "\",\"notes\":\"" + notes + "\",\"meetingDate\":\"2026-11-02\"}";
    }

    private MvcResult createMeeting() throws Exception {
        return mvc.perform(post("/api/meetings").contentType(MediaType.APPLICATION_JSON).content(json("Weekly sync", NOTES)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.analysisSource").value("heuristic"))
                .andExpect(jsonPath("$.decisions[0]").value("ship the beta"))
                .andExpect(jsonPath("$.actionItems.length()").value(1))
                .andExpect(jsonPath("$.actionItems[0].owner").value("Ana"))
                .andExpect(jsonPath("$.actionItems[0].priority").value("HIGH"))
                .andExpect(jsonPath("$.actionItems[0].status").value("OPEN"))
                .andReturn();
    }

    @Test
    void createdMeetingCanBeReadBackAndListed() throws Exception {
        MvcResult created = createMeeting();
        Number id = JsonPath.read(created.getResponse().getContentAsString(), "$.id");

        mvc.perform(get("/api/meetings/" + id.longValue()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Weekly sync"));

        mvc.perform(get("/api/meetings"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].openItems").isNumber());
    }

    @Test
    void statusTransitionsAreEnforced() throws Exception {
        MvcResult created = createMeeting();
        Number itemId = JsonPath.read(created.getResponse().getContentAsString(), "$.actionItems[0].id");
        String url = "/api/action-items/" + itemId.longValue() + "/status";

        mvc.perform(patch(url).contentType(MediaType.APPLICATION_JSON).content("{\"status\":\"DONE\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("DONE"))
                .andExpect(jsonPath("$.allowedStatuses[0]").value("OPEN"));

        mvc.perform(patch(url).contentType(MediaType.APPLICATION_JSON).content("{\"status\":\"IN_PROGRESS\"}"))
                .andExpect(status().isConflict());
    }

    @Test
    void invalidInputIsRejectedWithAProblemResponse() throws Exception {
        mvc.perform(post("/api/meetings").contentType(MediaType.APPLICATION_JSON).content(json("Sync", "   ")))
                .andExpect(status().isBadRequest());
        mvc.perform(patch("/api/action-items/1/status").contentType(MediaType.APPLICATION_JSON).content("{\"status\":\"NOPE\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void unknownMeetingIsNotFound() throws Exception {
        mvc.perform(get("/api/meetings/999999")).andExpect(status().isNotFound());
    }

    @Test
    void deletedMeetingDisappears() throws Exception {
        MvcResult created = createMeeting();
        Number id = JsonPath.read(created.getResponse().getContentAsString(), "$.id");

        mvc.perform(delete("/api/meetings/" + id.longValue())).andExpect(status().isNoContent());
        mvc.perform(get("/api/meetings/" + id.longValue())).andExpect(status().isNotFound());
    }
}
