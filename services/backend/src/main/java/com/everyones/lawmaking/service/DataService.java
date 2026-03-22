package com.everyones.lawmaking.service;

import com.everyones.lawmaking.common.dto.request.*;
import com.everyones.lawmaking.domain.entity.*;
import com.everyones.lawmaking.global.error.CongressmanException;
import com.everyones.lawmaking.global.error.PartyException;
import com.everyones.lawmaking.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
// 데이터 변경에 관한 서비스이므로 readOnly 제거
public class DataService {
    private final BillRepository billRepository;
    private final CongressmanRepository congressmanRepository;
    private final BillProposerRepository billProposerRepository;
    private final RepresentativeProposerRepository representativeProposerRepository;
    private final PartyRepository partyRepository;
    private final BillTimelineRepository billTimelineRepository;
    private final VoteRecordRepository voteRecordRepository;
    private final VotePartyRepository votePartyRepository;
    private final CongressmanRepositoryCustom congressmanRepositoryCustom;
    private final PartyRepositoryCustom partyRepositoryCustom;

    @Transactional
    public void insertBillInfoDf(List<BillDfRequest> billDfRequestList) {

        // stream으로 dto 각각을 맞는 부분에 넣어야함.
        // 중간에 로직이 필요하면 로직을 거쳐서 들어가자.
        // 시점 파티 데이터 넣기
        billDfRequestList
            .forEach(billDfRequest -> {
                var oldBill = billRepository.findBillById(billDfRequest.getBillId())
                        .orElse(null);
                if (oldBill != null){
                    oldBill.updateContent(billDfRequest);
                }
                else {
                    Bill newBill = Bill.of(billDfRequest);


                    billRepository.save(newBill);


                    //이름으로 congressmanId를 찾아서 billProposer 저장하기
                    //@ToDo 동명이인 필터링을 위해 후에 의원검색에 한글이름, 한자이름, 정당이름 세가지 조건을 추가하기.
                    //현재는 state가 true인 조건만 추가
                    //트랜잭션에서 에러가 발생하면 모든 트랜잭션이 롤백해야함.
                    billDfRequest.getPublicProposerIdList()
                            .forEach(congressmanId -> {
                                var billProposer = congressmanRepository.findLawmakerById(congressmanId)
                                        .orElseThrow(() -> new CongressmanException.CongressmanNotFound(Map.of("congressman", congressmanId)));
                                billProposerUpdate(newBill, billProposer);
                                    }
                            );
                    //대표발의자 이름 검색해서 RP 찾기
                    billDfRequest.getRstProposerIdList().
                            forEach((rpID) -> {
                        var representativeProposer = congressmanRepository.findLawmakerById(rpID)
                                .orElseThrow(() -> new CongressmanException.CongressmanNotFound(Map.of("congressman", rpID)));
                                updateRepresentativeProposer(newBill, representativeProposer);
                            }
                    );
                }
                }
            );

    }

    @Transactional
    public Map<String, List<String>> updateBillStageDf(List<BillStageDfRequest> billStageDfRequestList) {
        // 법안 number나 법안 id로 법안을 찾아
        // stage를 수정하고 act status와 statusUpdateDate를 가지고 billTimeline 객체를 만든다.
        Map<String, List<String>> resultMap = new HashMap<>();
        resultMap.put("notFoundBill", new ArrayList<>());
        resultMap.put("duplicateBill", new ArrayList<>());


        billStageDfRequestList.forEach(
                billStageDfRequest -> {
                    var billId = billStageDfRequest.getBillId();
                    var foundBill = billRepository.findBillById(billId)
                            .orElse(null);
                    var equalBillTimeline = billTimelineRepository.findBillTimelineByInfo(
                            billStageDfRequest.getBillId(),
                            billStageDfRequest.getStage(),
                            billStageDfRequest.getCommittee(),
                            billStageDfRequest.getStatusUpdateDate());

                    if(equalBillTimeline.isPresent()){
                        resultMap.get("duplicateBill").add(equalBillTimeline.get());
                    }
                    else if(foundBill == null){
                        resultMap.get("notFoundBill").add(billStageDfRequest.getBillId());
                    }
                    // 중복된 billTimeline이 없고 bill이 존재할 경우
                    else{
                        foundBill.updateStatusByStep(billStageDfRequest);
                        // billTimeline 객체 만들기
                        var billTimeline = BillTimeline.of(foundBill, billStageDfRequest);
                        billTimelineRepository.save(billTimeline);
                    }

                }
        );

        return resultMap;
    }

