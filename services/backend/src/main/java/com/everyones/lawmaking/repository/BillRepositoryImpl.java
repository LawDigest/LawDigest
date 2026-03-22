package com.everyones.lawmaking.repository;

import static com.everyones.lawmaking.domain.entity.QBill.bill;
import static com.everyones.lawmaking.domain.entity.QBillLike.billLike;
import static com.everyones.lawmaking.domain.entity.QBillProposer.billProposer;
import static com.everyones.lawmaking.domain.entity.QCongressman.congressman;
import static com.everyones.lawmaking.domain.entity.QParty.party;
import static com.everyones.lawmaking.domain.entity.QRepresentativeProposer.representativeProposer;

import com.everyones.lawmaking.common.dto.BillInfoDto;
import com.everyones.lawmaking.common.dto.PublicProposerDto;
import com.everyones.lawmaking.common.dto.QBillInfoDto;
import com.everyones.lawmaking.common.dto.QPublicProposerDto;
import com.everyones.lawmaking.common.dto.bill.BillDto;
import com.everyones.lawmaking.common.dto.proposer.QRepresentativeProposerDto;
import com.everyones.lawmaking.common.dto.proposer.RepresentativeProposerDto;
import com.everyones.lawmaking.common.dto.response.BillListResponse;
import com.everyones.lawmaking.common.dto.response.PaginationResponse;
import com.everyones.lawmaking.global.util.PaginationUtil;
import com.querydsl.core.group.GroupBy;
import com.querydsl.core.types.dsl.BooleanExpression;
import com.querydsl.jpa.impl.JPAQueryFactory;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import org.springframework.util.StringUtils;

/**
 * @version 3
 * @author 강정훈
 */
@Repository
@RequiredArgsConstructor
public class BillRepositoryImpl implements BillRepositoryCustom {
    private final JPAQueryFactory queryFactory;

    @Override
    public BillListResponse findBillWithDetailAndPage(Pageable pageable, Optional<Long> userIdOptional, String stage) {
        var pagedBill = findPagedBills(pageable, stage);
        var billIds = extractBillIds(pagedBill);
        var representativeProposerMap = findRepresentativeProposerMap(billIds);
        var publicProposerMap = findPublicProposerMap(billIds);
        var billLikeMap = checkBillLiked(billIds, userIdOptional);
        var billDtoList = createBillDtoList(pagedBill, representativeProposerMap, publicProposerMap, billLikeMap);
        var pagination = PaginationResponse.of(PaginationUtil.hasNextPage(pagedBill, pageable.getPageSize()), pageable.getPageNumber());
        return BillListResponse.of(pagination, billDtoList);
    }
    private List<BillInfoDto> findPagedBills(Pageable pageable, String stage) {
        return queryFactory.select(new QBillInfoDto(bill))
                .from(bill)
                .where(eqStage(stage))
                .offset(pageable.getOffset())
                .limit(pageable.getPageSize() + 1)
                .orderBy(bill.proposeDate.desc(), bill.id.desc())
                .fetch();
    }
    private BooleanExpression eqStage(String stage) {
        if(StringUtils.hasText(stage)) {
            return bill.stage.eq(stage);
        }
        return null;
    }
    private Map<String, List<RepresentativeProposerDto>> findRepresentativeProposerMap(List<String> billIds) {
        return queryFactory
                .from(representativeProposer)
                .where(representativeProposer.bill.id.in(billIds))
                .join(representativeProposer.congressman, congressman)
                .join(representativeProposer.congressman.party, party)
                .transform(
                        GroupBy.groupBy(representativeProposer.bill.id)
                                .as(GroupBy.list(
                                        new QRepresentativeProposerDto(
                                                congressman.id,
                                                congressman.name,
                                                congressman.congressmanImageUrl,
                                                party.id,
                                                party.name,
                                                party.partyImageUrl
                                        )
                                ))
                );

    }
    private Map<String, List<PublicProposerDto>> findPublicProposerMap(List<String> billIds) {
        return queryFactory
                .from(billProposer)
                .where(billProposer.bill.id.in(billIds))
                .join(billProposer.congressman, congressman)
                .join(billProposer.congressman.party, party)
                .transform(
                        GroupBy.groupBy(billProposer.bill.id)
                                .as(GroupBy.list(
                                        new QPublicProposerDto(
                                                congressman.id,
                                                congressman.name,
                                                congressman.congressmanImageUrl,
                                                party.id,
                                                party.name,
                                                party.partyImageUrl
                                        )
                                ))
                );
    }
    private Map<String, Boolean> checkBillLiked(List<String> billIds, Optional<Long> userIdOptional) {
        if (userIdOptional.isEmpty()) {
            return billIds.stream()
                    .collect(Collectors.toMap(billId -> billId, billId -> false));
        }
        var userId = userIdOptional.get();

        return queryFactory.select(billLike.id, billLike.isNotNull())
                .from(billLike)
                .where(
                        billLike.user.id.eq(userId),
                        billLike.bill.id.in(billIds)
                ).transform(
                        GroupBy.groupBy(billLike.bill.id)
                                .as(billLike.isNotNull())
                );
    }

    private List<String> extractBillIds(List<BillInfoDto> billList) {
        return billList.stream()
                .map(BillInfoDto::getBillId)
                .toList();
    }
    private List<BillDto> createBillDtoList(
            List<BillInfoDto> pagedBills,
            Map<String, List<RepresentativeProposerDto>> representativeProposerMap,
            Map<String, List<PublicProposerDto>> publicProposerMap,
            Map<String, Boolean> billLikeMap
    ) {
        return pagedBills.stream()
                .map(bill -> BillDto.of(
                        bill,
                        representativeProposerMap.getOrDefault(bill.getBillId(), Collections.emptyList()),
                        publicProposerMap.getOrDefault(bill.getBillId(), Collections.emptyList()),
                        billLikeMap.getOrDefault(bill.getBillId(), false)
                ))
                .toList();
    }
}
