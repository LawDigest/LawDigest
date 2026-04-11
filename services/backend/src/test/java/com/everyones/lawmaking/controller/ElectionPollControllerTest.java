package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.election.ElectionPollCandidateResponse;
import com.everyones.lawmaking.common.dto.response.election.ElectionPollOverviewResponse;
import com.everyones.lawmaking.common.dto.response.election.ElectionPollPartyResponse;
import com.everyones.lawmaking.common.dto.response.election.ElectionPollRegionResponse;
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

    @Test
    void returnsPartyPayloadForPollEndpoint() throws Exception {
        ElectionService electionService = mock(ElectionService.class);
        PollQueryService pollQueryService = mock(PollQueryService.class);
        ElectionController controller = new ElectionController(electionService, pollQueryService);
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(controller).build();

        when(pollQueryService.getParty("local-2026", "더불어민주당"))
                .thenReturn(ElectionPollPartyResponse.builder()
                        .selectedParty("더불어민주당")
                        .trendSeries(List.of(
                                ElectionPollPartyResponse.TrendPoint.builder()
                                        .survey(ElectionPollPartyResponse.SurveyReference.builder()
                                                .registrationNumber("서울-002")
                                                .pollster("한국리서치")
                                                .surveyEndDate(LocalDate.of(2026, 4, 2))
                                                .build())
                                        .percentage(new BigDecimal("42.50"))
                                        .build()
                        ))
                        .regionalDistribution(List.of(
                                ElectionPollPartyResponse.RegionalDistributionItem.builder()
                                        .regionName("서울특별시 전체")
                                        .percentage(new BigDecimal("42.50"))
                                        .build()
                        ))
                        .build());

        mockMvc.perform(get("/v1/election/polls/party")
                        .param("election_id", "local-2026")
                        .param("party_name", "더불어민주당"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.selected_party").value("더불어민주당"))
                .andExpect(jsonPath("$.data.trend_series[0].survey.registration_number").value("서울-002"))
                .andExpect(jsonPath("$.data.regional_distribution[0].region_name").value("서울특별시 전체"))
                .andExpect(jsonPath("$.data.regional_distribution[0].percentage").value(42.50));
    }

    @Test
    void returnsRegionPayloadForPollEndpoint() throws Exception {
        ElectionService electionService = mock(ElectionService.class);
        PollQueryService pollQueryService = mock(PollQueryService.class);
        ElectionController controller = new ElectionController(electionService, pollQueryService);
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(controller).build();

        when(pollQueryService.getRegion("local-2026", "11"))
                .thenReturn(ElectionPollRegionResponse.builder()
                        .regionName("서울특별시 전체")
                        .partySnapshot(List.of(
                                ElectionPollRegionResponse.PartySnapshot.builder()
                                        .partyName("더불어민주당")
                                        .percentage(new BigDecimal("42.50"))
                                        .build()
                        ))
                        .candidateSnapshot(List.of(
                                ElectionPollRegionResponse.CandidateSnapshot.builder()
                                        .candidateName("김동연")
                                        .percentage(new BigDecimal("45.10"))
                                        .build()
                        ))
                        .latestSurveys(List.of(
                                ElectionPollRegionResponse.SurveySummary.builder()
                                        .registrationNumber("서울-002")
                                        .pollster("한국리서치")
                                        .surveyEndDate(LocalDate.of(2026, 4, 2))
                                        .build()
                        ))
                        .build());

        mockMvc.perform(get("/v1/election/polls/region")
                        .param("election_id", "local-2026")
                        .param("region_code", "11"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.region_name").value("서울특별시 전체"))
                .andExpect(jsonPath("$.data.party_snapshot[0].party_name").value("더불어민주당"))
                .andExpect(jsonPath("$.data.candidate_snapshot[0].candidate_name").value("김동연"))
                .andExpect(jsonPath("$.data.latest_surveys[0].registration_number").value("서울-002"));
    }

    @Test
    void returnsCandidatePayloadForPollEndpoint() throws Exception {
        ElectionService electionService = mock(ElectionService.class);
        PollQueryService pollQueryService = mock(PollQueryService.class);
        ElectionController controller = new ElectionController(electionService, pollQueryService);
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(controller).build();

        when(pollQueryService.getCandidate("local-2026", "11", "김동연"))
                .thenReturn(ElectionPollCandidateResponse.builder()
                        .selectedCandidate("김동연")
                        .basisQuestionKind("MATCHUP")
                        .candidateOptions(List.of("김동연", "양향자"))
                        .series(List.of(
                                ElectionPollCandidateResponse.CandidateTrendPoint.builder()
                                        .survey(ElectionPollCandidateResponse.SurveyReference.builder()
                                                .registrationNumber("서울-002")
                                                .pollster("한국리서치")
                                                .surveyEndDate(LocalDate.of(2026, 4, 2))
                                                .build())
                                        .percentage(new BigDecimal("45.10"))
                                        .build()
                        ))
                        .comparisonSeries(List.of(
                                ElectionPollCandidateResponse.CandidateSeries.builder()
                                        .candidateName("양향자")
                                        .series(List.of(
                                                ElectionPollCandidateResponse.CandidateTrendPoint.builder()
                                                        .survey(ElectionPollCandidateResponse.SurveyReference.builder()
                                                                .registrationNumber("서울-002")
                                                                .pollster("한국리서치")
                                                                .surveyEndDate(LocalDate.of(2026, 4, 2))
                                                                .build())
                                                        .percentage(new BigDecimal("39.20"))
                                                        .build()
                                        ))
                                        .build()
                        ))
                        .latestSnapshot(List.of(
                                ElectionPollCandidateResponse.CandidateSnapshot.builder()
                                        .candidateName("김동연")
                                        .percentage(new BigDecimal("45.10"))
                                        .build()
                        ))
                        .build());

        mockMvc.perform(get("/v1/election/polls/candidate")
                        .param("election_id", "local-2026")
                        .param("region_code", "11")
                        .param("candidate_name", "김동연"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.selected_candidate").value("김동연"))
                .andExpect(jsonPath("$.data.basis_question_kind").value("MATCHUP"))
                .andExpect(jsonPath("$.data.candidate_options[1]").value("양향자"))
                .andExpect(jsonPath("$.data.comparison_series[0].candidate_name").value("양향자"));
    }
}
