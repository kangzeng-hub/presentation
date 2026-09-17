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

正式本地运行链（FastAPI 是唯一业务后端）：

```bash
./scripts/doctor.sh
./scripts/test.sh
PYTHONPATH=. .venv/bin/uvicorn backend.main:app --reload --port 8000
```

另开终端启动前端：

```bash
cd frontend
npm ci
npm run dev
```

浏览器打开 Vite 输出地址（默认 `http://localhost:5173`）。默认 Demo 不需要 API key。

默认前端地址是 `http://localhost:5173`，API 地址是 `http://localhost:8000`。
`mock-server/` 不属于正式业务链，仅用于离线演示、契约验证和前端无后端开发。

使用 Compose：

```bash
cp .env.example .env   # 可选；真实 provider 才需要填 key
docker compose up --build
```

前端在 `http://localhost:3000`，正式 Workspace API 在 `http://localhost:8000`；`4010` 仅保留给离线 mock-server。

需要单独验证离线 mock-server 时显式启用 profile：

```bash
docker compose --profile offline-demo up demo-backend
```

当前后端使用 SQLite 和本地 `output/` 文件存储，适合单节点/小团队试运行，不等同于已完成多副本水平扩展的生产部署。

## 验证

```bash
./scripts/test.sh
npm --prefix frontend run build
FRONTEND_URL=http://localhost:3000 BACKEND_URL=http://localhost:8000 ./scripts/smoke_test.sh
```

`scripts/test.sh` 使用 Python 标准库 `unittest`，干净环境不需要额外安装 pytest。真实 Wan、Apify、OpenAI-compatible 和 Seedance 调用均为显式 opt-in。

## 公开仓库边界

不会提交 `.env`、虚拟环境、`node_modules`、构建产物、运行输出、PPTX 导出物和客户/产品原始素材。发布前运行：

```bash
./scripts/release_check.sh
```

首次推送前人工确认 `p1/`、`c1/`、`c2/` 和中文资料是否拥有公开授权；它们默认保留在本地而不是公开仓库。

## 架构约束

公开 Demo 的 Product Truth 位于 `examples/demo_sku/`；真实业务资料仍保留在本地并被忽略。`contracts/openapi.yaml` 是 workspace API 合同；`backend/` 是正式 Workspace 与校准/再生 API；`mock-server/` 仅用于离线演示和契约验证。生成产物必须引用版本化的 Product Truth 和 Strategy，不在各模块复制事实。
