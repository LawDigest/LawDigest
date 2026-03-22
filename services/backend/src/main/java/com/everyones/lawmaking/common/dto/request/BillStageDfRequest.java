package com.everyones.lawmaking.common.dto.request;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Getter
@AllArgsConstructor
@NoArgsConstructor
public class BillStageDfRequest {

    private String billId;

    private String stage;

    private String committee;

    private String actStatusValue;

    @DateTimeFormat(pattern="yyyy-MM-dd")
    private LocalDate statusUpdateDate;
}
