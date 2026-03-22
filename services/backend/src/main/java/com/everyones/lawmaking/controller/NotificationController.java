package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.NotificationCountResponse;
import com.everyones.lawmaking.common.dto.response.NotificationResponse;
import com.everyones.lawmaking.facade.NotificationFacade;
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
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

@RestController
@RequiredArgsConstructor
@RequestMapping("/v1/notification/user")
@Tag(name="알림 관련 API", description = "알림 조회 및 생성 삭제 기능 포함")
public class NotificationController {
    private final NotificationFacade notificationFacade;

    @Operation(summary = "알림 조회 API", description = "발송 되지 않았고 읽지 않은 알림을 조회한다.")
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
    @GetMapping("")
    public BaseResponse<List<NotificationResponse>> getNotifications(Authentication authentication) {
        final UserDetails user = (UserDetails) authentication.getPrincipal();
        var result = notificationFacade.getNotifications(Long.parseLong(user.getUsername()));
        return BaseResponse.ok(result);
    }

    @GetMapping("/top3-unread")
    public BaseResponse<List<NotificationResponse>> getTop3UnreadNotifications(Authentication authentication) {
        final UserDetails user = (UserDetails) authentication.getPrincipal();
        var result = notificationFacade.getTop3UnreadNotifications(Long.parseLong(user.getUsername()));
        return BaseResponse.ok(result);
    }

    @Operation(summary = "알림 읽음 처리 API", description = "모든 알림을 읽음 처리")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "읽음 성공"),
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
    @PutMapping("/read/all")
    public BaseResponse<List<NotificationResponse>> readAllNotifications(Authentication authentication) {
        final UserDetails user = (UserDetails) authentication.getPrincipal();
        var result = notificationFacade.readAllNotifications(Long.parseLong(user.getUsername()));
        return BaseResponse.ok(result);
    }

    @Operation(summary = "알림 읽음 처리 API", description = "특정 알림을 읽음 처리")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "읽음 성공"),
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
    @PutMapping("/read")
    public BaseResponse<NotificationResponse> readNotification(Authentication authentication,
             @Parameter(example = "3", description = "읽음 처리할 알림id를 의미합니다.")
             @RequestParam(name = "notification_id") int notificationId) {
        final UserDetails user = (UserDetails) authentication.getPrincipal();
        var result = notificationFacade.readNotification(Long.parseLong(user.getUsername()), notificationId);
        return BaseResponse.ok(result.get(0));
    }

    @Operation(summary = "알림 삭제 처리 API", description = "모든 알림을 삭제 처리")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "읽음 성공"),
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
    @DeleteMapping("/delete/all")
    public BaseResponse<String> deleteAllNotification(Authentication authentication) {
        final UserDetails user = (UserDetails) authentication.getPrincipal();
        var result = notificationFacade.deleteAllNotification(Long.parseLong(user.getUsername()));
        return BaseResponse.ok(result);
    }

    @Operation(summary = "알림 삭제 처리 API", description = "특정 알림을 삭제 처리")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "읽음 성공"),
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
    @DeleteMapping("/delete")
    public BaseResponse<String> deleteNotification(Authentication authentication,
           @Parameter(example = "3", description = "읽음 처리할 알림id를 의미합니다.")
           @RequestParam(name = "notification_id") int notificationId) {
        final UserDetails user = (UserDetails) authentication.getPrincipal();
        var result = notificationFacade.deleteNotification(Long.parseLong(user.getUsername()),notificationId);
        return BaseResponse.ok(result);
    }


    @Operation(summary = "새 알림 개수 조회 API", description = "알림 개수를 조회합니다.")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "읽음 성공"),
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
    @GetMapping("/count")
    public BaseResponse<NotificationCountResponse> countNotifications(Authentication authentication) {
        final UserDetails user = (UserDetails) authentication.getPrincipal();
        var result = notificationFacade.countNotifications(Long.parseLong(user.getUsername()));
        return BaseResponse.ok(result);
    }

}
