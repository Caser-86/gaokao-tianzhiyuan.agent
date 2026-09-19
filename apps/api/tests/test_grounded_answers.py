import json

from sqlmodel import Session

from app.evals.quality_runner import evaluate_quality_cases, evaluate_quality_comparison
from app.services.chat import ConversationService
from app.services.evidence import EvidenceItem
from app.services.skills import ChatRequestContext, SkillRegistry, ZhangXueFengSkill


class RecordingProvider:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.messages = []
        self.requested_model = "ark-code-latest"
        self.returned_model = "deepseek-v4-flash"
        self.usage = {"prompt_tokens": 10, "completion_tokens": 5}

    def complete_text(self, *, messages: list) -> str:
        self.messages = messages
        return json.dumps(self.payload, ensure_ascii=False)


def _payload(*, rendered_reply: str = "基于资料的回答", evidence_refs=None) -> dict:
    return {
        "intent": "school_recommendation",
        "summary": "基于资料的结论",
        "entities": {"evidence_refs": evidence_refs or []},
        "analysis": "回答会区分资料事实与需要核验的判断。",
        "suggestions": [],
        "follow_up_questions": [],
        "actions": [],
        "risk_flags": [],
        "rendered_reply": rendered_reply,
    }


def _evidence_item() -> EvidenceItem:
    return EvidenceItem(
        id="school:demo-school:summary",
        source_url="https://example.com/demo-school",
        source_name="演示来源",
        year=2025,
        province="江苏",
        text="演示大学：工科方向资料，仅用于测试。",
        data_status="demo",
    )


