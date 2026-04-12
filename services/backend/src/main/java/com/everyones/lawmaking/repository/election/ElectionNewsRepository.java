package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionNews;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface ElectionNewsRepository extends JpaRepository<ElectionNews, Long> {

    @Query("""
            SELECT n FROM ElectionNews n
            WHERE n.electionId = :electionId
            ORDER BY n.pubDate DESC, n.id DESC
            """)
    List<ElectionNews> findFeedItemsFirst(
            @Param("electionId") String electionId,
            Pageable pageable);

    @Query("""
            SELECT n FROM ElectionNews n
            WHERE n.electionId = :electionId
              AND (n.pubDate < :cursorDate
                   OR (n.pubDate = :cursorDate AND n.id < :cursorId))
            ORDER BY n.pubDate DESC, n.id DESC
            """)
    List<ElectionNews> findFeedItems(
            @Param("electionId") String electionId,
            @Param("cursorDate") LocalDateTime cursorDate,
            @Param("cursorId") Long cursorId,
            Pageable pageable);
}
