package com.everyones.lawmaking.global.constant;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

public class BillInfoConstant {

    private static final LocalDate OPENING_OF_THE_NATIONAL_ASSEMBLY = LocalDate.of(2024, 5, 30);

    private static final int CURRENT_ASSEMBLY_NUMBER = 22;

    public static int getCurrentAssemblyNumber() {
        return CURRENT_ASSEMBLY_NUMBER;
    }

    public static Long getDaysSinceOpening() {
        return ChronoUnit.DAYS.between(OPENING_OF_THE_NATIONAL_ASSEMBLY, LocalDate.now());
    }

}
