package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.bill.BillDto;
import com.everyones.lawmaking.common.dto.response.BillDetailResponse;
import com.everyones.lawmaking.common.dto.response.BillLikeResponse;
import com.everyones.lawmaking.common.dto.response.BillListResponse;
import com.everyones.lawmaking.common.dto.response.BillViewCountResponse;
import com.everyones.lawmaking.facade.BillFacade;
import com.everyones.lawmaking.facade.LikeFacade;
import com.everyones.lawmaking.global.BaseResponse;
import com.everyones.lawmaking.global.constant.BillStageType;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

@RequiredArgsConstructor
@RestController
@RequestMapping("/v1/bill")
@Tag(name = "법안 API", description = "법안 조회 API")
public class BillController {
    private final BillFacade billFacade;
    private final LikeFacade likeFacade;

    @Operation(summary = "메인피드 조회", description = "메인피드에 들어갈 데이터를 가져옵니다.")
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
    @GetMapping("/mainfeed")
    public BaseResponse<BillListResponse> getBillsFromMainFeed(
            @Parameter(example = "0", description = "스크롤할 때마다 page값을 0에서 1씩 늘려주면 됩니다.")
            @RequestParam(name = "page")
            int page,
            @Parameter(example = "3", description = "한번에 가져올 데이터 크기를 의미합니다.")
            @RequestParam(name = "size")
            int size,
            @Parameter(example = "공포", description = "법안의 단계 현황을 나타냅니다.")
            @Schema(type = "string", allowableValues = {"접수", "위원회심사",
                    "본회의 심의", "공포"})
            @RequestParam(name = "stage", required = false) String stage
            ) {
        var pageable = PageRequest.of(page, size);
        if(StringUtils.hasText(stage) && !BillStageType.containsValue(stage)) {
            throw new IllegalArgumentException(stage);
        }
        var result = billFacade.getBillList(pageable, stage);
        return BaseResponse.ok(result);
    }

    /**
     * 프론트가 새로운 uri(/mainfeed?stage)로 해당 api를 바꾸면 삭제될 예정입니다.
     */
    @Deprecated
    @GetMapping("/mainfeed/stage")
    public BaseResponse<BillListResponse> getBillsByStage(
            @Parameter(example = "0", description = "스크롤할 때마다 page값을 0에서 1씩 늘려주면 됩니다.")
            @RequestParam(name = "page") int page,
            @Parameter(example = "3", description = "한번에 가져올 데이터 크기를 의미합니다.")
            @RequestParam(name = "size") int size,
            @Parameter(example = "공포", description = "법안의 단계 현황을 나타냅니다.")
            @Schema(type = "string", allowableValues = {"접수", "위원회 심사",
                    "본회의 심의","공포"})
            @RequestParam(name = "stage") String stage
    ) {
        var pageable = PageRequest.of(page, size);
        var result = billFacade.getBillList(pageable, stage);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "법안 상세 조회", description = "법안 id로 법안 데이터를 가져옵니다.")
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
    @GetMapping("/detail/{bill_id}")
    public BaseResponse<BillDetailResponse> getBillWithDetail(
            @Parameter(example = "PRC_G2O3O1N2O1M1K1L5A0A8Z2Z2Y7W6X3")
            @PathVariable("bill_id") String billId) {
        var result = billFacade.getBillByBillId(billId);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "법안 조회수 증가", description = "법안 id로 조회수를 증가시킵니다.")
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
    @PatchMapping("/view_count")
    public BaseResponse<BillViewCountResponse> updateViewCount(
            @Parameter(example = "PRC_G2O3O1N2O1M1K1L5A0A8Z2Z2Y7W6X3")
            @RequestParam("bill_id") String billId
    ) {
        var result = billFacade.updateViewCount(billId);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "법안 좋아요", description = "법안 좋아요 기능")
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
    @PatchMapping("/user/bookmark")
    public BaseResponse<BillLikeResponse> likeBill(
            Authentication authentication,
            @Parameter(example = "PRC_G2O3O1N2O1M1K1L5A0A8Z2Z2Y7W6X3")
            @RequestParam("bill_id") String billId,
            @Schema(type = "boolean", allowableValues = {"true", "false"})
            @RequestParam("likeChecked") boolean likeChecked
    ) {
        var userDetails = (UserDetails) authentication.getPrincipal();
        var userId = Long.parseLong(userDetails.getUsername());
        var result = likeFacade.likeBill(userId, billId, likeChecked);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "인기 법안 조회", description = "인기 법안 조회 기능")
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
    @GetMapping("/popular")
    public BaseResponse<List<BillDto>> getPopularBills() {
        var result = billFacade.getPopularBills();
        return BaseResponse.ok(result);
    }
}
