# 规模化、迁移与 GitHub 发布审计

审计日期：2026-09-16

## 结论

当前代码已经可以作为“确定性本地 Demo + Python 能力模块集合”发布，但还不是可水平扩展的生产系统。第一轮已经修复了干净 clone 会直接失败的入口问题；下一轮最有效的投入不是继续加页面，而是统一后端、持久化和任务状态。

## P0：已落地的发布阻断

### 1. 本地依赖掩盖了不可复现安装

逻辑链：本地存在 `node_modules` → `npm run build` 成功 → 误以为干净环境可用 → 实际 `package.json` 与 lockfile 不同步，`npm ci` 失败 → CI、Docker 和其他开发者无法启动。

解决：同步 lockfile、固定前端直接依赖版本、release check 强制先执行 `npm ci`，并加入 GitHub Actions。

### 2. 测试入口与测试体系不一致

逻辑链：测试全部使用标准库 `unittest` → `scripts/test.sh` 却调用未声明的 pytest → 新机器立即失败 → 发布检查没有可信基线。

解决：统一为 `python -m unittest discover`。当前结果为 80 个测试通过，1 个真实 Wan 集成测试按设计跳过。

### 3. Demo server 依赖调用者当前目录

逻辑链：server 用 `process.cwd()` 拼合同路径 → 从 `frontend/` 启动能跑、从仓库根目录启动失败 → Docker/CLI/IDE 行为不一致 → 迁移后随机报找不到合同。

解决：按 `server.mjs` 自身位置解析合同，Docker 显式注入 `CONTRACT_PATH`。

### 4. 两套 API 入口互相冲突

逻辑链：浏览器客户端默认指向 4010 workspace API → Vite `/api` 代理却指向 8000 calibration API → 开发与 Compose 行为不同 → 接口问题只能在特定启动方式下复现。

解决：workspace UI 和开发代理统一指向 4010；8000 明确只保留为校准/再生 API。

### 5. 发布检查会产生假绿灯

逻辑链：smoke test 的前端 curl 失败后继续执行 → 最后仍打印 passed → 发布者获得错误信心。

解决：任何端点不可达立即退出非零；已验证成功路径返回 0、失败路径返回 1。

### 6. 密钥与素材边界不明确

逻辑链：本地 `.env` 含真实凭据，目录中还有真实产品/竞品图片 → 直接 `git add .` 可能泄密或侵权 → Git 历史一旦推送很难彻底清理。

解决：`.env`、输出、PPTX、`p1/`、`c1/`、`c2/` 默认忽略；Docker build context 同样排除这些内容；公开演示只使用 `examples/demo_sku/`。首次提交前仍需人工审阅 staged files。

## P1：规模化的主要结构问题

### 1. 两个后端不是同一产品后端

`mock-server/` 实现 workspace 全流程但只存内存；`backend/` 实现真实校准/再生但不实现 workspace 合同。结果是 UI 演示能力和真实生成能力无法共享项目、状态、权限和错误模型。

最有效方案：以 `contracts/openapi.yaml` 为边界，把 workspace routes 落到 Python API；Node mock 仅作为 contract fixture 保留。不要继续在两个后端重复业务逻辑。

### 2. 项目状态不可持久化、不可并发

Node Map 在进程重启后丢失；生成接口同步返回“completed”；没有租约、重试、幂等键或 worker。多 SKU 或多人操作时会出现丢数据、重复调用 provider、状态覆盖。

最有效方案：先用 SQLite/PostgreSQL 持久化 Project、ArtifactVersion、Job、Review；耗时任务进入队列；以 `project_id + stage + input_version` 作为幂等边界。

### 3. 数据合同仍然过于宽松

OpenAPI 中大量 `object` 和前端 `any` 让字段漂移无法在编译期被发现；此前 Insight 响应类型和 VideoPlan 版本类型已发生实际漂移。

最有效方案：补全 schema，CI 中重新生成 TypeScript client 后检查 working tree 必须无差异；逐步移除 `(client as any)` 与组件 props 的 `any`。

### 4. Product Truth 与私有案例耦合

运行默认仍围绕单一 G23 案例，部分生成请求和文档引用本地素材。若直接扩展 SKU，只会复制 JSON 和脚本，最终出现事实不一致。

最有效方案：公开路径统一改用 `examples/demo_sku`；真实 SKU 进入外部数据目录或对象存储；所有下游只保存 `product_truth_version` 和证据引用。

### 5. 输出目录承担数据库职责

校准 API 通过扫描 `output/` 发现 run，目录结构就是隐式合同。文件一多，扫描成本、损坏恢复、权限和并发写入都会恶化。

最有效方案：保留对象文件，但把索引、版本和状态写入数据库；文件路径只作为 artifact locator，不再作为业务状态源。

## 推荐实施顺序

1. 建立首个 Git 仓库和 CI，只提交公开边界内文件。
2. 给 OpenAPI 补齐严格 schema 与生成校验。
3. 在 Python API 内实现 Project/Job/ArtifactVersion 持久化。
4. 把 workspace UI 从 Node mock 切到 Python routes。
5. 增加队列、幂等、失败重试和 provider observability。
6. 用第二个完全合成 SKU 做迁移验收；没有第二 SKU 的通过，不能称为可迁移。
