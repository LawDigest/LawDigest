from __future__ import annotations

import json

from lawdigest_data.polls.models import ListRecord
from lawdigest_data.polls.targets import is_ignored_analysis_filename, load_targets, matches_target


def test_load_targets_builds_targets_from_region_and_election_specs(tmp_path):
    config_path = tmp_path / "poll_targets.json"
    config_path.write_text(
        json.dumps(
            {
                "regions": {
                    "gyeonggi": {
                        "search_cnd": "4",
                        "search_wrd": "경기도",
                        "region": "경기도 전체",
                    },
                    "seoul": {
                        "search_cnd": "4",
                        "search_wrd": "서울특별시",
                        "region": "서울특별시 전체",
                    },
                },
                "elections": {
                    "local_9th_governor": {
                        "poll_gubuncd": "VT026",
                        "election_type": "제9회 전국동시지방선거",
                        "election_names": ["광역단체장선거"],
                    }
                },
                "targets": [
                    {
                        "slug": "gyeonggi_governor_9th",
                        "region_key": "gyeonggi",
                        "election_key": "local_9th_governor",
                        "ignored_analysis_filenames": ["gyeonggi-ignore.pdf"],
                    },
                    {
                        "slug": "seoul_mayor_9th",
                        "region_key": "seoul",
                        "election_key": "local_9th_governor",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    targets = load_targets(config_path)

    assert [target.slug for target in targets] == [
        "gyeonggi_governor_9th",
        "seoul_mayor_9th",
    ]
    assert targets[0].search_cnd == "4"
    assert targets[0].search_wrd == "경기도"
    assert targets[0].region == "경기도 전체"
    assert targets[0].poll_gubuncd == "VT026"
    assert targets[0].election_type == "제9회 전국동시지방선거"
    assert targets[0].election_names == ("광역단체장선거",)
    assert targets[1].search_wrd == "서울특별시"
    assert is_ignored_analysis_filename("gyeonggi-ignore.pdf", targets[0]) is True


def test_matches_target_distinguishes_seoul_from_gyeonggi(tmp_path):
    config_path = tmp_path / "poll_targets.json"
    config_path.write_text(
        json.dumps(
            {
                "regions": {
                    "gyeonggi": {"search_cnd": "4", "search_wrd": "경기도", "region": "경기도 전체"},
                    "seoul": {"search_cnd": "4", "search_wrd": "서울특별시", "region": "서울특별시 전체"},
                },
                "elections": {
                    "local_9th_governor": {
                        "poll_gubuncd": "VT026",
                        "election_type": "제9회 전국동시지방선거",
                        "election_names": ["광역단체장선거"],
                    }
                },
                "targets": [
                    {"slug": "gyeonggi_governor_9th", "region_key": "gyeonggi", "election_key": "local_9th_governor"},
                    {"slug": "seoul_mayor_9th", "region_key": "seoul", "election_key": "local_9th_governor"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    gyeonggi_target, seoul_target = load_targets(config_path)
    record = ListRecord(
        registration_number="REG-SEOUL-1",
        pollster="테스트기관",
        sponsor="테스트의뢰자",
        method="CATI",
        sample_frame="유무선 RDD",
        title_region="서울특별시 전체 광역단체장선거",
        registered_date="2026-04-06",
        province="서울특별시",
        detail_url="https://example.com/detail/1",
    )

    assert matches_target(record, seoul_target) is True
    assert matches_target(record, gyeonggi_target) is False


def test_real_config_marks_seoul_climate_survey_as_ignored():
    targets = load_targets()
    seoul_target = next(target for target in targets if target.slug == "seoul_mayor_9th")

    assert is_ignored_analysis_filename(
        "2026 기후위기 국민 인식조사_01_서울_TABLE_등록0306.pdf",
        seoul_target,
    ) is True
