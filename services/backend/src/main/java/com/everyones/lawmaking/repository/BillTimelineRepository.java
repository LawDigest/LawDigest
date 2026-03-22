package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.domain.entity.BillTimeline;
import jakarta.persistence.Tuple;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface BillTimelineRepository extends JpaRepository<BillTimeline,Long> {

    @Query("select bt.id from BillTimeline bt " +
            "where bt.bill.id =:billId and bt.billTimelineCommittee=:billTimelineCommittee and bt.billTimelineStage=:billTimelineStage and bt.statusUpdateDate=:statusUpdateDate")
    Optional<String> findBillTimelineByInfo(@Param("billId") String billId,
                                                  @Param("billTimelineStage") String billTimelineStage,
                                                  @Param("billTimelineCommittee") String billTimelineCommittee,
                                                  @Param("statusUpdateDate") LocalDate statusUpdateDate);

    // TODO: Grouping + Group_concat QueryDSL로 많이 사용하는 것 같아서 해당 부분 QueryDSL로 교체 요망
    @Query(value = "SELECT bill_timeline_committee AS committee, GROUP_CONCAT(bill_id) AS billIds " +
            "FROM BillTimeline " +
            "WHERE bill_timeline_stage = '위원회 심사' and status_update_date = :proposeDate " +
            "GROUP BY bill_timeline_committee " +
            "HAVING COUNT(DISTINCT bill_id) >= 1",
            nativeQuery = true)
    List<Tuple> findCommitteesWithMultipleBills(@Param("proposeDate") LocalDate proposeDate);

    @Query("select tl.bill.id from BillTimeline tl " +
            "where tl.statusUpdateDate = :proposeDate and tl.billTimelineStage = :stage " +
            "order by case tl.billResult " +
            "    when '원안가결' then 1 " +
            "    when '수정가결' then 2 " +
            "    when '철회' then 3 " +
            "    when '대안반영폐기' then 4 " +
            "    else 5 " +
            "end")
    List<String> findBillTimelineBetweenProposeDateAndStage(@Param("proposeDate") LocalDate localDate, @Param("stage") String stage);

    List<BillTimeline> findByBillIdAndBillTimelineStageAndBillResult(String bill_id, String billTimelineStage, String billResult);

    @Query("SELECT DISTINCT bl.statusUpdateDate FROM BillTimeline bl " +
            "ORDER BY bl.statusUpdateDate DESC")
    Slice<LocalDate> findTopProposeDates(Pageable pageable);

    LocalDate findTopByOrderByStatusUpdateDateDesc();

    @Query("SELECT bt.billResult " +
            "FROM BillTimeline bt " +
            "WHERE bt.bill.id = :billId " +
            "ORDER BY bt.statusUpdateDate DESC " +
            "limit 1 ")
    String findTopByBillIdOrderByStatusUpdateDateDesc(String billId);

}