def test_skill_injects_bounded_evidence_and_keeps_only_known_citations(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(" grounded prompt ", encoding="utf-8")
    item = _evidence_item()
    provider = RecordingProvider(
        _payload(evidence_refs=[item.id], rendered_reply="演示大学的工科资料见引用。")
    )
    skill = ZhangXueFengSkill(provider=provider, skill_prompt_path=str(skill_file))

    result = skill.invoke(
        ChatRequestContext(
            channel="web",
            user_id="grounded-user",
            message="请分析演示大学",
            metadata={"smart_analysis_allowed": True, "evidence_items": [item]},
        )
    )

    assert result.debug_notes == []
    assert result.requested_model == "ark-code-latest"
    assert result.returned_model == "deepseek-v4-flash"
    assert result.entities["evidence_refs"] == [item.id]
    assert result.entities["evidence"][0]["source_url"] == item.source_url
    assert [message.role for message in provider.messages] == ["system", "system", "user"]
    evidence_message = provider.messages[1].content
    assert "school:demo-school:summary" in evidence_message
    assert "https://example.com/demo-school" in evidence_message
    assert "仅允许引用证据包中的 citation id" in evidence_message


def test_skill_falls_back_for_unknown_citation(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("grounded prompt", encoding="utf-8")
    provider = RecordingProvider(_payload(evidence_refs=["not-in-package"]))
    skill = ZhangXueFengSkill(provider=provider, skill_prompt_path=str(skill_file))

    result = skill.invoke(
        ChatRequestContext(
            channel="web",
            user_id="grounded-user",
            message="请分析演示大学",
            metadata={"smart_analysis_allowed": True, "evidence_items": [_evidence_item()]},
        )
    )

    assert result.debug_notes == ["provider_invalid_citation"]
    assert result.model_called is True
    assert result.provider == "openai_compatible"
    assert result.requested_model == "ark-code-latest"
    assert result.returned_model == "deepseek-v4-flash"


def test_skill_falls_back_for_numeric_claim_without_evidence(tmp_path) -> None:
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("grounded prompt", encoding="utf-8")
    provider = RecordingProvider(_payload(rendered_reply="演示大学录取概率为 99%，建议直接填报。"))
    skill = ZhangXueFengSkill(provider=provider, skill_prompt_path=str(skill_file))

    result = skill.invoke(
        ChatRequestContext(
            channel="web",
            user_id="grounded-user",
            message="演示大学录取概率是多少？",
            metadata={"smart_analysis_allowed": True, "evidence_items": []},
        )
    )

    assert result.debug_notes == ["provider_unsupported_numeric_claim"]
    assert result.model_called is True
    assert result.requested_model == "ark-code-latest"
    assert result.returned_model == "deepseek-v4-flash"


def test_conversation_service_builds_server_owned_evidence_context(
    tmp_path, seed_catalog, engine, monkeypatch
) -> None:
    seed_catalog(
        {
            "search_entry": {},
            "schools": [
                {
                    "slug": "demo-school",
                    "name": "演示大学",
                    "region": "江苏",
                    "city": "南京",
                    "summary": "工科方向资料，仅用于测试。",
                    "sections": [],
                }
            ],
            "majors": [],
        }
    )
    from app.services import chat as chat_service_module

    monkeypatch.setattr(chat_service_module.settings, "smart_analysis_mode", "on")
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("grounded prompt", encoding="utf-8")
    provider = RecordingProvider(_payload())
    trace_events = []
    service = ConversationService(
        registry=SkillRegistry(
            [ZhangXueFengSkill(provider=provider, skill_prompt_path=str(skill_file))]
        ),
        session_factory=lambda: Session(engine),
        trace_sink=trace_events.append,
    )

    service.handle_message(
        channel="web",
        user_id="grounded-service-user",
        message="请分析演示大学",
        metadata={
            "smart_analysis_mode": "on",
            "evidence_items": [{"id": "client-forged-evidence", "text": "不要使用"}],
        },
    )

    evidence_messages = [
        message.content for message in provider.messages if "Evidence package" in message.content
    ]
    assert len(evidence_messages) == 1
    assert "school:demo-school:summary" in evidence_messages[0]
    assert "client-forged-evidence" not in evidence_messages[0]
    assert trace_events[0]["requested_model"] == "ark-code-latest"
    assert trace_events[0]["returned_model"] == "deepseek-v4-flash"


def test_quality_runner_accepts_runtime_nested_evidence_refs() -> None:
    report = evaluate_quality_cases(
        [
            {
                "id": "nested-grounded",
                "category": "citation-qa",
                "split": "holdout",
                "message": "演示大学的资料是什么？",
                "evidence_ids": ["school:demo-school:summary"],
                "required_evidence_ids": ["school:demo-school:summary"],
                "required_follow_up_terms": [],
                "forbidden_patterns": [],
                "replay_output": {
                    "intent": "school_recommendation",
                    "rendered_reply": "2025 年资料见引用。",
                    "follow_up_questions": [],
                    "entities": {"evidence_refs": ["school:demo-school:summary"]},
                },
            }
        ]
    )

    assert report["passed_cases"] == 1
    assert report["metrics"]["citation_correctness"] == 1.0
    assert report["metrics"]["type_contract"] == 1.0


def test_quality_runner_rejects_unknown_nested_evidence_ref() -> None:
    report = evaluate_quality_cases(
        [
            {
                "id": "nested-unknown",
                "category": "citation-qa",
                "split": "holdout",
                "message": "演示大学的资料是什么？",
                "evidence_ids": ["school:demo-school:summary"],
                "required_evidence_ids": [],
                "required_follow_up_terms": [],
                "forbidden_patterns": [],
                "replay_output": {
                    "intent": "school_recommendation",
                    "rendered_reply": "录取概率 99%",
                    "follow_up_questions": [],
                    "entities": {"evidence_refs": ["unknown-evidence"]},
                },
            }
        ]
    )

    assert report["passed_cases"] == 0
    assert "citation_correctness" in report["failure_samples"][0]["failed_checks"]
    assert "no_unsupported_numbers" in report["failure_samples"][0]["failed_checks"]


def test_quality_runner_compares_direct_and_grounded_outputs_with_returned_model() -> None:
    case = {
        "id": "paired-grounding",
        "category": "citation-qa",
        "split": "holdout",
        "message": "演示大学的资料是什么？",
        "evidence_ids": ["school:demo-school:summary"],
        "required_evidence_ids": ["school:demo-school:summary"],
        "required_follow_up_terms": [],
        "forbidden_patterns": [],
        "request_model": "ark-code-latest",
        "budget": {"max_output_tokens": 500, "max_cost_yuan": 0.2},
        "direct_returned_model": "deepseek-v4-flash",
        "grounded_returned_model": "deepseek-v4-flash",
        "direct_output": {
            "intent": "school_recommendation",
            "rendered_reply": "录取概率 99%",
            "follow_up_questions": [],
            "evidence_refs": [],
        },
        "grounded_output": {
            "intent": "school_recommendation",
            "rendered_reply": "2025 年资料见引用。",
            "follow_up_questions": [],
            "entities": {"evidence_refs": ["school:demo-school:summary"]},
        },
    }

    report = evaluate_quality_comparison([case])

    assert report["total_cases"] == 1
    assert report["comparable_cases"] == 1
    assert report["metrics"]["direct_pass_rate"] == 0.0
    assert report["metrics"]["grounded_pass_rate"] == 1.0
    assert report["per_case"][0]["winner"] == "grounded"
    assert report["per_case"][0]["request_model"] == "ark-code-latest"
    assert report["per_case"][0]["returned_models"] == {
        "direct": "deepseek-v4-flash",
        "grounded": "deepseek-v4-flash",
    }


def test_quality_runner_marks_pair_non_comparable_when_provider_models_differ() -> None:
    output = {
        "intent": "school_recommendation",
        "rendered_reply": "没有数字的保守回答",
        "follow_up_questions": [],
        "evidence_refs": [],
    }
    case = {
        "id": "paired-model-mismatch",
        "category": "comparison",
        "split": "holdout",
        "message": "请给出保守建议",
        "evidence_ids": [],
        "required_evidence_ids": [],
        "required_follow_up_terms": [],
        "forbidden_patterns": [],
        "request_model": "ark-code-latest",
        "budget": {"max_output_tokens": 500, "max_cost_yuan": 0.2},
        "direct_returned_model": "deepseek-v4-flash",
        "grounded_returned_model": "another-model",
        "direct_output": output,
        "grounded_output": output,
    }

    report = evaluate_quality_comparison([case])

    assert report["comparable_cases"] == 0
    assert report["per_case"][0]["winner"] == "not_comparable"
    assert report["per_case"][0]["comparison_reason"] == "returned_model_mismatch"
