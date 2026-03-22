package com.everyones.lawmaking.repository;

import com.querydsl.jpa.JPAExpressions;
import com.querydsl.jpa.JPQLQuery;
import com.querydsl.jpa.impl.JPAQueryFactory;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import static com.everyones.lawmaking.domain.entity.QBill.bill;
import static com.everyones.lawmaking.domain.entity.QBillProposer.billProposer;
import static com.everyones.lawmaking.domain.entity.QRepresentativeProposer.representativeProposer;

@Repository
@RequiredArgsConstructor
public class PartyRepositoryCustom {

    private final JPAQueryFactory jpaQueryFactory;

    public Integer countBillCountByPartyId(Long partyId, boolean isRepresentativeProposer) {
        JPQLQuery<Integer> subQuery;

        if (isRepresentativeProposer) {
            subQuery = JPAExpressions
                    .selectOne()
                    .from(representativeProposer)
                    .where(representativeProposer.bill.eq(bill)
                            .and(representativeProposer.congressman.party.id.eq(partyId)));
        } else {
            subQuery = JPAExpressions
                    .selectOne()
                    .from(billProposer)
                    .where(billProposer.bill.eq(bill)
                            .and(billProposer.congressman.party.id.eq(partyId)));

        }

        // 메인 쿼리
        Long count = jpaQueryFactory
                .select(bill.count())
                .from(bill)
                .where(subQuery.exists())
                .fetchOne();

        return count != null ? count.intValue() : 0;

    }
}

