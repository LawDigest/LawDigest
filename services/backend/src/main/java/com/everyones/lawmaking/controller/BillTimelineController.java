package com.everyones.lawmaking.controller;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

import com.everyones.lawmaking.common.dto.response.BillStateCountResponse;
import com.everyones.lawmaking.common.dto.response.BillTimelinePaginationResponse;
import com.everyones.lawmaking.common.dto.response.BillTimelineResponse;
import com.everyones.lawmaking.facade.BillFacade;
import com.everyones.lawmaking.facade.TimelineFacade;
import com.everyones.lawmaking.global.BaseResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.time.LocalDate;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/v1/time-line")
@Tag(name = "법안 타임라인 API", description = "법안 타임라인 API")
public class BillTimelineController {
    private final TimelineFacade timelineFacade;
    private final BillFacade billFacade;

    @Operation(summary = "타임라인 피드 조회", description = "타임라인에 들어갈 데이터를 가져옵니다.")
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
    @Deprecated
    @GetMapping("/feed")
    public BaseResponse<BillTimelineResponse> getTimeline(
            @Parameter(example = "2024-08-02", description = "날짜별 법안 조회")
            @RequestParam(value = "billProposeDate", required = false)
            @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate billProposeDate
    ) {
        if (billProposeDate == null) {
            billProposeDate = LocalDate.now();
        }
        var result = timelineFacade.getTimeline(billProposeDate);
        return BaseResponse.ok(result);
    }
    @GetMapping("/feed/paging")
    public BaseResponse<BillTimelinePaginationResponse> getTimelinePaging(
            @Parameter(example = "0", description = "페이지 넘버")
            @RequestParam(value = "page") int page,
            @Parameter(example = "2", description = "불러올 날짜 개수")
            @RequestParam(value = "size") int size
    ) {
        var pageable = PageRequest.of(page, size);
        var result = timelineFacade.getTimeline(pageable);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "타임라인 법안 단계별 카운트 조회", description = "타임라인 법안 단계별 카운트 조회 API입니다.")
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
    @GetMapping("/bill-state")
    public BaseResponse<BillStateCountResponse> getBillStateCount() {
        var result = billFacade.getBillStateCount();
        return BaseResponse.ok(result);
    }
}
