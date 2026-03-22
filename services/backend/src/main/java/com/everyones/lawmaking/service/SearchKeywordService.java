package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.response.SearchKeywordResponse;
import com.everyones.lawmaking.domain.entity.SearchKeyword;
import com.everyones.lawmaking.domain.entity.User;
import com.everyones.lawmaking.repository.SearchKeywordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class SearchKeywordService {
    private final SearchKeywordRepository searchKeywordRepository;

    // 있으면 추가하고 없으면 넣고
    @Transactional
    public void makeSearchKeyword(User user, String keyWord) {
        var searchKeywordOptional = searchKeywordRepository.findByUserIdAndSearchWord(user.getId(), keyWord);
        if(searchKeywordOptional.isPresent()) {
            updateRecentSearchKeyword(searchKeywordOptional.get());
        } else {
            saveRecentSearchKeyword(user, keyWord);
        }
    }

    public void updateRecentSearchKeyword(SearchKeyword searchKeyword) {
        searchKeyword.setModifiedDate(LocalDateTime.now());
        searchKeywordRepository.save(searchKeyword);

    }

    public void saveRecentSearchKeyword(User user, String keyword) {
        var searchKeyword = SearchKeyword.builder()
                .searchWord(keyword)
                .user(user)
                .modifiedDate(LocalDateTime.now())
                .build();
        searchKeywordRepository.save(searchKeyword);
    }
    @Transactional
    public void removeRecentSearchWord(Long userId, String keyword) {
        searchKeywordRepository.deleteByUserIdAndSearchWord(userId, keyword);
    }

    // 최근 검색어 목록 조회
    public List<SearchKeywordResponse> getRecentSearchWords(Long userId) {
        return searchKeywordRepository.findTop10ByUserIdOrderByModifiedDateDesc(userId).stream()
                .map(SearchKeywordResponse::from)
                .toList();
    }
    public void deleteAllSearchWordsByUserId(Long userId) {
        searchKeywordRepository.deleteAllByUserId(userId);
    }
}
