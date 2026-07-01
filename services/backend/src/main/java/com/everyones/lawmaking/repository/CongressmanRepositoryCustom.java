package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.common.dto.CongressmanRankingDto;
import com.everyones.lawmaking.common.dto.QCongressmanRankingDto;
import com.querydsl.jpa.impl.JPAQueryFactory;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

import static com.everyones.lawmaking.domain.entity.QBillProposer.billProposer;
import static com.everyones.lawmaking.domain.entity.QCongressman.congressman;
import static com.everyones.lawmaking.domain.entity.QParty.party;
import static com.everyones.lawmaking.domain.entity.QRepresentativeProposer.representativeProposer;

@Repository
@RequiredArgsConstructor
public class CongressmanRepositoryCustom {
    private final JPAQueryFactory queryFactory;

    /**
     * 현직 의원을 대표발의 건수 내림차순으로 조회한다. (발의 랭킹 / 의원 리스트 공용)
     * partyId가 주어지면 해당 정당 소속으로 한정한다. hasNext 판별을 위해 호출측에서 limit+1을 넘긴다.
     */
    public List<CongressmanRankingDto> findCongressmanRanking(Long partyId, long offset, long limit) {
        return queryFactory
                .select(new QCongressmanRankingDto(
                        congressman.id,
                        congressman.name,
                        congressman.congressmanImageUrl,
                        party.id,
                        party.name,
                        party.partyImageUrl,
                        representativeProposer.count()))
                .from(representativeProposer)
                .join(representativeProposer.congressman, congressman)
                .join(congressman.party, party)
                .where(
                        congressman.state.isTrue()
                                .and(partyId != null ? party.id.eq(partyId) : null))
                .groupBy(
                        congressman.id,
                        congressman.name,
                        congressman.congressmanImageUrl,
                        party.id,
                        party.name,
                        party.partyImageUrl)
                .orderBy(representativeProposer.count().desc(), congressman.name.asc())
                .offset(offset)
                .limit(limit)
                .fetch();
    }

    public Integer countCongressmanByPartyId(Long partyId, boolean isProportional) {
        Long congressmanCount = queryFactory.select(congressman.count())
                .from(congressman)
                .where(
                        congressman.state.isTrue()
                                .and(congressman.party.id.eq(partyId))
                                .and(isProportional ?
                                        congressman.district.eq("비례대표") :
                                        congressman.district.ne("비례대표"))
                )
                .fetchOne();

        return congressmanCount != null ? congressmanCount.intValue() : 0;
    }
    public LocalDate updateProposeDateByCongressman(String congressmanId) {

        // 서브쿼리 작성
        return queryFactory
                .select(billProposer.bill.proposeDate)
                .from(billProposer)
                .where(billProposer.congressman.id.eq(congressmanId))
                .orderBy(billProposer.bill.proposeDate.desc())
                .fetchFirst();
    }

    }