    @Transactional
    public void updateBillResultDf(List<BillResultDfRequest> billResultDfRequestList) {
        billResultDfRequestList.forEach(
                // bill number로 bill을 찾고 내용 수정하자!
                (billResultDfRequest) -> {
                    var billId = billResultDfRequest.getBillId();
                    var foundBill = billRepository.findBillById(billId);
                    foundBill.ifPresent(bill -> bill.setBillResult(billResultDfRequest.getBillProposeResult()));
                    var billTimelist = billTimelineRepository.findByBillIdAndBillTimelineStageAndBillResult(billId, "본회의 심의",null);
                    billTimelist.forEach(billTimeline -> billTimeline.setBillResult(billResultDfRequest.getBillProposeResult()));
                }
        );
    }

    @Transactional
    public void updateLawmakerDf(List<LawmakerDfRequest> lawmakerDfRequestList) {

        // 삽입 :국회 API 호출 데이터 - (API 교집합 DB의원데이터)
        // state false로 만들기 진행: 디비 의원 데이터 - (API 교집합 DB의원데이터) -> 전부 False로 처리
        // 교집합 처리: API 교집합 DB의원 데이터를 새롭게 업데이트 해주면서 state True로 처리

        // API 데이터 들을 맵으로 만들기
        Map<String,LawmakerDfRequest> lawmakerApiData = new HashMap<>();
        lawmakerDfRequestList.forEach(lawmaker-> {
            lawmakerApiData.put(lawmaker.getCongressmanId(), lawmaker);
        });

        //DB 의원데이터 가져오기
        Set<String> congressmanSet = new HashSet<>(congressmanRepository.findAllCongressmanId());
        Set<String> intersectionWithApiAndDB = new HashSet<>(congressmanSet);

        //API 데이터 집합
        Set<String> lawmakerApi = new HashSet<>(lawmakerApiData.keySet());

        //디비에 존재하는 현재 의원 데이터
        intersectionWithApiAndDB.retainAll(lawmakerApi);

        //삽입해야하는 차집합
        lawmakerApi.removeAll(intersectionWithApiAndDB);
        congressmanSet.removeAll(intersectionWithApiAndDB);

        //삽입 과정 진행
        lawmakerApi.forEach((insertLawmaker)->
                this.insertLawmaker(lawmakerApiData.get(insertLawmaker)));

        //상태 false로 만들기 진행
        congressmanSet.forEach(updateStateFalseCongressman ->
                congressmanRepository.findCongressmanById(updateStateFalseCongressman)
                        .filter(Congressman::getState)
                        .ifPresent(this::lawmakerStateToFalse)
        );

        //수정 과정 진행
        //API로 들어온 의원리스트로 기존 의원 데이터 최신화 시키기
        intersectionWithApiAndDB.forEach((updateStateTrueCongressmanId)->{
            var congressmanUpdateToTrue = congressmanRepository.findCongressmanById(updateStateTrueCongressmanId)
                    .orElseThrow(() -> new CongressmanException.CongressmanNotFound(Map.of("congressman", updateStateTrueCongressmanId)));
            lawmakerStateToTrue(lawmakerApiData.get(updateStateTrueCongressmanId),congressmanUpdateToTrue);
        });

    }

    @Transactional
    public List<String> insertAssemblyVote(List<VoteDfRequest> voteDfRequestList){
        List<String> result = new ArrayList<>();

        voteDfRequestList.forEach((voteDfRequest)->{
            var billId = voteDfRequest.getBillId();
            var foundBill = billRepository.findBillById(billId)
                    .orElse(null);
            if (foundBill == null) {
                result.add(billId);
            }
            else{
                var voteRecord = voteRecordRepository.findVoteRecordByBillId(foundBill.getId());
                if(voteRecord.isEmpty()){
                    var newVoteRecord = VoteRecord.of(foundBill, voteDfRequest);
                    voteRecordRepository.save(newVoteRecord);
                }
            }
        });
        return result;
    }

