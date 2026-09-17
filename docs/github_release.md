# GitHub 发布与迁移清单

## 发布前必须通过

1. `./scripts/doctor.sh`：检查本机工具和公开目录结构。
2. `./scripts/test.sh`：运行标准库单元测试。
3. `npm --prefix frontend run build`：确认前端类型检查和生产构建。
4. `./scripts/smoke_test.sh`：确认前端、Demo API、健康检查和 demo project 可访问。
5. `./scripts/release_check.sh`：检查 secrets、Compose 配置、测试和前端构建。
6. `git diff --cached --name-only`：逐项确认没有 `.env`、PPTX、运行输出或未授权素材。

## 推荐的首个公开边界

公开：Python/Node 源码、schemas、contracts、templates、examples/demo_sku、测试、脚本和文档。

默认不公开：`output/`、`frontend/dist/`、虚拟环境、原始产品/竞品图片、客户材料和 PPTX 导出物。若要展示视觉效果，新增完全合成的 `examples/` 资产，并在旁边写明授权和来源。

## 迁移原则

- 从项目根目录运行命令；FastAPI 是正式 Workspace API，默认监听 8000。
- 前端请求以 `VITE_API_BASE_URL` 为唯一入口；开发代理和 Compose 都指向 8000 FastAPI。4010 仅用于 mock-server 的离线契约验证。
- 默认 `docker compose up` 不启动 mock-server；仅 `--profile offline-demo` 显式启用。
- provider key 只通过环境变量注入；默认路径不触发外部网络调用。
- Product Truth、Competitor Insight、Strategy 通过版本号串联下游，避免 Listing/Image/Video 复制事实。

## 当前规模边界

当前持久化方案是单节点 SQLite 加本地文件系统，适合本地演示、单节点部署和小团队试运行。它尚不适合多副本水平扩展、跨机器共享文件或高并发生产任务；规模化部署前需要迁移到共享数据库、对象存储和独立任务队列，并重新验证租约、并发和备份策略。
