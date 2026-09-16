"""OpenAI-compatible image generation adapter.

The adapter targets the OpenAI Images API exposed by the AIPic-compatible
relay (``/v1/images/generations`` and ``/v1/images/edits``).  Requests always
enable SSE streaming and understand both partial-image and final-image events.
No API key is stored in source code; configure ``OPENAI_API_KEY`` or
``SUB2API_API_KEY`` in the environment.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable
from urllib import error as urlerror
from urllib import request as urlrequest

from ..models import GenerationRequest, GenerationResult, ModelExecutionPolicy, OutputAsset
from ..task_compiler import image_task_from_request
from .base import ImageGenerationProvider
from .wan import ReferenceAssetResolver, _image_dimensions


DEFAULT_BASE_URL = "https://sub2api.simplaj.top"
DEFAULT_MODEL = "gpt-image-2"


class OpenAIConfigurationError(RuntimeError):
    pass


class OpenAIProviderError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, retryable: bool = False, request_id: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable
        self.request_id = request_id


class _HttpResponse:
    def __init__(self, status_code: int, body: bytes = b"", headers: dict[str, str] | None = None, raw=None):
        self.status_code = status_code
        self.content = body
        self.headers = headers or {}
        self.raw = raw

    def json(self):
        return json.loads(self.content.decode("utf-8")) if self.content else {}

    def iter_bytes(self, chunk_size: int = 65536):
        if self.raw is not None:
            while True:
                chunk = self.raw.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        elif self.content:
            yield self.content

    def close(self):
        if self.raw is not None:
            self.raw.close()


class OpenAIHttpClient:
    """Small stdlib-only HTTP client so the project needs no new dependency."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        path = path.lstrip("/")
        root = self.base_url
        if not root.endswith("/v1"):
            root += "/v1"
        return f"{root}/{path}"

    def post_json(self, path: str, payload: dict[str, Any], timeout: float) -> _HttpResponse:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urlrequest.Request(self._url(path), data=body, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        })
        return self._open(req, timeout)

    def post_multipart(self, path: str, fields: dict[str, str], files: list[tuple[str, str, str, bytes]], timeout: float) -> _HttpResponse:
        boundary = f"----codex-{uuid.uuid4().hex}"
        chunks: list[bytes] = []
        for name, value in fields.items():
            chunks.extend([
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                str(value).encode("utf-8"), b"\r\n",
            ])
        for field, filename, mime, content in files:
            chunks.extend([
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(), content, b"\r\n",
            ])
        chunks.append(f"--{boundary}--\r\n".encode())
        req = urlrequest.Request(self._url(path), data=b"".join(chunks), method="POST", headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "text/event-stream, application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        })
        return self._open(req, timeout)

    def get_bytes(self, url: str, timeout: float) -> _HttpResponse:
        req = urlrequest.Request(url, method="GET", headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        })
        return self._open(req, timeout)

    @staticmethod
    def _open(req, timeout):
        try:
            response = urlrequest.urlopen(req, timeout=timeout)
            headers = {k.lower(): v for k, v in response.headers.items()}
            return _HttpResponse(response.status, headers=headers, raw=response)
        except urlerror.HTTPError as exc:
            return _HttpResponse(exc.code, exc.read(), {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])})