    @Transactional
    public List<String> insertVoteParty(List<VotePartyRequest> votePartyRequestList){
        List<String> result = new ArrayList<>();

        votePartyRequestList.forEach((votePartyRequest)->{
            var party = partyRepository.findPartyByName(votePartyRequest.getPartyName())
                    .orElse(null);
            var foundBill = billRepository.findBillById(votePartyRequest.getBillId())
                    .orElse(null);

            if (party == null || foundBill == null) {
                result.add(votePartyRequest.getBillId());
            }
            else{
                var foundVoteParty = votePartyRepository.findByBillAndParty(foundBill.getId(), party.getId())
                        .orElse(null);
                if (foundVoteParty==null){
                    var voteParty = VoteParty.of(foundBill,party, votePartyRequest);
                    votePartyRepository.save(voteParty);
                }
                else{
                    foundVoteParty.updateVotesForCount(votePartyRequest);
                    votePartyRepository.save(foundVoteParty);
                }
            }
        });
        return result;
    }

    @Transactional
    public void billProposerUpdate(Bill newBill, Congressman billProposer) {
                var newBillProposer = BillProposer.builder()
                        .bill(newBill)
                        .congressman(billProposer)
                        .party(billProposer.getParty())
                        .build();

                billProposerRepository.save(newBillProposer);




    }

    @Transactional
    public void updateRepresentativeProposer(Bill newBill, Congressman representativeProposer) {


                var repProposer = RepresentativeProposer.builder()
                        .bill(newBill)
                        .congressman(representativeProposer)
                        .party(representativeProposer.getParty())
                        .build();

                //RP 저장
                representativeProposerRepository.save(repProposer);

        }


    @Transactional
    public void insertLawmaker(LawmakerDfRequest ldr) {

        String partyName = ldr.getPartyName();
        var party = partyRepository.findPartyByName(partyName).orElse(null);

        if (party == null) {
            party = Party.create(partyName);
        }

        var congressman = Congressman.of(ldr, party);

        partyRepository.save(party);
        congressmanRepository.save(congressman);

    }

    @Transactional
    public void lawmakerStateToFalse(Congressman lawmaker) {
        // 정당 정보 업데이트
        if(lawmaker.getState()){
            lawmaker.updateState(false);
        }
        congressmanRepository.save(lawmaker);
    }


    @Transactional
    public void lawmakerStateToTrue(LawmakerDfRequest ldr, Congressman congressmanStateUpdateTrue) {
        var party = congressmanStateUpdateTrue.getParty();
        if (party == null) {
            throw new PartyException.PartyNotFound(Map.of("party", "null"));
        }
        //정당이 같고 의원유형이 같은경우
        if (congressmanStateUpdateTrue.getState() & party.getName().equals(ldr.getPartyName()) & congressmanStateUpdateTrue.getDistrict().equals(ldr.getDistrict())) {
            return;
        }
        var partyName = party.getName();
        // 정당 정보 업데이트

        if (partyName.equals(ldr.getPartyName())) {
            congressmanStateUpdateTrue.update(ldr, party);
            partyRepository.save(party);
        } else {
            var newParty = partyRepository.findPartyByName(ldr.getPartyName())
                    .orElse(null);
            if (newParty == null) {
                newParty = Party.create(ldr.getPartyName());
            }
            congressmanStateUpdateTrue.update(ldr, newParty);
            partyRepository.save(newParty);

        }
        //의원 상태 변경
        congressmanStateUpdateTrue.updateState(true);

        //flush처리 되지만 가독성을 위해 flush처리
        congressmanRepository.save(congressmanStateUpdateTrue);
    }

    @Transactional
    public void updateCongressmanCountByParty() {
        List<Party> partyList = partyRepository.findAll();
        partyList.forEach(party -> {
            var proportionalCongressmanCount = congressmanRepositoryCustom.countCongressmanByPartyId(party.getId(), true);
            var districtCongressmanCount = congressmanRepositoryCustom.countCongressmanByPartyId(party.getId(),false);
            party.updateCongressmanCount(districtCongressmanCount, proportionalCongressmanCount);
            partyRepository.save(party);
        });
    }

    @Transactional
    public void updateBillCountByParty() {
        List<Party> partyList = partyRepository.findAll();
        partyList.forEach(party -> {
            var representativeBillCount = partyRepositoryCustom.countBillCountByPartyId(party.getId(), true);
            var publicBillCount = partyRepositoryCustom.countBillCountByPartyId(party.getId(),false);
            party.updateBillCount(representativeBillCount, publicBillCount);
            partyRepository.save(party);
        });
    }

    @Transactional
    public void updateProposeDateByCongressman() {
        List<Congressman> congressmanList = congressmanRepository.findAll();
        congressmanList.forEach(congressman -> {
            var billProposerUpdateDate = congressmanRepositoryCustom.updateProposeDateByCongressman(congressman.getId());
            congressman.updateBillProposeDate(billProposerUpdateDate);
            });
        }
}



