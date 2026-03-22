package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.response.SearchDataResponse;
import com.everyones.lawmaking.common.dto.response.SearchBillResponse;
import com.everyones.lawmaking.common.dto.response.SearchKeywordResponse;
import com.everyones.lawmaking.service.CongressmanService;
import com.everyones.lawmaking.service.PartyService;
import com.everyones.lawmaking.service.BillService;
import com.everyones.lawmaking.service.LikeService;
import com.everyones.lawmaking.service.SearchKeywordService;
import com.everyones.lawmaking.global.util.AuthenticationUtil;
import com.everyones.lawmaking.common.dto.response.BillListResponse;
import com.everyones.lawmaking.global.error.UserException;
import com.everyones.lawmaking.service.UserService;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.stream.Stream;

@Service
@RequiredArgsConstructor
public class SearchFacade {
    private final UserService userService;
    private final CongressmanService congressmanService;
    private final PartyService partyService;
    private final BillService billService;
    private final LikeService likeService;
    private final SearchKeywordService searchKeywordService;

    public SearchDataResponse searchCongressmanAndParty(String searchWord) {
        var searchDataResponse = congressmanService.searchCongressman(searchWord);
        var searchPartyList = partyService.searchParty(searchWord);
        searchDataResponse.setSearchResponse(Stream
                .concat(searchDataResponse.getSearchResponse().stream(), searchPartyList.stream())
                .toList());
        return searchDataResponse;
    }

    public SearchBillResponse searchBill(String searchWord, int page) {
        Pageable pageable = PageRequest.of(page, 5);
        var billList = billService.searchBill(searchWord, pageable);
        var billListByUser = setBillListResponseBookMark(billList);
        return SearchBillResponse.builder()
                .paginationResponse(billList.getPaginationResponse())
                .searchResponse(billListByUser.getBillList())
                .build();
    }

    public List<SearchKeywordResponse> getRecentSearchWords() {
        var userId = AuthenticationUtil.getUserId()
                .orElseThrow(UserException.UserNotFoundException::new);
        return searchKeywordService.getRecentSearchWords(userId);
    }

    public void makeSearchKeywordAndGetRecentSearchWords(String keyword) {
        var userId = AuthenticationUtil.getUserId()
                .orElseThrow(UserException.UserNotFoundException::new);
        var user = userService.findById(userId);
        searchKeywordService.makeSearchKeyword(user, keyword);
    }

    public void removeRecentSearchWord(String keyword) {
        var userId = AuthenticationUtil.getUserId()
                .orElseThrow(UserException.UserNotFoundException::new);
        searchKeywordService.removeRecentSearchWord(userId, keyword);
    }

    private BillListResponse setBillListResponseBookMark(BillListResponse billListResponse) {
        var userId = AuthenticationUtil.getUserId();
        if (userId.isEmpty()) {
            return billListResponse;
        }
        var billList = billListResponse.getBillList().stream()
                .map(billDto -> {
                    var isBookMark = likeService.getBillLikeChecked(billDto.getBillInfoDto().getBillId(), userId.get());
                    billDto.setIsBookMark(isBookMark);
                    return billDto;
                })
                .toList();
        billListResponse.setBillList(billList);
        return billListResponse;
    }
} 