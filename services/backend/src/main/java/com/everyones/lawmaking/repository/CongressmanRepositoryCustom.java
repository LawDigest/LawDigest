package com.everyones.lawmaking.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;

import static com.everyones.lawmaking.domain.entity.QBillProposer.billProposer;
import static com.everyones.lawmaking.domain.entity.QCongressman.congressman;

@Repository
@RequiredArgsConstructor
public class CongressmanRepositoryCustom {
    private final JPAQueryFactory queryFactory;

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
