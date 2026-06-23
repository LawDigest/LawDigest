from lawdigest_ai.processor.law_open_api_terms import LawOpenApiTermClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        target = params["target"]
        if target == "lstrmAI":
            return _FakeResponse(
                {
                    "lstrmAISearch": {
                        "법령용어": [
                            {"법령용어명": "청문"},
                            {"법령용어명": "인사청문"},
                        ]
                    }
                }
            )
        if target == "lstrmRlt":
            return _FakeResponse(
                {
                    "lstrmRltService": {
                        "법령용어": [
                            {
                                "법령용어명": "청문",
                                "연계용어": [
                                    {"일상용어명": "면담"},
                                    {"일상용어명": "심문"},
                                    {"일상용어명": "면담"},
                                ],
                            }
                        ]
                    }
                }
            )
        if target == "dlytrmRlt":
            return _FakeResponse(
                {
                    "dlytrmRltService": {
                        "일상용어": {
                            "일상용어명": params["query"],
                            "연계용어": [
                                {"법령용어명": "청문"},
                                {"법령용어명": "의견청취"},
                            ],
                        }
                    }
                }
            )
        raise AssertionError(f"unexpected target: {target}")


def test_law_open_api_term_client_looks_up_terms_and_relations():
    session = _FakeSession()
    client = LawOpenApiTermClient(oc="law-key", session=session, timeout_seconds=1.5)

    result = client.lookup_term("청문")

    assert result is not None
    assert result.term == "청문"
    assert result.source == "law.go.kr"
    assert result.related_daily_terms == ("면담", "심문")
    assert result.related_legal_terms == ()
    assert [call["params"]["target"] for call in session.calls] == ["lstrmAI", "lstrmRlt"]
    assert session.calls[0]["params"]["OC"] == "law-key"
    assert session.calls[0]["params"]["type"] == "JSON"
    assert session.calls[0]["params"]["query"] == "청문"
    assert session.calls[0]["timeout"] == 1.5


def test_law_open_api_term_client_is_disabled_without_oc():
    client = LawOpenApiTermClient(oc="")

    assert client.enabled is False
