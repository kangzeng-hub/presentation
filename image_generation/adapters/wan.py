"""Wan 2.7 image generation adapter.

The adapter is intentionally a thin execution layer: it maps a
GenerationRequest to DashScope's content-message payload and never rewrites or
re-plans the business prompt.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import struct
import time
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlsplit

from ..models import GenerationRequest, GenerationResult, ModelExecutionPolicy, OutputAsset
from .base import ImageGenerationProvider


DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"


class WanConfigurationError(RuntimeError):
    pass


class WanProviderError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, retryable: bool = False, request_id: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable
        self.request_id = request_id


class ReferenceAssetResolver:
    """Resolve local references to API-supported HTTPS/data representations."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or os.getcwd())

    def resolve(self, asset) -> tuple[str, str]:
        path = str(asset.path)
        if path.startswith("https://") or path.startswith("http://") or path.startswith("data:"):
            return path, self._hash_remote_identifier(path)
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        if not candidate.is_file():
            raise FileNotFoundError(f"reference asset not found: {candidate}")
        raw = candidate.read_bytes()
        mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{encoded}", hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _hash_remote_identifier(value: str) -> str:
        # Remote bytes are not fetched just to calculate idempotency. The URL or
        # data URI itself is a stable, non-secret identifier for this purpose.
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


class _HttpResponse:
    def __init__(self, status_code: int, body: bytes, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.content = body
        self.headers = headers or {}

    def json(self):
        return json.loads(self.content.decode("utf-8")) if self.content else {}


class DashScopeHttpClient:
    def __init__(self, api_key: str, endpoint: str = DEFAULT_ENDPOINT):
        self.api_key = api_key
        self.endpoint = endpoint

    def post_json(self, payload: dict[str, Any], timeout: float):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(self.endpoint, data=body, method="POST", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "X-DashScope-Async": "enable"})
        return self._open(req, timeout)

    def get_json(self, url: str, timeout: float):
        req = urlrequest.Request(url, method="GET", headers={"Authorization": f"Bearer {self.api_key}"})
        return self._open(req, timeout)

    def get_bytes(self, url: str, timeout: float):
        req = urlrequest.Request(url, method="GET")
        return self._open(req, timeout)

    @staticmethod
    def _open(req, timeout):
        try:
            with urlrequest.urlopen(req, timeout=timeout) as response:
                return _HttpResponse(response.status, response.read(), dict(response.headers.items()))
        except urlerror.HTTPError as exc:
            return _HttpResponse(exc.code, exc.read(), dict(exc.headers.items()) if exc.headers else {})


