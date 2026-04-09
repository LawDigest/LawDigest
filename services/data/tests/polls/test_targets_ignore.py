from __future__ import annotations

import json

from lawdigest_data.polls.targets import is_ignored_analysis_filename, load_targets


def test_load_targets_parses_ignored_analysis_filenames(tmp_path):
    targets_path = tmp_path / "targets.json"
    targets_path.write_text(
        json.dumps(
            {
                "regions": {
                    "gyeonggi": {
                        "search_cnd": "4",
                        "search_wrd": "경기도",
                        "region": "경기도 전체",
                    }
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
                        "ignored_analysis_filenames": [
                            "2026 기후위기 국민 인식조사_09_경기_TABLE_등록_0306.pdf",
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    targets = load_targets(targets_path)

    assert targets[0].ignored_analysis_filenames == (
        "2026 기후위기 국민 인식조사_09_경기_TABLE_등록_0306.pdf",
    )
    assert is_ignored_analysis_filename(
        "2026 기후위기 국민 인식조사_09_경기_TABLE_등록_0306.pdf",
        targets[0],
    )
    assert not is_ignored_analysis_filename("other.pdf", targets[0])
