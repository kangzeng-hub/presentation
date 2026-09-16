"""Thin, opt-in Qwen-VL evaluator.

No SDK dependency is required. A caller may inject an HTTP client implementing
``post_json``; the default client uses DashScope's OpenAI-compatible endpoint.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import request as urlrequest

from .parser import parse_qwen_response


QA_SYSTEM_PROMPT = """You are a visual QA evaluator.
Your task is not to improve the image. Evaluate the generated image against the provided GenerationRequest.
Do not invent facts. Do not infer unsupported product specifications. Treat required_visual_evidence as explicit acceptance criteria.
Return JSON only. Do not add markdown. Do not add explanations. Do not wrap JSON in code fences.
Use exactly these top-level keys: product_truth, template_fidelity, visual_evidence, decision_coverage, violations.
Return observations and evidence, not a final overall QA status. Unknown must remain UNKNOWN."""


class QwenVLConfigurationError(RuntimeError):
    pass


class QwenVisionEvaluator:
    def __init__(self, api_key: str | None = None, *, endpoint: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", model: str = "qwen-vl-max", http_client=None, raw_dir=None):
        self.api_key = api_key if api_key is not None else os.getenv("DASHSCOPE_API_KEY")
        self.endpoint = endpoint
        self.model = model
        self.http_client = http_client
        self.raw_dir = Path(raw_dir) if raw_dir else None

    def evaluate(self, request, result, *, canonical_asset=None, template_requirements=None):
        if not self.api_key and self.http_client is None:
            raise QwenVLConfigurationError("DASHSCOPE_API_KEY is not configured")
        image_path = Path(result.output_assets[0].path)
        image = self._data_uri(image_path)
        user_prompt = self._prompt(request, template_requirements or [])
        payload = {"model": self.model, "messages": [{"role": "system", "content": [{"type": "text", "text": QA_SYSTEM_PROMPT}]}, {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image}}, {"type": "text", "text": user_prompt}]}], "temperature": 0}
        response = self._post(payload)
        data = response if isinstance(response, dict) else response.json()
        raw = {"timestamp": datetime.now(timezone.utc).isoformat(), "model": self.model, "generation_id": result.generation_id, "image_id": result.image_id, "request_id": result.request_id, "response": data}
        self._save_raw(result.image_id, raw)
        evaluation = parse_qwen_response(data)
        if evaluation.parse_status != "SUCCESS":
            raise ValueError(evaluation.parse_error or "invalid Qwen output")
        return evaluation.model_dump()

    def _post(self, payload):
        if self.http_client is not None:
            return self.http_client.post_json(payload, 120)
        req = urlrequest.Request(self.endpoint, data=json.dumps(payload, ensure_ascii=False).encode(), method="POST", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        with urlrequest.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode())

    def _save_raw(self, image_id, data):
        if self.raw_dir is None:
            return
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        (self.raw_dir / f"{image_id}.raw.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _data_uri(path):
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"

    @staticmethod
    def _prompt(request, template_requirements):
        return "\n".join(["[DECISION QUESTION]", request.generation_goal, "[REQUIRED FACTS]", *request.required_facts, "[REQUIRED CLAIMS]", *request.required_claims, "[REQUIRED VISUAL EVIDENCE]", *request.required_visual_evidence, "[TEMPLATE REQUIREMENTS]", *template_requirements, "[CONSTRAINTS]", *request.negative_constraints])
