"""Robust Qwen-VL response parsing and observation normalization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


REQUIRED_SECTIONS = {"product_truth", "template_fidelity", "visual_evidence", "decision_coverage"}


@dataclass
class VisionEvaluation:
    parse_status: str
    product_truth: dict[str, Any]
    template_fidelity: dict[str, Any]
    visual_evidence: dict[str, Any]
    decision_coverage: dict[str, Any]
    violations: list[dict[str, Any]]
    raw_model_output: str
    parse_error: str | None = None

    def model_dump(self):
        return {
            "parse_status": self.parse_status,
            "product_truth": self.product_truth,
            "template_fidelity": self.template_fidelity,
            "visual_evidence": self.visual_evidence,
            "decision_coverage": self.decision_coverage,
            "violations": self.violations,
            "raw_model_output": self.raw_model_output,
            "parse_error": self.parse_error,
        }


def parse_qwen_response(raw: Any) -> VisionEvaluation:
    text = extract_text(raw)
    try:
        value = extract_json(text)
        if not isinstance(value, dict):
            raise ValueError("top-level JSON is not an object")
        missing = REQUIRED_SECTIONS - set(value)
        if missing:
            raise ValueError(f"missing required sections: {sorted(missing)}")
        if not isinstance(value.get("violations", []), list):
            raise ValueError("violations must be an array")
        normalized = {item: normalize_section(value[item], item) for item in REQUIRED_SECTIONS}
        violations = normalize_violations(value.get("violations", []))
        return VisionEvaluation("SUCCESS", normalized["product_truth"], normalized["template_fidelity"], normalized["visual_evidence"], normalized["decision_coverage"], violations, text)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return VisionEvaluation("INVALID", {}, {}, {}, {}, [], text, str(exc))


def extract_text(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        if "raw_text" in raw:
            return str(raw["raw_text"])
        choices = raw.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content", "") if isinstance(message, dict) else ""
            if isinstance(content, list):
                return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
            return str(content)
        return json.dumps(raw, ensure_ascii=False)
    return str(raw)


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    candidates = [fenced.group(1)] if fenced else []
    candidates.append(cleaned)
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            value, _ = decoder.raw_decode(candidate.lstrip())
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
        start = candidate.find("{")
        while start >= 0:
            try:
                value, _ = decoder.raw_decode(candidate[start:])
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                start = candidate.find("{", start + 1)
            else:
                break
    raise ValueError("no valid JSON object found")


def normalize_section(value: Any, name: str) -> dict[str, Any]:
    """Accept observed model shorthand while keeping uncertainty explicit."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        token = value.strip().upper()
        if token in {"PASS", "FAIL", "PARTIAL", "UNKNOWN", "NEEDS_REVIEW"}:
            return {"status": token, "finding": value}
        return {"status": "NEEDS_REVIEW", "finding": value}
    if isinstance(value, list):
        return {"status": "NEEDS_REVIEW", "findings": [{"observed": str(item), "criterion": name} for item in value]}
    return {"status": "NEEDS_REVIEW", "finding": f"unsupported section value: {type(value).__name__}"}


def normalize_violations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        value = [value]
    result = []
    for item in value:
        if isinstance(item, dict):
            result.append(item)
            continue
        text = str(item)
        lowered = text.lower()
        if any(token in lowered for token in ("scale", "wear context", "size or fit")):
            failure_type = "UNVERIFIED_SCALE"
        elif any(token in lowered for token in ("closure", "hinge", "seam")):
            failure_type = "MISSING_VISUAL_EVIDENCE"
        elif any(token in lowered for token in ("material", "pvd", "titanium", "certification", "test report")):
            failure_type = "UNSUPPORTED_CLAIM"
        else:
            failure_type = "MISSING_VISUAL_EVIDENCE"
        result.append({"criterion": "provider violation", "observed": text, "expected": "request contract", "severity": "medium", "evidence": text, "failure_type": failure_type})
    return result
