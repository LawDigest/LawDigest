package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.election.ElectionPollOverviewResponse;
import com.everyones.lawmaking.common.dto.response.election.ElectionSelectorResponse;
import com.everyones.lawmaking.service.election.ElectionService;
import com.everyones.lawmaking.service.election.poll.PollQueryService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = "ACTIVE=test")
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ElectionPublicAccessTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ElectionService electionService;

    @MockBean
    private PollQueryService pollQueryService;

    @Test
    void allowsUnauthenticatedSelectorRequest() throws Exception {
        when(electionService.getSelector()).thenReturn(ElectionSelectorResponse.builder()
                .defaultElectionId("local-2026")
                .elections(List.of())
                .build());

        mockMvc.perform(get("/v1/election/selector"))
                .andExpect(status().isOk());
    }

    @Test
    void allowsUnauthenticatedPollOverviewRequest() throws Exception {
        when(pollQueryService.getOverview("local-2026", "11")).thenReturn(ElectionPollOverviewResponse.builder().build());

        mockMvc.perform(get("/v1/election/polls/overview")
                        .param("election_id", "local-2026")
                        .param("region_code", "11"))
                .andExpect(status().isOk());
    }
}
