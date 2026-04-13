package com.everyones.lawmaking.repository.election;

import com.everyones.lawmaking.domain.entity.election.ElectionDistrict;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class ElectionDistrictRepositoryTest {

    @SpringBootConfiguration
    @EnableAutoConfiguration
    @EntityScan(basePackageClasses = ElectionDistrict.class)
    @EnableJpaRepositories(basePackageClasses = ElectionDistrictRepository.class)
    static class TestJpaConfig {
    }

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private ElectionDistrictRepository electionDistrictRepository;

    @Test
    void returnsDistinctProvinceNamesInOrder() {
        entityManager.persist(ElectionDistrict.builder()
                .sgId("20260603")
                .sgTypecode(3)
                .sdName("서울특별시")
                .sggName("종로구")
                .sOrder(2)
                .build());
        entityManager.persist(ElectionDistrict.builder()
                .sgId("20260603")
                .sgTypecode(3)
                .sdName("경기도")
                .sggName("수원시")
                .sOrder(1)
                .build());
        entityManager.persist(ElectionDistrict.builder()
                .sgId("20260603")
                .sgTypecode(3)
                .sdName("서울특별시")
                .sggName("중구")
                .sOrder(2)
                .build());
        entityManager.flush();

        List<String> names = electionDistrictRepository.findDistinctSdNameBySgIdAndSgTypecode("20260603", 3);

        assertThat(names).containsExactly("경기도", "서울특별시");
    }
}