class OpenAIImageAdapter(ImageGenerationProvider):
    """Generate images through an OpenAI-compatible relay using SSE streaming."""

    provider = "openai_compatible"

    def __init__(self, api_key: str | None = None, *, base_url: str | None = None, endpoint: str | None = None,
                 http_client=None, asset_resolver: ReferenceAssetResolver | None = None,
                 output_dir: str | Path = "output/openai", on_partial_image: Callable[[str], None] | None = None):
        self.api_key = api_key if api_key is not None else (os.getenv("OPENAI_API_KEY") or os.getenv("SUB2API_API_KEY"))
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("SUB2API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.endpoint = endpoint or f"{self.base_url}/v1/images/generations"
        self.http = http_client or (OpenAIHttpClient(self.api_key, self.base_url) if self.api_key else None)
        self.asset_resolver = asset_resolver or ReferenceAssetResolver()
        self.output_dir = Path(output_dir)
        self.on_partial_image = on_partial_image

    def build_payload(self, request: GenerationRequest, policy: ModelExecutionPolicy) -> tuple[dict[str, Any], dict[str, str]]:
        model = policy.model_id or DEFAULT_MODEL
        if model != DEFAULT_MODEL:
            raise ValueError(f"OpenAIImageAdapter only supports {DEFAULT_MODEL}, got {model}")
        hashes: dict[str, str] = {}
        for asset in request.reference_assets:
            _, digest = self.asset_resolver.resolve(asset)
            hashes[asset.asset_id] = digest
        hints = policy.experimental_hints if isinstance(policy.experimental_hints, dict) else {}
        payload: dict[str, Any] = {
            "model": model,
            "prompt": request.prompt if not request.negative_constraints else self.compile_prompt(request),
            "size": policy.size,
            "n": policy.number_of_images,
            "stream": True,
            "partial_images": int(hints.get("partial_images", 3)),
        }
        if hints.get("quality") is not None:
            payload["quality"] = hints["quality"]
        if hints.get("output_format") is not None:
            payload["output_format"] = hints["output_format"]
        return payload, hashes

    def generate_task(self, task):
        """Execute an ImageTask using the existing OpenAI-compatible implementation."""
        from ..models import LegacyReferenceAsset
        refs = [LegacyReferenceAsset(asset_id=a.asset_id, path=a.path, role=a.role, approved_uses=[a.purpose])
                for a in task.reference_assets if a.allowed_for_generation]
        request = GenerationRequest(generation_id=task.task_id, image_id=task.task_id.replace("gen_", ""), role=task.role,
            template_id=task.composition_spec.layout, product_id=task.sku, reference_assets=refs,
            generation_goal=task.objective, prompt=task.visual_strategy, negative_constraints=task.constraints.must_not_introduce,
            required_visual_evidence=task.qa_requirements.required_visual_evidence, required_facts=task.constraints.must_preserve,
            required_claims=[], asset_limitations=[], generation_metadata={"generation_mode": task.generation_mode})
        policy = ModelExecutionPolicy(policy_id="gpt-image-task", model_id=DEFAULT_MODEL)
        result = self.generate(request, policy)
        from ..models import ImageResult
        asset = result.output_assets[0]
        return ImageResult(task_id=task.task_id, provider=result.provider, model=result.model, image_path=asset.path,
                           generation_mode=task.generation_mode, metadata=result.model_dump())

    @staticmethod
    def compile_prompt(request: GenerationRequest) -> str:
        if not request.negative_constraints:
            return request.prompt
        lines = []
        for item in request.negative_constraints:
            text = str(item).rstrip(".")
            lines.append(text + "." if text.lower().startswith("do not ") else "Do not include " + text + ".")
        return f"{request.prompt.rstrip()}\n[DO NOT]\n" + "\n".join(lines)

    def generate(self, request: GenerationRequest, policy: ModelExecutionPolicy) -> GenerationResult:
        started = time.monotonic()
        payload, file_hashes = self.build_payload(request, policy)
        idem = self._idempotency_key(request, policy, file_hashes)
        existing = self._load_existing(idem)
        if existing is not None:
            return existing
        if self.http is None:
            raise OpenAIConfigurationError("OPENAI_API_KEY or SUB2API_API_KEY is not configured")
        max_attempts = policy.retry.get("max_attempts", 3) if isinstance(policy.retry, dict) else getattr(policy.retry, "max_attempts", 3)
        last_error: Exception | None = None
        attempt = 0
        for attempt in range(1, max_attempts + 1):
            try:
                response = self._submit(request, payload, policy)
                data, inline_images, image_urls = self._parse_response(response, policy)
                request_id = self._request_id(data, response)
                output_assets = self._save_outputs(request.image_id, data, inline_images, image_urls, policy)
                result = GenerationResult(generation_id=request.generation_id, image_id=request.image_id, provider=self.provider,
                    model=policy.model_id, status="succeeded", output_assets=output_assets, request_id=request_id,
                    latency_ms=int((time.monotonic() - started) * 1000), attempt=attempt, policy_id=policy.policy_id,
                    prompt_hash=hashlib.sha256(payload["prompt"].encode()).hexdigest(),
                    request_hash=hashlib.sha256(json.dumps(request.model_dump(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                    reference_asset_ids=[a.asset_id for a in request.reference_assets], input_file_hashes=file_hashes,
                    size=policy.size, idempotency_key=idem, error=None)
                self._persist(result)
                return result
            except OpenAIConfigurationError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= max_attempts or not getattr(exc, "retryable", False):
                    break
                time.sleep(min(2 ** (attempt - 1), 8))
        error = {"type": type(last_error).__name__ if last_error else "ProviderError", "message": str(last_error) if last_error else "unknown error"}
        result = GenerationResult(generation_id=request.generation_id, image_id=request.image_id, provider=self.provider,
            model=policy.model_id, status="failed", output_assets=[], request_id=getattr(last_error, "request_id", None),
            latency_ms=int((time.monotonic() - started) * 1000), attempt=attempt, policy_id=policy.policy_id,
            prompt_hash=hashlib.sha256(payload["prompt"].encode()).hexdigest(), reference_asset_ids=[a.asset_id for a in request.reference_assets],
            input_file_hashes=file_hashes, size=policy.size, idempotency_key=idem, error=error)
        self._persist(result)
        return result

    def _submit(self, request, payload, policy):
        if request.reference_assets:
            files = []
            for index, asset in enumerate(request.reference_assets, 1):
                resolved, _ = self.asset_resolver.resolve(asset)
                if resolved.startswith("data:"):
                    header, encoded = resolved.split(",", 1)
                    raw = base64.b64decode(encoded)
                    mime = header.split(";", 1)[0][5:] or "image/png"
                else:
                    raw = self.http.get_bytes(resolved, policy.timeout_seconds).content
                    mime = mimetypes.guess_type(asset.path)[0] or "image/png"
                files.append(("image[]", f"reference-{index}." + mime.split("/")[-1], mime, raw))
            fields = {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in payload.items()}
            return self.http.post_multipart("images/edits", fields, files, policy.timeout_seconds)
        return self.http.post_json("images/generations", payload, policy.timeout_seconds)

    def _parse_response(self, response, policy) -> tuple[dict[str, Any], list[bytes], list[str]]:
        status = getattr(response, "status_code", 200)
        if status >= 400:
            data = self._response_json(response)
            raise OpenAIProviderError(self._error_message(data, status), status_code=status, retryable=status == 429 or status >= 500, request_id=self._request_id(data, response))
        content_type = str(getattr(response, "headers", {}).get("content-type", "")).lower()
        raw = b"".join(response.iter_bytes()) if hasattr(response, "iter_bytes") else getattr(response, "content", b"")
        try:
            if "text/event-stream" in content_type or b"data:" in raw[:200]:
                return self._parse_sse(raw)
            data = json.loads(raw.decode("utf-8")) if raw else self._response_json(response)
            return data, self._extract_images(data), self._extract_urls(data)
        finally:
            if hasattr(response, "close"):
                response.close()

    def _parse_sse(self, raw: bytes) -> tuple[dict[str, Any], list[bytes], list[str]]:
        final: dict[str, Any] = {}
        images: list[bytes] = []
        urls: list[str] = []
        for block in raw.decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n\n"):
            values = [line[5:].lstrip() for line in block.split("\n") if line.startswith("data:")]
            if not values:
                continue
            text = "\n".join(values).strip()
            if not text or text == "[DONE]":
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("error"):
                raise OpenAIProviderError(self._error_message(event, 500), retryable=True)
            b64 = event.get("b64_json") or event.get("partial_image_b64")
            typ = str(event.get("type", ""))
            if b64 and ("partial" in typ):
                if self.on_partial_image:
                    self.on_partial_image(str(b64))
                continue
            if b64:
                try:
                    images.append(base64.b64decode(str(b64).split(",", 1)[-1]))
                except Exception:
                    pass
            url = event.get("url") or event.get("image_url")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                urls.append(url)
            if event.get("data") or event.get("object", "").endswith("result"):
                final = event
            elif typ.endswith(".completed"):
                final = event
        if not images:
            images = self._extract_images(final)
        if not images:
            urls.extend(self._extract_urls(final))
        if not images and not urls:
            raise OpenAIProviderError("流式接口未返回最终图片数据")
        return final, images, urls

    @staticmethod
    def _extract_images(data: Any) -> list[bytes]:
        values = data.get("data", []) if isinstance(data, dict) else []
        if isinstance(values, dict):
            values = [values]
        images = []
        for item in values if isinstance(values, list) else []:
            if not isinstance(item, dict):
                continue
            value = item.get("b64_json") or item.get("base64") or item.get("image")
            if value:
                try: images.append(base64.b64decode(str(value).split(",", 1)[-1]))
                except Exception: pass
        return images

    @staticmethod
    def _extract_urls(data: Any) -> list[str]:
        values = data.get("data", []) if isinstance(data, dict) else []
        if isinstance(values, dict):
            values = [values]
        urls: list[str] = []
        for item in values if isinstance(values, list) else []:
            if not isinstance(item, dict):
                continue
            value = item.get("url") or item.get("image_url") or item.get("imageUrl")
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                urls.append(value)
        return urls

    def _save_outputs(self, image_id, data, inline_images, image_urls, policy):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        assets = []
        all_outputs: list[bytes] = list(inline_images)
        for url in image_urls:
            response = self.http.get_bytes(url, policy.timeout_seconds)
            status = getattr(response, "status_code", 200)
            if status >= 400:
                raise OpenAIProviderError(f"image download failed with HTTP {status}", status_code=status, retryable=status >= 500)
            raw = getattr(response, "content", response if isinstance(response, bytes) else b"")
            all_outputs.append(raw)
        for index, raw in enumerate(all_outputs, 1):
            filename = f"{image_id}.png" if len(all_outputs) == 1 else f"{image_id}_{index}.png"
            path = self.output_dir / filename
            path.write_bytes(raw)
            width, height = _image_dimensions(raw)
            assets.append(OutputAsset(path=str(path), mime_type="image/png", width=width, height=height, sha256=hashlib.sha256(raw).hexdigest()))
        return assets

    def _persist(self, result):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        index = self.output_dir / ".generation_index.json"
        try: current = json.loads(index.read_text(encoding="utf-8")) if index.exists() else {}
        except (OSError, ValueError): current = {}
        current[result.idempotency_key] = result.model_dump()
        index.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self.output_dir / f"{result.image_id}.json").write_text(json.dumps(result.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _load_existing(self, key):
        index = self.output_dir / ".generation_index.json"
        if not index.exists(): return None
        try:
            data = json.loads(index.read_text(encoding="utf-8")).get(key)
            if data and data.get("status") == "succeeded" and all(Path(item["path"]).exists() for item in data.get("output_assets", [])):
                data["output_assets"] = [OutputAsset(**item) for item in data.get("output_assets", [])]
                return GenerationResult(**data)
        except (OSError, ValueError, TypeError, KeyError):
            return None
        return None

    @staticmethod
    def _idempotency_key(request, policy, file_hashes):
        canonical = json.dumps({"request": request.model_dump(), "policy": policy.model_dump(), "reference_file_hashes": file_hashes}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _response_json(response):
        if isinstance(response, dict): return response
        try: return response.json()
        except (ValueError, TypeError, json.JSONDecodeError): return {}

    @staticmethod
    def _request_id(data, response):
        headers = getattr(response, "headers", {}) or {}
        return data.get("id") or data.get("request_id") or headers.get("x-request-id") or headers.get("x-openai-request-id")

    @staticmethod
    def _error_message(data, status):
        if isinstance(data, dict):
            error = data.get("error")
            if isinstance(error, dict) and error.get("message"): return str(error["message"])
            if data.get("message"): return str(data["message"])
        return f"HTTP {status}"


GPTImageAdapter = OpenAIImageAdapter

__all__ = ["OpenAIImageAdapter", "GPTImageAdapter", "OpenAIHttpClient", "OpenAIConfigurationError", "OpenAIProviderError", "DEFAULT_BASE_URL", "DEFAULT_MODEL"]
