# GPT Image 2 中转配置

默认生图服务为 OpenAI 兼容接口：

- Base URL: `https://sub2api.simplaj.top`
- Model: `gpt-image-2`
- Endpoint: `/v1/images/generations`（文生图）或 `/v1/images/edits`（带参考图）
- 传输：SSE 流式，`stream=true`，默认请求 3 个 partial image

API Key 不保存在仓库。运行前设置环境变量：

```bash
export OPENAI_API_KEY='<your-api-key>'
export OPENAI_BASE_URL='https://sub2api.simplaj.top'
```

执行全部请求：

```bash
python -m image_generation.cli generate \
  --requests generation_requests.json \
  --policy config/openai_gpt_image_v2.json \
  --output-dir output/gpt_image_2
```

先检查请求体而不调用接口：

```bash
python -m image_generation.cli generate \
  --requests generation_requests.json \
  --policy config/openai_gpt_image_v2.json \
  --image-id image_01 --dry-run
```

如需继续使用 Wan，传入 `--provider wan` 并使用 Wan policy。
