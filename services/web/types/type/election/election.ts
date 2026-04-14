import { ELECTION_FAMILY, ELECTION_STATUS, ELECTION_UI_TEMPLATE, ELECTION_VIEW_MODE } from '@/constants';
import { ValueOf } from '@/types/helper';

export type ElectionFamily = ValueOf<typeof ELECTION_FAMILY>;
export type ElectionStatus = ValueOf<typeof ELECTION_STATUS>;
export type ElectionId = string;
export type ElectionCandidateId = string;
export type ElectionRegionCode = string;
export type ElectionRegionType = 'COUNTY' | 'DISTRICT' | 'PROVINCE' | 'NATIONAL';
export type ElectionRegionResolveState =
  | 'idle'
  | 'requesting-permission'
  | 'manual-required'
  | 'gps-suggested'
  | 'confirmed';
export type ElectionPermissionStatus = 'idle' | 'denied' | 'granted' | 'prompt';
export type ElectionViewMode = ValueOf<typeof ELECTION_VIEW_MODE>;

export interface ElectionSelectorResponse {
  default_election_id: ElectionId;
  elections: ElectionSelectorItem[];
}

export interface ElectionSelectorItem {
  election_id: ElectionId;
  election_name: string;
  election_date: string;
  upcoming: boolean;
}

export interface ElectionOverviewResponse {
  selected_election_id: ElectionId;
  ui_template: ElectionUiTemplate;
  default_result_card: ElectionResultCardResponse;
}

export interface ElectionResultCardResponse {
  source_election_id: ElectionId;
  region_type: ElectionRegionType;
  region_code: ElectionRegionCode;
  title: string;
}

export interface ElectionMapResponse {
  selected_election_id: ElectionId;
  depth: ElectionRegionType;
  region_code: ElectionRegionCode;
  view_mode: ElectionViewMode;
  regions: ElectionMapRegion[];
}

export interface ElectionMapRegion {
  region_code: ElectionRegionCode;
  region_name: string;
  value: string;
}

export interface ElectionRegionPanelResponse {
  selected_election_id: ElectionId;
  depth: ElectionRegionType;
  region_code: ElectionRegionCode;
  office_type: string | null;
  region_name: string;
  result_card: ElectionResultCardResponse;
}

export interface ElectionCandidateListResponse {
  selected_election_id: ElectionId;
  region_code: ElectionRegionCode;
  office_type: string | null;
  candidates: ElectionCandidateSummary[];
}

export interface ElectionCandidateSummary {
  candidate_id: ElectionCandidateId;
  candidate_name: string;
  party_name: string;
  candidate_image_url: string;
  giho?: string | null;
  status?: string | null;
  candidate_type?: string | null;
}

export interface ElectionCandidateDetailResponse {
  selected_election_id: ElectionId;
  candidate_id: ElectionCandidateId;
  candidate_name: string;
  party_name: string;
  candidate_image_url: string;
  gender?: string | null;
  age?: number | null;
  edu?: string | null;
  job?: string | null;
  career1?: string | null;
  career2?: string | null;
  sgg_name?: string | null;
  sd_name?: string | null;
  giho?: string | null;
  status?: string | null;
  candidate_type?: string | null;
  manifesto_summary: string | null;
  manifesto_items: ElectionCandidateManifestoItem[];
}

export interface ElectionCandidateManifestoItem {
  order?: number | null;
  title?: string | null;
  content?: string | null;
}

export interface ElectionPollOverviewResponse {
  leading_party: ElectionPollLeadingParty | null;
  party_trend: ElectionPollTrendPoint[];
  latest_surveys: ElectionPollLatestSurvey[];
}

export interface ElectionPollLeadingParty {
  party_name: string;
  percentage: number;
  runner_up_party: string | null;
  gap: number;
  undecided: number;
}

export interface ElectionPollTrendPoint {
  survey: ElectionPollSurveyReference;
  snapshot: ElectionPollSnapshotItem[];
}

export interface ElectionPollSurveyReference {
  registration_number: string;
  pollster: string;
  survey_end_date: string;
}

export interface ElectionPollSnapshotItem {
  party_name: string;
  percentage: number;
}

export interface ElectionPollLatestSurvey {
  registration_number: string;
  pollster: string;
  sponsor: string;
  survey_end_date: string;
  sample_size: number;
  margin_of_error: string;
  question_title: string;
  snapshot: ElectionPollSnapshotItem[];
}

export interface ElectionPollPartyResponse {
  selected_party: string;
  trend_series: ElectionPollPartyTrendPoint[];
  regional_distribution: ElectionPollRegionalDistributionItem[];
}

export interface ElectionPollPartyTrendPoint {
  survey: ElectionPollSurveyReference;
  percentage: number;
}

export interface ElectionPollRegionalDistributionItem {
  region_name: string;
  percentage: number;
}

export interface ElectionPollRegionResponse {
  region_name: string;
  party_snapshot: ElectionPollSnapshotItem[];
  candidate_snapshot: ElectionPollRegionCandidateSnapshot[];
  latest_surveys: ElectionPollRegionSurveySummary[];
}

export interface ElectionPollRegionSurveySummary {
  registration_number: string;
  pollster: string;
  sponsor: string;
  survey_end_date: string;
  sample_size: number;
  margin_of_error: string;
  question_title: string;
}

export interface ElectionPollRegionCandidateSnapshot {
  candidate_name: string;
  percentage: number;
}

export interface ElectionPollCandidateResponse {
  selected_candidate: string | null;
  basis_question_kind: string | null;
  candidate_options: string[];
  series: ElectionPollCandidateTrendPoint[];
  comparison_series: ElectionPollCandidateSeries[];
  latest_snapshot: ElectionPollRegionCandidateSnapshot[];
}

export interface ElectionPollCandidateTrendPoint {
  survey: ElectionPollSurveyReference;
  percentage: number;
}

export interface ElectionPollCandidateSeries {
  candidate_name: string;
  series: ElectionPollCandidateTrendPoint[];
}

export type ElectionQueryContract = {
  selectorKey: readonly ['/election', 'selector'];
  candidateDetailKey: readonly ['/election', 'candidate-detail', ElectionId, ElectionCandidateId];
  resolveRequest: ElectionRegionResolveRequest;
  resolveResponseState: ElectionRegionResolveState;
};

export interface ElectionRegionResolveRequest {
  election_id: ElectionId;
  latitude?: number | null;
  longitude?: number | null;
  region_code?: ElectionRegionCode | null;
  region_type?: ElectionRegionType | null;
  region_name?: string | null;
  permission_status?: ElectionPermissionStatus | null;
}

export interface ElectionRegionResolveResponse {
  election_id: ElectionId;
  state: ElectionRegionResolveState;
  confirmation_required: boolean;
  suggested_region_type: ElectionRegionType | null;
  suggested_region_code: ElectionRegionCode | null;
  suggested_region_name: string | null;
  manual_correction_available: boolean;
  deny_available: boolean;
}

export type ElectionUiTemplate = ValueOf<typeof ELECTION_UI_TEMPLATE>;