class WanAdapter(ImageGenerationProvider):
    provider = "aliyun_dashscope"

    def __init__(self, api_key: str | None = None, *, endpoint: str = DEFAULT_ENDPOINT, http_client=None, asset_resolver: ReferenceAssetResolver | None = None, output_dir: str | Path = "output"):
        self.api_key = api_key if api_key is not None else os.getenv("DASHSCOPE_API_KEY")
        self.endpoint = endpoint
        self.http = http_client or (DashScopeHttpClient(self.api_key, endpoint) if self.api_key else None)
        self.asset_resolver = asset_resolver or ReferenceAssetResolver()
        self.output_dir = Path(output_dir)

    def generate_task(self, task):
        from ..models import GenerationRequest, LegacyReferenceAsset, ImageResult
        refs = [LegacyReferenceAsset(asset_id=a.asset_id, path=a.path, role=a.role, approved_uses=[a.purpose])
                for a in task.reference_assets if a.allowed_for_generation]
        request = GenerationRequest(generation_id=task.task_id, image_id=task.task_id.replace("gen_", ""), role=task.role,
            template_id=task.composition_spec.layout, product_id=task.sku, reference_assets=refs,
            generation_goal=task.objective, prompt=task.visual_strategy, negative_constraints=task.constraints.must_not_introduce,
            required_visual_evidence=task.qa_requirements.required_visual_evidence, required_facts=task.constraints.must_preserve,
            required_claims=[], asset_limitations=[], generation_metadata={"generation_mode": task.generation_mode})
        result = self.generate(request, ModelExecutionPolicy(policy_id="wan-task", model_id="wan2.7-image-pro"))
        asset = result.output_assets[0]
        return ImageResult(task_id=task.task_id, provider=result.provider, model=result.model, image_path=asset.path,
                           generation_mode=task.generation_mode, metadata=result.model_dump())

    def build_payload(self, request: GenerationRequest, policy: ModelExecutionPolicy) -> tuple[dict[str, Any], dict[str, str]]:
        if policy.model_id != "wan2.7-image-pro":
            raise ValueError(f"WanAdapter only supports wan2.7-image-pro, got {policy.model_id}")
        ordered_assets = list(request.reference_assets)
        if policy.reference_strategy == "canonical_first":
            ordered_assets.sort(key=lambda item: 0 if item.asset_id == "asset_p1_gold_3pcs" else 1)
        if len(ordered_assets) > 9:
            raise ValueError("Wan supports at most 9 reference assets")
        refs: list[dict[str, str]] = []
        file_hashes: dict[str, str] = {}
        for asset in ordered_assets:
            resolved, digest = self.asset_resolver.resolve(asset)
            refs.append({"image": resolved})
            file_hashes[asset.asset_id] = digest
        content = [*refs, {"text": self.compile_prompt(request)}]
        parameters: dict[str, Any] = {"size": policy.size, "n": policy.number_of_images, "watermark": policy.watermark, "enable_sequential": policy.enable_sequential}
        if getattr(policy, "seed", None) is not None:
            parameters["seed"] = policy.seed
        # thinking_mode is not sent for reference-image requests in this baseline.
        if policy.thinking_mode and not refs:
            parameters["thinking_mode"] = True
        return {"model": policy.model_id, "input": {"messages": [{"role": "user", "content": content}]}, "parameters": parameters}, file_hashes

    @staticmethod
    def compile_prompt(request: GenerationRequest) -> str:
        if not request.negative_constraints:
            return request.prompt
        compiled = []
        for item in request.negative_constraints:
            text = str(item).rstrip(".")
            if text.lower().startswith("do not "):
                compiled.append(text + ".")
            elif text.lower().startswith("does not "):
                compiled.append("Do not infer or claim that the reference " + text + ".")
            else:
                compiled.append("Do not include " + text + ".")
        constraints = "\n".join(compiled)
        return f"{request.prompt.rstrip()}\n[DO NOT]\n{constraints}"

    def submit(self, payload: dict, *, timeout: float | None = None):
        if self.http is None:
            raise WanConfigurationError("DASHSCOPE_API_KEY is not configured")
        if hasattr(self.http, "post_json"):
            return self.http.post_json(payload, timeout or 120)
        if hasattr(self.http, "post"):
            return self.http.post(self.endpoint, json=payload, timeout=timeout or 120)
        return self.http("POST", self.endpoint, payload, timeout or 120)

    def get_status(self, task_id: str, *, timeout: float | None = None):
        if self.http is None:
            raise WanConfigurationError("DASHSCOPE_API_KEY is not configured")
        parts = urlsplit(self.endpoint)
        base = f"{parts.scheme}://{parts.netloc}"
        api_prefix = parts.path.split("/api/v1", 1)[0] + "/api/v1" if "/api/v1" in parts.path else ""
        url = f"{base}{api_prefix}/tasks/{task_id}"
        if hasattr(self.http, "get_json"):
            return self.http.get_json(url, timeout or 120)
        if hasattr(self.http, "get"):
            return self.http.get(url, timeout=timeout or 120)
        return self.http("GET", url, None, timeout or 120)

    def download(self, url: str, *, timeout: float | None = None):
        if self.http is None:
            raise WanConfigurationError("DASHSCOPE_API_KEY is not configured")
        if hasattr(self.http, "get_bytes"):
            return self.http.get_bytes(url, timeout or 120)
        if hasattr(self.http, "get"):
            return self.http.get(url, timeout=timeout or 120)
        return self.http("GET", url, None, timeout or 120)

    def generate(self, request: GenerationRequest, policy: ModelExecutionPolicy) -> GenerationResult:
        started = time.monotonic()
        payload, file_hashes = self.build_payload(request, policy)
        prompt_hash = hashlib.sha256(self.compile_prompt(request).encode("utf-8")).hexdigest()
        idem = self._idempotency_key(request, policy, file_hashes)
        existing = self._load_existing(idem)
        if existing is not None:
            request_hash = hashlib.sha256(json.dumps(request.model_dump(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            if not getattr(existing, "request_hash", None):
                existing.request_hash = request_hash
                self._persist(existing)
            return existing
        max_attempts = policy.retry.get("max_attempts", 3) if isinstance(policy.retry, dict) else getattr(policy.retry, "max_attempts", 3)
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.submit(payload, timeout=policy.timeout_seconds)
                data = self._response_json(response)
                request_id = self._request_id(data, response)
                self._raise_for_provider_error(response, data, request_id)
                data = self._poll_if_needed(data, policy)
                output_assets = self._save_outputs(request.image_id, data, policy)
                request_hash = hashlib.sha256(json.dumps(request.model_dump(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
                result = GenerationResult(generation_id=request.generation_id, image_id=request.image_id, provider=self.provider, model=policy.model_id, status="succeeded", output_assets=output_assets, request_id=request_id, latency_ms=int((time.monotonic() - started) * 1000), attempt=attempt, policy_id=policy.policy_id, prompt_hash=prompt_hash, request_hash=request_hash, reference_asset_ids=[a.asset_id for a in request.reference_assets], input_file_hashes=file_hashes, seed=self._seed(data), size=policy.size, idempotency_key=idem, error=None)
                self._persist(result)
                return result
            except WanConfigurationError:
                raise
            except Exception as exc:
                last_error = exc
                retryable = isinstance(exc, (TimeoutError, urlerror.URLError)) or getattr(exc, "retryable", False)
                if attempt >= max_attempts or not retryable:
                    break
                time.sleep(min(2 ** (attempt - 1), 8))
        error = {"type": type(last_error).__name__ if last_error else "ProviderError", "message": str(last_error) if last_error else "unknown error"}
        request_hash = hashlib.sha256(json.dumps(request.model_dump(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        result = GenerationResult(generation_id=request.generation_id, image_id=request.image_id, provider=self.provider, model=policy.model_id, status="failed", output_assets=[], request_id=getattr(last_error, "request_id", None), latency_ms=int((time.monotonic() - started) * 1000), attempt=attempt, policy_id=policy.policy_id, prompt_hash=prompt_hash, request_hash=request_hash, reference_asset_ids=[a.asset_id for a in request.reference_assets], input_file_hashes=file_hashes, size=policy.size, idempotency_key=idem, error=error)
        self._persist(result)
        return result

    def _poll_if_needed(self, data: dict[str, Any], policy: ModelExecutionPolicy) -> dict[str, Any]:
        task_id = data.get("output", {}).get("task_id") or data.get("task_id")
        if not task_id:
            return data
        deadline = time.monotonic() + policy.timeout_seconds
        while time.monotonic() < deadline:
            current = self.get_status(task_id, timeout=policy.timeout_seconds)
            body = self._response_json(current)
            status = str(body.get("output", {}).get("task_status") or body.get("task_status") or "").upper()
            if status in {"SUCCEEDED", "FAILED", "CANCELED"}:
                self._raise_for_provider_error(current, body, self._request_id(body, current))
                return body
            time.sleep(policy.poll_interval_seconds)
        raise TimeoutError(f"timed out waiting for Wan task {task_id}")

    def _save_outputs(self, image_id: str, data: dict[str, Any], policy: ModelExecutionPolicy) -> list[OutputAsset]:
        results = data.get("output", {}).get("results") or data.get("results") or []
        if isinstance(results, dict):
            results = [results]
        urls = [item.get("url") or item.get("image_url") for item in results if isinstance(item, dict)]
        if not urls and data.get("output", {}).get("url"):
            urls = [data["output"]["url"]]
        if not urls:
            choices = data.get("output", {}).get("choices") or data.get("choices") or []
            for choice in choices if isinstance(choices, list) else []:
                message = choice.get("message", {}) if isinstance(choice, dict) else {}
                content = message.get("content", []) if isinstance(message, dict) else []
                for item in content if isinstance(content, list) else []:
                    if isinstance(item, dict) and (item.get("image") or item.get("url")):
                        urls.append(item.get("image") or item.get("url"))
        if not urls:
            raise WanProviderError("provider response did not contain output image URL", request_id=self._request_id(data, None))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        assets = []
        for index, url in enumerate(urls, 1):
            response = self.download(url, timeout=policy.timeout_seconds)
            status = getattr(response, "status_code", 200)
            if status >= 400:
                raise WanProviderError(f"image download failed with HTTP {status}", status_code=status, retryable=status >= 500)
            raw = getattr(response, "content", response if isinstance(response, bytes) else b"")
            filename = f"{image_id}.png" if len(urls) == 1 else f"{image_id}_{index}.png"
            path = self.output_dir / filename
            path.write_bytes(raw)
            width, height = _image_dimensions(raw)
            assets.append(OutputAsset(path=str(path), mime_type="image/png", width=width, height=height, sha256=hashlib.sha256(raw).hexdigest()))
        return assets

    def _persist(self, result: GenerationResult):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        index = self.output_dir / ".generation_index.json"
        try:
            current = json.loads(index.read_text(encoding="utf-8")) if index.exists() else {}
        except (OSError, ValueError):
            current = {}
        current[result.idempotency_key] = result.model_dump()
        index.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.output_dir / f"{result.image_id}.json").write_text(json.dumps(result.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _load_existing(self, key: str):
        index = self.output_dir / ".generation_index.json"
        if not index.exists():
            return None
        try:
            data = json.loads(index.read_text(encoding="utf-8")).get(key)
            if data and data.get("status") == "succeeded" and all(Path(item["path"]).exists() for item in data.get("output_assets", [])):
                assets = [OutputAsset(**item) for item in data.get("output_assets", [])]
                data["output_assets"] = assets
                return GenerationResult(**data)
        except (OSError, ValueError, TypeError, KeyError):
            return None
        return None

    @staticmethod
    def _idempotency_key(request, policy, file_hashes):
        canonical = json.dumps({"request": request.model_dump(), "policy": policy.model_dump(), "reference_file_hashes": file_hashes}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _response_json(response):
        if isinstance(response, dict):
            return response
        try:
            return response.json()
        except (ValueError, TypeError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _request_id(data, response):
        return data.get("request_id") or data.get("requestId") or getattr(response, "headers", {}).get("x-dashscope-request-id")

    @staticmethod
    def _seed(data):
        return data.get("output", {}).get("seed") or data.get("seed")

    @staticmethod
    def _raise_for_provider_error(response, data, request_id):
        status = getattr(response, "status_code", 200)
        code = data.get("code") or data.get("error_code") or data.get("output", {}).get("code")
        message = data.get("message") or data.get("error_message") or data.get("output", {}).get("message")
        task_status = str(data.get("output", {}).get("task_status") or data.get("task_status") or "").upper()
        if status >= 400 or code or task_status in {"FAILED", "CANCELED"}:
            retryable = status == 429 or status >= 500
            raise WanProviderError(message or code or f"HTTP {status}", status_code=status, retryable=retryable, request_id=request_id)


def _image_dimensions(raw: bytes) -> tuple[int | None, int | None]:
    if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
        return struct.unpack(">II", raw[16:24])
    if raw.startswith(b"\xff\xd8"):
        i = 2
        while i + 9 < len(raw):
            if raw[i] != 0xFF:
                i += 1
                continue
            marker = raw[i + 1]
            i += 2
            if marker in (0xD8, 0xD9):
                continue
            if i + 2 > len(raw):
                break
            length = struct.unpack(">H", raw[i:i + 2])[0]
            if marker in range(0xC0, 0xC4):
                if i + 7 <= len(raw):
                    height, width = struct.unpack(">HH", raw[i + 3:i + 7])
                    return width, height
                break
            i += length
    return None, None
