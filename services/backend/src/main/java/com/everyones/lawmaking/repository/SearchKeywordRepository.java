package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.SearchKeyword;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SearchKeywordRepository extends JpaRepository<SearchKeyword, Long> {

    // 특정 사용자의 최근 검색어 목록 조회
    List<SearchKeyword> findTop10ByUserIdOrderByModifiedDateDesc(Long userId);

    Optional<SearchKeyword> findByUserIdAndSearchWord(Long userId, String searchWord);

    void deleteByUserIdAndSearchWord(Long userId, String searchWord);

    @Modifying(clearAutomatically = true)
    void deleteAllByUserId(Long userId);


}
