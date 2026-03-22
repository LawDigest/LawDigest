package com.everyones.lawmaking.facade;

import com.everyones.lawmaking.common.dto.request.BillDfRequest;
import com.everyones.lawmaking.common.dto.request.BillStageDfRequest;
import com.everyones.lawmaking.common.dto.request.BillResultDfRequest;
import com.everyones.lawmaking.common.dto.request.LawmakerDfRequest;
import com.everyones.lawmaking.common.dto.request.VoteDfRequest;
import com.everyones.lawmaking.common.dto.request.VotePartyRequest;
import com.everyones.lawmaking.service.DataService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class DataFacade {
    private final DataService dataService;

    public void insertBillInfoDf(List<BillDfRequest> billDfRequestList) {
        dataService.insertBillInfoDf(billDfRequestList);
    }

    public Map<String, List<String>> updateBillStageDf(List<BillStageDfRequest> billStageDfRequestList) {
        return dataService.updateBillStageDf(billStageDfRequestList);
    }

    public void updateBillResultDf(List<BillResultDfRequest> billResultDfRequestList) {
        dataService.updateBillResultDf(billResultDfRequestList);
    }

    public void updateLawmakerDf(List<LawmakerDfRequest> lawmakerDfRequestList) {
        dataService.updateLawmakerDf(lawmakerDfRequestList);
    }

    public List<String> insertAssemblyVote(List<VoteDfRequest> voteDfRequestList){
        return dataService.insertAssemblyVote(voteDfRequestList);
    }

    public List<String> insertVoteIndividual(List<VotePartyRequest> votePartyRequestList){
        return dataService.insertVoteParty(votePartyRequestList);
    }

    public void updateCongressmanCountByParty(){
        dataService.updateCongressmanCountByParty();
    }
    public void updateBillCountByParty(){
        dataService.updateBillCountByParty();
    }
    public void updateProposeDateByCongressman(){
        dataService.updateProposeDateByCongressman();
    }
} 