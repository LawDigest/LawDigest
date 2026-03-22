package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.*;
import com.everyones.lawmaking.facade.UserFacade;
import com.everyones.lawmaking.facade.PartyFacade;
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
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

@RestController
@RequiredArgsConstructor
@RequestMapping("/v1/user")
@Tag(name = "유저 관련 API", description = "유저 관련 API 호출")
public class UserController {
    private final UserFacade userFacade;
    private final PartyFacade partyFacade;
    private final CongressmanFacade congressmanFacade;
    private final BillFacade billFacade;

    @Operation(summary = "유저 정보 조회", description = "마이 페이지에서 유저의 기본 정보 조회 ")
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
    @GetMapping("/info")
    public BaseResponse<UserMyPageInfoResponse> getUserMyPageInfo(
            Authentication authentication) {
        var userDetails = (UserDetails) authentication.getPrincipal();
        var userId = Long.parseLong(userDetails.getUsername());
        var result = userFacade.getUserMyPageInfo(userId);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "팔로우한 정당 조회", description = "마이 페이지에서 유저가 팔로우한 정당을 조회합니다. ")
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
    @GetMapping("/following/party")
    public BaseResponse<List<FollowingPartyResponse>> getFollowingParty (
            Authentication authentication) {
        var userDetails = (UserDetails) authentication.getPrincipal();
        var userId = Long.parseLong(userDetails.getUsername());
        var result = partyFacade.getFollowingParty(userId);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "팔로우한 의원 조회", description = "마이 페이지에서 유저가 팔로우한 의원을 조회합니다. ")
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
    @GetMapping("/liking/congressman")
    public BaseResponse<List<LikingCongressmanResponse>> getLikingCongressman (
            Authentication authentication) {
        var userDetails = (UserDetails) authentication.getPrincipal();
        var userId = Long.parseLong(userDetails.getUsername());
        var result = congressmanFacade.getLikingCongressman(userId);
        return BaseResponse.ok(result);
    }

    @Operation(summary = "팔로우한 의원 수 반환", description = "마이페이지에서 팔로우한 의원 수 반환")
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
    @GetMapping("/liking/congressman/count")
    public BaseResponse<CountDto> getCongressmanLikeCount() {
        var result = congressmanFacade.getCongressmanLikeCount();
        return BaseResponse.ok(result);
    }

    @Operation(summary = "스크랩한 법안 가져오기", description = "스크랩탭에서 유저가 북마크한 목록 제공 api ")
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
    @GetMapping("/bookmarking/bill")
    public BaseResponse<BillListResponse> getBookmarkedBills(
            @Parameter(example = "0", description = "스크롤할 때마다 page값을 0에서 1씩 늘려주면 됩니다.")
            @RequestParam(name = "page") int page,
            @Parameter(example = "3", description = "한번에 가져올 데이터 크기를 의미합니다.")
            @RequestParam(name = "size") int size
    ) {
        var userId = AuthenticationUtil.getUserId()
                .orElseThrow(UserException.UserNotFoundException::new);
        Pageable pageable = PageRequest.of(page, size);
        var result = billFacade.getBookmarkedBills(pageable, userId);
        return BaseResponse.ok(result);
    }
    @Operation(summary = "스크랩한 법안 수 가져오기", description = "스크랩탭에서 유저가 북마크한 법안 수 제공 api ")
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
    @GetMapping("/bookmarking/bill/count")
    public BaseResponse<CountDto> getBookmarkedBillCount() {
        var result = billFacade.getBookmarkedBillCount();
        return BaseResponse.ok(result);
    }
}
