package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.BillListResponse;
import com.everyones.lawmaking.common.dto.response.LikingCongressmanResponse;
import com.everyones.lawmaking.facade.CongressmanFacade;
import com.everyones.lawmaking.facade.BillFacade;
import com.everyones.lawmaking.global.BaseResponse;
import com.everyones.lawmaking.global.error.UserException;
import com.everyones.lawmaking.global.util.AuthenticationUtil;
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
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

@RequiredArgsConstructor
@RestController
@RequestMapping("/v1/following-tab")
@Tag(name = "팔로잉탭 API", description = "팔로잉 탭 API")
public class FollowingTabController {
    private final CongressmanFacade congressmanFacade;
    private final BillFacade billFacade;

    @Operation(summary = "팔로잉 탭의 법안 조회", description = "팔로우한 의원의 목록을 최근 발의 순으로 가져옵니다..")
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
    @GetMapping("/congressman")
    public BaseResponse<List<LikingCongressmanResponse>> getCongressman() {
        var userId = AuthenticationUtil.getUserId();
        if (userId.isEmpty()) {
            throw new UserException.UserNotFoundException();
        }
        var result = congressmanFacade.getLikingCongressman(userId.get());
        return BaseResponse.ok(result);
    }

    @Operation(summary = "팔로잉 탭의 법안 조회", description = "팔로우 한 의원의 대표발의안을 최신순으로 가져옵니다.")
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
    @GetMapping("/bill")
    public BaseResponse<BillListResponse> getBills(
            @Parameter(example = "0", description = "스크롤할 때마다 page값을 0에서 1씩 늘려주면 됩니다.")
            @RequestParam(name = "page") int page,
            @Parameter(example = "3", description = "한번에 가져올 데이터 크기를 의미합니다.")
            int size
    ) {
        var pageable = PageRequest.of(page, size);
        var result = billFacade.getBillsFromFollowingTab(pageable);
        return BaseResponse.ok(result);
    }
}
