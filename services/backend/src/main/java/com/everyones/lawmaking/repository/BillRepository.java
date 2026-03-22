package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.common.dto.response.BillStateCountResponse;
import com.everyones.lawmaking.domain.entity.Bill;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface BillRepository extends JpaRepository<Bill, String>, BillRepositoryCustom{


    // 특정 의원이 대표 발의한 법안들
    @Query("SELECT b FROM Bill b " +
            "WHERE exists (select rp FROM b.representativeProposer rp where rp.congressman.id = :congressmanId) " +
            "ORDER BY b.proposeDate desc, b.id desc")
    Slice<Bill> findByRepresentativeProposer(String congressmanId, Pageable pageable);

    @Query("SELECT b FROM Bill b " +
            "WHERE exists (select rp FROM b.representativeProposer rp where rp.congressman.id = :congressmanId) " +
            "AND b.stage = :stage " +
            "ORDER BY b.proposeDate desc, b.id desc")
    Slice<Bill> findByRepresentativeProposer(String congressmanId, Pageable pageable, String stage);

    // 특정의원이 공동 발의한 법안들
    @Query("SELECT b " +
            "FROM Bill b " +
            "WHERE b.id IN (" +
            "    SELECT DISTINCT bp.bill.id " +
            "    FROM BillProposer bp " +
            "    WHERE bp.congressman.id = :congressmanId" +
            ") " +
            "ORDER BY b.proposeDate DESC")
    Slice<Bill> findBillByPublicProposer(String congressmanId, Pageable pageable);

    @Query("SELECT b FROM Bill b " +
            "WHERE exists (select bp FROM b.publicProposer bp where bp.congressman.id = :congressmanId) " +
            "AND b.stage = :stage " +
            "ORDER BY b.proposeDate desc, b.id desc")
    Slice<Bill> findBillByPublicProposer(String congressmanId, Pageable pageable, String stage);

    // 정당 소속 의원들이 대표 발의한 법안
    @Query("SELECT b FROM Bill b " +
            "WHERE exists (select rp FROM b.representativeProposer rp where rp.congressman.party.id = :partyId) " +
            "ORDER BY b.proposeDate DESC, b.id DESC")
    Slice<Bill> findRepresentativeBillsByParty(Pageable pageable, @Param("partyId") long partyId);

    @Query("SELECT b FROM Bill b " +
            "WHERE exists (select rp FROM b.representativeProposer rp where rp.congressman.party.id = :partyId) " +
            "AND b.stage = :stage " +
            "ORDER BY b.proposeDate DESC, b.id DESC")
    Slice<Bill> findRepresentativeBillsByParty(Pageable pageable, @Param("partyId") long partyId,@Param("stage") String stage);

    // 정당 소속 의원들이 공동 발의한 법안
    // TODO: 쿼리 개선 필요
    @Query("SELECT distinct b FROM Bill b " +
            "JOIN b.publicProposer bp " +
            "WHERE bp.congressman.party.id = :partyId " +
            "ORDER BY b.proposeDate DESC, b.id DESC")
    Slice<Bill> findPublicBillsByParty(Pageable pageable, @Param("partyId") long partyId);


    @Query("SELECT b FROM Bill b " +
            "WHERE exists (select bp FROM b.publicProposer bp where bp.congressman.party.id = :partyId) " +
            "AND b.stage = :stage " +
            "ORDER BY b.proposeDate DESC, b.id DESC")
    Slice<Bill> findPublicBillsByParty(Pageable pageable, @Param("partyId") long partyId,@Param("stage") String stage);

    // 유저가 스크랩한 법안 페이징해서 가져오는 쿼리
    @Query("SELECT b FROM Bill b " +
            "JOIN b.billLike bl " +
            "JOIN bl.user u " +
            "WHERE u.id = :userId " +
            "ORDER BY bl.createdDate DESC, b.id desc")
    Slice<Bill> findByUserId(Pageable pageable, @Param("userId") long userId);

    // 단일 법안과 관련된 정보 가져오는 쿼리
    Optional<Bill> findBillById(String billId);

    /**
     * TODO: 삭제 예정
     * @deprecated
     * 본래 페이징과 분리하여 fetch join + batch size를 함께 사용하여 가져오려 했으나, 그냥 batch size로 처리
      */

    @Query("SELECT b FROM Bill b " +
            "WHERE b.id in :billList " +
            "ORDER BY b.proposeDate desc, b.id desc")
    List<Bill> findBillInfoByIdList(List<String> billList);

    // 유사한 법안 조회 법안과 같은 이름을 가진 법안 조회
    @Query("SELECT b FROM Bill b " +
            "WHERE b.billName = :billName " +
            "AND b.id != :billId ")
    List<Bill> findSimilarBills(@Param("billName") String billName, @Param("billId") String billId);

    @Query(value = "select bill_id\n" +
            "from\n" +
            "(select bill_id, propose_date, match(bill_name) against(concat('*',:keyword,'*') in boolean mode) as bill_name_rel,\n" +
            "match(brief_summary) against(concat('*',:keyword,'*') in boolean mode) as brief_summary_rel,\n" +
            "match(gpt_summary) against(concat('*',:keyword,'*') in boolean mode) as gpt_summary_rel,\n" +
            "match(summary) against(concat('*',:keyword,'*') in boolean mode) as summary_rel\n" +
            "from Bill) search\n" +
            "where bill_name_rel >0 or brief_summary_rel>0 or gpt_summary_rel>0 or summary_rel > 0\n" +
            "order by propose_date desc, bill_name_rel desc, brief_summary_rel desc, gpt_summary_rel desc, summary_rel desc ;"
            , nativeQuery = true)
    Slice<String> findBillByKeyword(Pageable pageable,@Param("keyword") String keyword);



    @Query("select distinct b from Bill b " +
            "JOIN b.representativeProposer rp " +
            "JOIN rp.congressman c " +
            "JOIN c.congressmanLike cl " +
            "where cl.user.id = :userId " +
            "ORDER BY b.proposeDate desc, b.id desc")
    Slice<Bill> findByUserAndCongressmanLike(Pageable pageable, long userId);

    @Query("SELECT DISTINCT b FROM Bill b " +
            "JOIN FETCH b.representativeProposer rp " +
            "JOIN FETCH rp.congressman c " +
            "JOIN FETCH c.party " +
            "WHERE b.id IN :billIds")
    List<Bill> findBillsWithPartiesByIds(@Param("billIds") List<String> billIds);

    @Query("SELECT new com.everyones.lawmaking.common.dto.response.BillStateCountResponse(" +
            "COUNT(b), " +
            "SUM(CASE WHEN b.stage IN ('위원회 심사', '본회의 심의', '체계자구 심사', '정부이송', '공포') THEN 1 ELSE 0 END), " +
            "SUM(CASE WHEN b.stage IN ('정부이송', '공포') THEN 1 ELSE 0 END)) " +
            "FROM Bill b "+
            "where b.assemblyNumber = :currentAssemblyNumber")
    BillStateCountResponse findStateCount(@Param("currentAssemblyNumber") int currentAssemblyNumber);

}
