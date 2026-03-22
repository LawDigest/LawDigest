package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.response.NotificationResponse;
import com.everyones.lawmaking.common.dto.response.NotificationCountResponse;
import com.everyones.lawmaking.domain.entity.ColumnEventType;
import com.everyones.lawmaking.domain.entity.ProposerKindType;
import com.everyones.lawmaking.domain.entity.User;
import com.everyones.lawmaking.global.util.NullUtil;
import com.everyones.lawmaking.service.BillService;
import com.everyones.lawmaking.service.CongressmanService;
import com.everyones.lawmaking.service.NotificationService;
import com.everyones.lawmaking.service.PartyService;
import com.everyones.lawmaking.service.UserService;
import java.util.stream.Stream;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class NotificationFacade {
    private final NotificationService notificationService;
    private final UserService userService;
    private final CongressmanService congressmanService;
    private final BillService billService;
    private final PartyService partyService;

    public List<NotificationResponse> getNotifications(long userId){
        return notificationService.getNotifications(userId);
    }

    public List<NotificationResponse> getTop3UnreadNotifications(long userId) {
        return notificationService.getTop3UnreadNotifications(userId);
    }

    public List<NotificationResponse> readAllNotifications(long userId) {
        return notificationService.readNotification(userId, Optional.empty());
    }

    public List<NotificationResponse> readNotification(long userId, int notificationId) {
        return notificationService.readNotification(userId, Optional.of(notificationId));
    }

    public String deleteAllNotification(long userId) {
        return notificationService.deleteAllNotifications(userId);
    }

    public String deleteNotification(long userId, int notificationId) {
        return notificationService.deleteNotification(userId, notificationId);
    }

    public NotificationCountResponse countNotifications(long userId) {
        return notificationService.countNotifications(userId);
    }
    public List<User> getSubscribedUsers(ColumnEventType cet, String targetId) {
        return switch (cet) {
            case RP_INSERT, CONGRESSMAN_PARTY_UPDATE -> userService.getUserByLikedCongressmanId(targetId);
            case BILL_STAGE_UPDATE, BILL_RESULT_UPDATE -> userService.getUserByLikedBillId(targetId);
        };
    }
    public List<String> getProcessedData(ColumnEventType columnEventType,List<String> eventData) {
        return switch (columnEventType) {
            case RP_INSERT -> insertRepresentativeBill(eventData);
            case CONGRESSMAN_PARTY_UPDATE -> updateCongressmanParty(eventData);
            case BILL_STAGE_UPDATE -> updateBillStage(eventData);
            case BILL_RESULT_UPDATE -> updateBillResult(eventData);
        };
    }
    public List<String> insertRepresentativeBill(List<String> uniqueKeys) {
        var bill = billService.findById(uniqueKeys.get(1));
        if (!(bill.getProposerKind()==(ProposerKindType.CONGRESSMAN))) {
            return List.of();
        }
        var congressman = congressmanService.findById(uniqueKeys.get(0));
        var congressmanName = congressman.getName();
        var party = congressman.getParty();
        var billId = bill.getId();
        var billBriefSummary = bill.getBriefSummary();
        String partyName = NullUtil.nullCoalescing(party::getName, "defaultPartyName");
        String partyImageUrl = NullUtil.nullCoalescing(party::getPartyImageUrl, "defaultPartyImageUrl");
        var congressmanInfo = partyName+":"+congressman.getCongressmanImageUrl();
        var partyInfo = partyName+":"+partyImageUrl;


        return List.of(billId, congressmanName, billBriefSummary, congressmanInfo, partyInfo);
    }
    public List<String> updateCongressmanParty(List<String> uniqueKeys) {
        var congressman = congressmanService.findById(uniqueKeys.get(0));
        var congressmanId = congressman.getId();
        var congressmanName = congressman.getName();

        String partyName = NullUtil.nullCoalescing(() -> congressman.getParty().getName(), "defaultPartyName");
        var congressmanInfo = partyName+":"+congressman.getCongressmanImageUrl();
        return List.of(congressmanId, partyName, congressmanName,congressmanInfo);
    }
    public List<String> updateBillStage(List<String> uniqueKeys) {
        var billId = uniqueKeys.get(0);
        var bill = billService.findById(billId);
        var proposerKind = bill.getProposerKind();
        var briefSummary = bill.getBriefSummary();
        var proposers = bill.getProposers();
        var stage = bill.getStage();

        if(proposerKind.equals(ProposerKindType.CONGRESSMAN)){
            return Stream.concat(Stream.of(billId, briefSummary, stage, proposerKind.name()), partyService.getPartyInfoList(billId).stream())
                    .toList();
        }
        else{
            return List.of(billId, briefSummary, stage, proposerKind.name(),proposers);

        }
    }
    public List<String> updateBillResult(List<String> relatedEntityIds) {
        var billId = relatedEntityIds.get(0);
        var bill = billService.findById(billId);
        var proposerKind = bill.getProposerKind();
        var briefSummary = bill.getBriefSummary();
        var proposers = bill.getProposers();
        var billResult = bill.getBillResult();

        if(proposerKind.equals(ProposerKindType.CONGRESSMAN)){
            return Stream.concat(Stream.of(billId, briefSummary, billResult, proposerKind.name()), partyService.getPartyInfoList(billId).stream())
                    .toList();
        }
        else{
            return List.of(billId, briefSummary, billResult, proposerKind.name(), proposers);

        }
    }
} 