package com.everyones.lawmaking.domain.entity.poll;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Immutable;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Getter
@Builder
@Immutable
@AllArgsConstructor(access = AccessLevel.PROTECTED)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(name = "PollSurvey")
public class PollSurvey {

    @Id
    @Column(name = "registration_number", nullable = false, length = 50)
    private String registrationNumber;

    @Column(name = "election_type", length = 100)
    private String electionType;

    @Column(name = "region", length = 200)
    private String region;

    @Column(name = "election_name", length = 200)
    private String electionName;

    @Column(name = "pollster", length = 100)
    private String pollster;

    @Column(name = "sponsor", length = 200)
    private String sponsor;

    @Column(name = "survey_start_date")
    private LocalDate surveyStartDate;

    @Column(name = "survey_end_date")
    private LocalDate surveyEndDate;

    @Column(name = "sample_size")
    private Integer sampleSize;

    @Column(name = "margin_of_error", length = 50)
    private String marginOfError;

    @Column(name = "source_url", length = 500)
    private String sourceUrl;

    @Column(name = "pdf_path", length = 500)
    private String pdfPath;

    @Column(name = "created_date")
    private LocalDateTime createdDate;

    @Column(name = "modified_date")
    private LocalDateTime modifiedDate;
}
