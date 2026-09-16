from __future__ import annotations

import json, os, time
from pathlib import Path
from urllib import error, request

DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"


class SeedanceAdapter:
    def __init__(self, api_key=None, model=None, endpoint=None, output_dir="output/video", timeout=900, poll_interval=5, retries=2):
        self.api_key = api_key or os.getenv("ARK_API_KEY") or self._dotenv("ARK_API_KEY")
        self.model = model or os.getenv("SEEDANCE_MODEL_ID") or self._dotenv("SEEDANCE_MODEL_ID") or "doubao-seedance-2-5-260628"
        self.endpoint = endpoint or os.getenv("SEEDANCE_API_ENDPOINT", DEFAULT_ENDPOINT)
        self.output_dir = Path(output_dir); self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timeout, self.poll_interval, self.retries = timeout, poll_interval, retries

    @staticmethod
    def _dotenv(key):
        path = Path(".env")
        if not path.is_file(): return None
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(key + "="): return line.split("=", 1)[1].strip().strip('"').strip("'")
        return None

    def _call(self, method, url, payload=None, timeout=60):
        if not self.api_key: return {"status_code": 0, "body": {}, "error": {"type": "configuration", "message": "ARK_API_KEY is not configured"}}
        data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
        req = request.Request(url, data=data, method=method, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=timeout) as r: raw = r.read(); return {"status_code": r.status, "body": json.loads(raw or b"{}")}
        except error.HTTPError as e:
            raw = e.read();
            try: body = json.loads(raw or b"{}")
            except Exception: body = {"raw": raw.decode(errors="replace")}
            return {"status_code": e.code, "body": body, "error": {"type": "http", "message": str(e)}}
        except Exception as e: return {"status_code": 0, "body": {}, "error": {"type": "network", "message": str(e)}}

    def submit(self, prompt, reference_images=None):
        payload = {"model": self.model, "content": [{"type": "text", "text": prompt}]}
        if reference_images: payload["content"].extend({"type": "image_url", "image_url": {"url": str(x)}} for x in reference_images)
        for attempt in range(self.retries + 1):
            result = self._call("POST", self.endpoint, payload)
            if result["status_code"] < 500 and result["status_code"] != 0: break
            if attempt < self.retries: time.sleep(2 ** attempt)
        result["request"] = payload
        result["task_id"] = self._task_id(result["body"])
        return result

    def get_status(self, task_id):
        return self._call("GET", f"{self.endpoint.rstrip('/')}/{task_id}")

    def wait_for_completion(self, task_id):
        deadline = time.monotonic() + self.timeout
        latest = None
        while time.monotonic() < deadline:
            latest = self.get_status(task_id); body = latest.get("body", {}); status = str(body.get("status", body.get("state", ""))).lower()
            if status in {"succeeded", "success", "completed", "failed", "error", "cancelled"}: return latest
            time.sleep(self.poll_interval)
        return {"status_code": 0, "body": latest.get("body", {}) if latest else {}, "error": {"type": "timeout", "message": f"timed out waiting for task {task_id}"}}

    def download_result(self, response, filename="result.mp4"):
        url = self._video_url(response.get("body", response))
        if not url: return {"error": {"type": "response", "message": "video URL not found", "body": response}}
        try:
            with request.urlopen(request.Request(url), timeout=120) as r: data = r.read()
            path = self.output_dir / filename; path.write_bytes(data); return {"path": str(path), "url": url}
        except Exception as e: return {"error": {"type": "download", "message": str(e), "url": url}}

    @staticmethod
    def _task_id(body):
        for key in ("id", "task_id"):
            if body.get(key): return body[key]
        return (body.get("data") or {}).get("id") or (body.get("task") or {}).get("id")

    @staticmethod
    def _video_url(body):
        for obj in (body, body.get("data", {}), body.get("content", {}), body.get("output", {})):
            if isinstance(obj, dict):
                for key in ("video_url", "url", "download_url"):
                    if isinstance(obj.get(key), str): return obj[key]
        return None
