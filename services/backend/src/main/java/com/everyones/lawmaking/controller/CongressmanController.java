package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.BillListResponse;
import com.everyones.lawmaking.common.dto.response.CongressmanLikeResponse;
import com.everyones.lawmaking.common.dto.response.CongressmanResponse;
import com.everyones.lawmaking.facade.CongressmanFacade;
import com.everyones.lawmaking.facade.BillFacade;
import com.everyones.lawmaking.facade.LikeFacade;
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
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

@RequiredArgsConstructor
@RestController
@RequestMapping("/v1/congressman")
@Tag(name="의원 관련 조회 API", description = "의원 관련 데이터를 가져오는 API입니다.")
public class CongressmanController {
    private final CongressmanFacade congressmanFacade;
    private final BillFacade billFacade;
    private final LikeFacade likeFacade;

    @Operation(summary = "의원 상세 조회", description = "의원 상세페이지에 들어갈 데이터를 가져옵니다.")
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
    @GetMapping("/detail")
    public BaseResponse<CongressmanResponse> getCongressmanDetails(
            @Parameter(example = "0PK7354M", description = "의원 Id")
            @RequestParam("congressman_id") String congressmanId) {
        var congressmanDto = congressmanFacade.getCongressman(congressmanId);
        return BaseResponse.ok(congressmanDto);
    }

    @Operation(summary = "의원의 발의안 리스트 조회", description = "의원이 발의한 법안 데이터 조회")
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
    @GetMapping("/bill_info")
    public BaseResponse<BillListResponse> getCongressmanBills(
            @Parameter(example = "0PK7354M", description = "의원 Id")
            @RequestParam("congressman_id") String congressmanId,
            @Parameter(example = "represent_proposer", description = "해당 의원의 법안 대표 발의 기준, 공동 발의 기준 여부")
            @Schema(type = "String", allowableValues = {"represent_proposer", "public_proposer"})
            @RequestParam("type") String type,
            @Parameter(example = "위원회 심사")
            @RequestParam(value = "stage", required = false) String stage,
            @Parameter(example = "0")
            @RequestParam("page") int page,
            @Parameter(example = "3")
            @RequestParam("size") int size) {
        Pageable pageable = PageRequest.of(page, size);
        if (type.equals("represent_proposer")) {
            var representativeBills = billFacade.getBillsFromRepresentativeProposer(congressmanId, pageable, stage);
            return BaseResponse.ok(representativeBills);
        }
        var publicProposerBills = billFacade.getBillsFromPublicProposer(congressmanId, pageable, stage);
        return BaseResponse.ok(publicProposerBills);
    }

    @Operation(summary = "의원 좋아요", description = "의원이 좋아요 클릭")
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
    @PatchMapping("/user/like")
    public BaseResponse<CongressmanLikeResponse> likeCongressman(
            Authentication authentication,
            @Parameter(example = "04T3751T", description = "의원 Id")
            @RequestParam("congressman_id") String congressmanId,
            @Schema(type = "boolean", allowableValues = {"true", "false"})
            @RequestParam("like_checked") boolean likeChecked
    ) {
        var userDetails = (UserDetails) authentication.getPrincipal();
        var userId = Long.parseLong(userDetails.getUsername());
        var result = likeFacade.likeCongressman(userId, congressmanId, likeChecked);
        return BaseResponse.ok(result);
    }
}
