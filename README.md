# Presentation Workspace

一个以 Product Truth 为源头、把竞品证据逐步转成 Strategy、Listing、ImagePlan 和 Video Prompt 的可迁移演示工作区。

Python runtime is standardized on 3.12. Install `requirements.txt` for the API,
`requirements-workbench.txt` for Streamlit calibration, `requirements-dev.txt`
for tests, and `requirements-ppt.txt` only for archived PPT tools.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

## 先跑起来

无 Docker 的本地 Demo：

```bash
./scripts/doctor.sh
./scripts/test.sh
node mock-server/server.mjs
```

另开终端启动前端：

```bash
cd frontend
npm ci
npm run dev
```

浏览器打开 Vite 输出地址（默认 `http://localhost:5173`）。默认 Demo 不需要 API key。

使用 Compose：

```bash
cp .env.example .env   # 可选；真实 provider 才需要填 key
docker compose up --build
```

前端在 `http://localhost:3000`，Demo API 在 `http://localhost:4010`，Python 校准 API 在 `http://localhost:8000`。

## 验证

```bash
./scripts/test.sh
npm --prefix frontend run build
FRONTEND_URL=http://localhost:3000 BACKEND_URL=http://localhost:4010 ./scripts/smoke_test.sh
```

`scripts/test.sh` 使用 Python 标准库 `unittest`，干净环境不需要额外安装 pytest。真实 Wan、Apify、OpenAI-compatible 和 Seedance 调用均为显式 opt-in。

## 公开仓库边界

不会提交 `.env`、虚拟环境、`node_modules`、构建产物、运行输出、PPTX 导出物和客户/产品原始素材。发布前运行：

```bash
./scripts/release_check.sh
```

首次推送前人工确认 `p1/`、`c1/`、`c2/` 和中文资料是否拥有公开授权；它们默认保留在本地而不是公开仓库。

## 架构约束

公开 Demo 的 Product Truth 位于 `examples/demo_sku/`；真实业务资料仍保留在本地并被忽略。`contracts/openapi.yaml` 是 workspace API 合同；`mock-server/` 是无需外部服务的确定性演示后端；`backend/` 是独立的校准/再生 API。生成产物必须引用版本化的 Product Truth 和 Strategy，不在各模块复制事实。
