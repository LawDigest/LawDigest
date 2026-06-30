package com.everyones.lawmaking.repository;

import com.everyones.lawmaking.common.dto.CategoryCountDto;
import com.everyones.lawmaking.common.dto.response.BillListResponse;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;

public interface BillRepositoryCustom {
    BillListResponse findBillWithDetailAndPage(Pageable pageable, Optional<Long> userIdOptional, String stage);

    BillListResponse findBillByCategoryAndPage(Pageable pageable, Optional<Long> userIdOptional, String category);

    List<CategoryCountDto> countByCategory();

}
