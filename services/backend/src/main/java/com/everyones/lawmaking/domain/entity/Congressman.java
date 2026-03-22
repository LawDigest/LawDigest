package com.everyones.lawmaking.domain.entity;

import com.everyones.lawmaking.common.dto.request.LawmakerDfRequest;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.ColumnDefault;

import java.time.LocalDate;
import java.util.List;


@Entity
@Data
@Builder
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class Congressman extends BaseEntity{
    @Version
    private Long version;

    @Id
    @Column(name = "congressman_id")
    private String id;

    private String name;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "party_id")
    private Party party;

    @OneToMany(mappedBy = "congressman")
    private List<BillProposer> billPublicProposer;

    @OneToMany(mappedBy = "congressman")
    private List<RepresentativeProposer> representativeProposer;

    @OneToMany(mappedBy = "congressman")
    private List<CongressmanLike> congressmanLike;

    @Column(name = "elect_sort")
    private String electSort;

    private String district;

    @Column(name = "commits", columnDefinition = "TEXT")
    private String commits;

    @Column(name = "elected")
    private String elected;

    @Column(name = "homepage")
    private String homepage;

    @Column(name = "state",columnDefinition = "boolean default false")
    private Boolean state;

    @Column(name = "congressman_age")
    private String congressmanAge;

    @Column(name = "sex")
    private String sex;

    @Column(name = "congressman_telephone")
    private String congressmanTelephone;

    @Column(name = "congressman_bill_propose_date")
    private LocalDate congressmanBillProposeDate;

    @Column(name = "email")
    private String email;

    @Column(name = "congressman_office")
    private String congressmanOffice;

    @Column(name = "congressman_image_url")
    private String congressmanImageUrl;

    @ColumnDefault("22")
    @Column(name = "assembly_number")
    private int assemblyNumber;

    @Column(name = "brief_history",columnDefinition = "TEXT")
    private String briefHistory;

    @Override
    public String toString() {
        return "Congressman{" +
                "id=" + id +
                ", name='" + name + '\'' +
                '}';
    }


    public static Congressman of(LawmakerDfRequest lawmakerDfRequest,Party party){
        String congressmanId = lawmakerDfRequest.getCongressmanId();
        int assemblyNumber = lawmakerDfRequest.getAssemblyNumber();
        String congressmanImageUrl = "/congressman/" + assemblyNumber + "/" + congressmanId + ".jpg";
        return Congressman.builder()
                .id(congressmanId)
                .name(lawmakerDfRequest.getCongressmanName())
                .party(party)
                .assemblyNumber(assemblyNumber)
                .commits(lawmakerDfRequest.getCommits())
                .elected(lawmakerDfRequest.getElected())
                .homepage(lawmakerDfRequest.getHomepage())
                .district(lawmakerDfRequest.getDistrict())
                .congressmanImageUrl(congressmanImageUrl)
                .congressmanAge(lawmakerDfRequest.getCongressmanBirth())
                .congressmanOffice(lawmakerDfRequest.getCongressmanOffice())
                .congressmanTelephone(lawmakerDfRequest.getCongressmanTelephone())
                .sex(lawmakerDfRequest.getSex())
                .email(lawmakerDfRequest.getEmail())
                .briefHistory(lawmakerDfRequest.getBriefHistory())
                .state(true)
                .build();

    }

    public void update(LawmakerDfRequest lawmakerDfRequest,Party party){
        this.setId(lawmakerDfRequest.getCongressmanId());
        this.setName(lawmakerDfRequest.getCongressmanName());
        this.setParty(party);
        this.setAssemblyNumber(lawmakerDfRequest.getAssemblyNumber());
        this.setCommits(lawmakerDfRequest.getCommits());
        this.setElected(lawmakerDfRequest.getElected());
        this.setHomepage(lawmakerDfRequest.getHomepage());
        this.setDistrict(lawmakerDfRequest.getDistrict());
        this.setCongressmanAge(lawmakerDfRequest.getCongressmanBirth());
        this.setCongressmanOffice(lawmakerDfRequest.getCongressmanOffice());
        this.setCongressmanTelephone(lawmakerDfRequest.getCongressmanTelephone());
        this.setSex(lawmakerDfRequest.getSex());
        this.setEmail(lawmakerDfRequest.getEmail());
        this.setBriefHistory(lawmakerDfRequest.getBriefHistory());

    }

    public void updateState(Boolean changedState){
        this.setState(changedState);
        if(!changedState){
            this.setElectSort("");
            this.setDistrict("");
        }
    }

    public void updateBillProposeDate(LocalDate proposeDate) {
        this.setCongressmanBillProposeDate(proposeDate);
    }



}
