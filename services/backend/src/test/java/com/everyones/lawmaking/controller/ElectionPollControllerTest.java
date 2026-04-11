package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.election.ElectionPollOverviewResponse;
import com.everyones.lawmaking.service.election.ElectionService;
import com.everyones.lawmaking.service.election.poll.PollQueryService;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class ElectionPollControllerTest {

    @Test
    void returnsOverviewPayloadForPollEndpoint() throws Exception {
        ElectionService electionService = mock(ElectionService.class);
        PollQueryService pollQueryService = mock(PollQueryService.class);
        ElectionController controller = new ElectionController(electionService, pollQueryService);
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(controller).build();

        when(pollQueryService.getOverview("local-2026", "11"))
                .thenReturn(ElectionPollOverviewResponse.builder()
                        .leadingParty(ElectionPollOverviewResponse.LeadingPartyResponse.builder()
                                .partyName("더불어민주당")
                                .percentage(new BigDecimal("42.50"))
                                .undecided(new BigDecimal("15.60"))
                                .build())
                        .partyTrend(List.of(
                                ElectionPollOverviewResponse.PartyTrendPoint.builder()
                                        .survey(ElectionPollOverviewResponse.SurveyReference.builder()
                                                .registrationNumber("서울-002")
                                                .pollster("한국리서치")
                                                .surveyEndDate(LocalDate.of(2026, 4, 2))
                                                .build())
                                        .snapshot(List.of(
                                                ElectionPollOverviewResponse.PartySnapshot.builder()
                                                        .partyName("더불어민주당")
                                                        .percentage(new BigDecimal("42.50"))
                                                        .build(),
                                                ElectionPollOverviewResponse.PartySnapshot.builder()
                                                        .partyName("undecided")
                                                        .percentage(new BigDecimal("15.60"))
                                                        .build()
                                        ))
                                        .build()
                        ))
                        .latestSurveys(List.of(
                                ElectionPollOverviewResponse.LatestSurveyResponse.builder()
                                        .registrationNumber("서울-002")
                                        .pollster("한국리서치")
                                        .surveyEndDate(LocalDate.of(2026, 4, 2))
                                        .snapshot(List.of(
                                                ElectionPollOverviewResponse.PartySnapshot.builder()
                                                        .partyName("더불어민주당")
                                                        .percentage(new BigDecimal("42.50"))
                                                        .build(),
                                                ElectionPollOverviewResponse.PartySnapshot.builder()
                                                        .partyName("undecided")
                                                        .percentage(new BigDecimal("15.60"))
                                                        .build()
                                        ))
                                        .build()
                        ))
                        .build());

        mockMvc.perform(get("/v1/election/polls/overview")
                        .param("election_id", "local-2026")
                        .param("region_code", "11"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.leading_party.party_name").value("더불어민주당"))
                .andExpect(jsonPath("$.data.leading_party.undecided").value(15.60))
                .andExpect(jsonPath("$.data.party_trend[0].survey.registration_number").value("서울-002"))
                .andExpect(jsonPath("$.data.latest_surveys[0].snapshot[1].party_name").value("undecided"))
                .andExpect(jsonPath("$.data.latest_surveys[0].snapshot[1].percentage").value(15.60));
    }
}
