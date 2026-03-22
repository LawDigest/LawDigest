package com.everyones.lawmaking.controller;

import com.everyones.lawmaking.common.dto.response.SearchBillResponse;
import com.everyones.lawmaking.common.dto.response.SearchDataResponse;
import com.everyones.lawmaking.common.dto.response.SearchKeywordResponse;
import com.everyones.lawmaking.facade.SearchFacade;
import com.everyones.lawmaking.global.BaseResponse;
import com.everyones.lawmaking.global.error.BillException;
import com.everyones.lawmaking.global.error.CongressmanException;
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
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

import static com.everyones.lawmaking.global.SwaggerConstants.EXAMPLE_ERROR_500_CONTENT;

@RestController
@RequiredArgsConstructor
@RequestMapping("/v1/search")
@Tag(name="검색 관련 API", description = "의원, 정당 및 법안 검색 API")
public class SearchController {
    private final SearchFacade searchFacade;

    @Operation(summary = "최근 검색어 삽입 API", description = "최근 10개의 검색어를 가져옵니다.")
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
    @PostMapping("/recent-keword")
    public BaseResponse<String> makeRecentKeyword(
            @Parameter(example = "국민", description = "국민의 힘 정당 노리는 검색어")
            @RequestParam("search_word") String searchWord) {
        searchFacade.makeSearchKeywordAndGetRecentSearchWords(searchWord);
        return BaseResponse.ok(searchWord + "업데이트 완료");
    }

    @Operation(summary = "최근 검색어 제공 API", description = "최근 10개의 검색어를 가져옵니다.")
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
    @GetMapping("/recent-keword")
    public BaseResponse<List<SearchKeywordResponse>> getRecentSearchWords() {
        var result = searchFacade.getRecentSearchWords();
        return BaseResponse.ok(result);
    }

    @Operation(summary = "최근 검색어 삭제 API", description = "검색어 삭제 API")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "삭제 성공"),
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
    @DeleteMapping("/recent-keword")
    public BaseResponse<String> removeRecentKeyword(
            @Parameter(example = "국민", description = "국민의 힘 정당 노리는 검색어")
            @RequestParam("search_word") String searchWord) {
        searchFacade.removeRecentSearchWord(searchWord);
        return BaseResponse.ok(searchWord + "가 삭제되었습니다. ");
    }
    // 의원, 정당 검색

    @Operation(summary = "의원 및 정당 검색", description = "의원 또는 정당 탭에서 검색한 결과를 주는 API입니다. ")
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
    @GetMapping("/congressman/party")
    public BaseResponse<SearchDataResponse> searchCongressmanAndParty (
            @Parameter(example = "국민", description = "국민의 힘 정당 노리는 검색어")
            @RequestParam("search_word") String searchWord){

        if(searchWord == null || searchWord.trim().isEmpty()) {
            throw new CongressmanException.SearchParameterInvalid(Map.of("searchWord", searchWord));
        }

        var result = searchFacade.searchCongressmanAndParty(searchWord);
        return BaseResponse.ok(result);

    }

     //법안 검색
    @Operation(summary = "법안 검색", description = "법안을 검색한 결과를 주는 API입니다. ")
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
    public BaseResponse<SearchBillResponse> searchBill (
            @Parameter(example = "소방", description = "소방 관련 법안을 검색하려는 검색어")
            @RequestParam("search_word") String searchWord,
            @Parameter(example = "0", description = "검색 결과 페이징을 위한 페이지 넘버")
            @RequestParam("page") int page) {
        if (searchWord.trim().length()<2){
            throw new BillException.SearchParameterInvalid(Map.of("searchWord", searchWord));
        }
        var result = searchFacade.searchBill(searchWord,page);
        return BaseResponse.ok(result);

    }


}
