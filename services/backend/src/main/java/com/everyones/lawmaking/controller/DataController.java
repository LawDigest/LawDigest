package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.request.*;
import com.everyones.lawmaking.facade.DataFacade;
import com.everyones.lawmaking.global.BaseResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/v1/auto_data_upload")
@Tag(name = "내수용 데이터 API", description = "새로 수집되는 데이터들을 기록하기 위한 API")
public class DataController {
    private final DataFacade dataFacade;

    @Operation(summary = "발의법률안 삽입 요청 API", description = "수집한 발의법률안 삽입 요청한다.")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/bill")
    public BaseResponse<String> insertBill(
            @Parameter(description = "발의법률안 삽입 데이터", required = true)
            @RequestBody BillListDfRequest billListDfRequest) {
        var billDfRequestList = billListDfRequest.getBillRequestList();
        dataFacade.insertBillInfoDf(billDfRequestList);
        return BaseResponse.ok("발의법률안정보 삽입 데이터 요청 성공");
    }

    @Operation(summary = "날짜별 법안 처리상태 변동 수집 데이터 수정 요청 API", description = "날짜별 법안 처리상태 변동 수집 데이터 수정 요청한다.")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/bill/timeline")
    public BaseResponse<Map<String, List<String>>> updateBillStageDf(
            @Parameter(description = "날짜별 법안 처리상태 변동 수집 수정 데이터", required = true)
            @RequestBody BillStageListDfRequest billStageListDfRequest) {
        var billStageDfRequestList = billStageListDfRequest.getBillStageRequestList();
        var result = dataFacade.updateBillStageDf(billStageDfRequestList);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "당일 법안 본회의 처리 결과 수집 수정 요청 API", description = "당일 법안 본회의 처리 결과 수집 수정 요청한다.")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/bill_result")
    public BaseResponse<String> updateBillResultDf(
            @Parameter(description = "당일 법안 본회의 처리 결과 수집 수정 데이터", required = true)
            @RequestBody BillResultListDfRequest billResultListDfRequest) {
        var billDfRequestList=billResultListDfRequest.getBillResultDfRequestList();
        dataFacade.updateBillResultDf(billDfRequestList);
        return BaseResponse.ok("당일 법안 본회의 처리 결과 수집 수정 데이터 요청 성공");
    }

    @Operation(summary = "국회의원 정보 수집 수정 요청 API", description = "국회의원 정보 수집 수정 요청한다.")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/lawmaker")
    public BaseResponse<String> updateLawmakerDf(
            @Parameter(description = "국회의원 정보 수집 삽입 api", required = true)
            @RequestBody LawmakerListDfRequest lawmakerListDfRequest) {
        var lawmakerDfRequestList=lawmakerListDfRequest.getLawmakerDfRequestList();
        dataFacade.updateLawmakerDf(lawmakerDfRequestList);
        return BaseResponse.ok("국회의원 정보 수집 삽입 데이터 요청 성공");
    }

    @Operation(summary = "당일 본회의 투표수 삽입 API", description = "당일 본회의 투표 수를 데이터베이스에 저장")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/vote")
    public BaseResponse<List<String>> insertAssemblyVote(
            @Parameter(description = "당일 본회의 투표수 삽입 API", required = true)
            @RequestBody VoteListRequest voteListRequest) {
        var voteDfRequestList=voteListRequest.getVoteDfRequestList();
        var result = dataFacade.insertAssemblyVote(voteDfRequestList);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "본회의 정당별 투표수 삽입 API", description = "본회의 정당별 투표수 삽입 API 데이터베이스 저장")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/vote/party")
    public BaseResponse<List<String>> insertVoteIndividual(
            @Parameter(description = "본회의 정당별 투표수 삽입 API", required = true)
            @RequestBody VotePartyListRequest votePartyListRequest) {
        var voteDfRequestList=votePartyListRequest.getVotePartyRequestList();
        var result = dataFacade.insertVoteIndividual(voteDfRequestList);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "의원 카운트 업데이트 API", description = "정당별 비례대표, 지역구 의원 카운트 수정")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/congressman/party/count")
    public BaseResponse<String> updateCongressmanCountByParty() {
        dataFacade.updateCongressmanCountByParty();
        return BaseResponse.ok("정당별 의원 카운트 업데이트 성공");
    }

    @Operation(summary = "정당별 법안 카운트 업데이트 API", description = "정당별 법안 카운트 업데이트 수정")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/bill/party/count")
    public BaseResponse<String> updateBillCountByParty() {
        dataFacade.updateBillCountByParty();
        return BaseResponse.ok("정당별 법안 카운트 업데이트 성공");
    }

    @Operation(summary = "의원별 최신 발의날짜 업데이트 API", description = "의원별 최신 발의날짜 수정")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "조회 성공"),
            @ApiResponse(
                    responseCode = "500",
                    description = "서버 오류 (문제 지속시 BE팀 문의)",
                    content = {@Content(
                            mediaType = "application/json;charset=UTF-8",
                            schema = @Schema(implementation = BaseResponse.class),
                            examples = @ExampleObject(value = EXAMPLE_ERROR_500_CONTENT)
                    )}
            ),
    })
    @PostMapping("/bill/congressman/date")
    public BaseResponse<String> updateProposeDateByCongressman() {
        dataFacade.updateProposeDateByCongressman();
        return BaseResponse.ok("의원별 최신 발의날짜 업데이트 성공");
    }
}
