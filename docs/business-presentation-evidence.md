# Presentation System 业务汇报数据真实性说明

## 真实已实现

1. **产品事实与内容约束**：`data/first_party_catalog.json` 注册了产品名称、材质、规格、闭合结构、套装组成、适用位置、品牌视觉策略、批准 claims、证据来源及禁止 claims。`p1/` 中有产品图片、规格清单、审核通过卖点与品牌视觉策略。
2. **竞品采集 MVP**：`competitor_ingestion/*` 支持通过可替换 provider 获取商品信息与 1–3 星评论，进行标准化并写入 provider-independent JSON；文档见 `docs/competitor-ingestion-mvp.md`。这是可运行的 MVP，不等于完整研究编排。
3. **竞品视觉分析输入**：`docs/competitor-visual-analysis.md` 对 `c1/`、`c2/` 素材的构图、信息密度、消费者问题与证据标签进行了分析。
4. **六张图片策略计划**：`image_planning/planner.py`、`image_plan.json` 和 `resolved_templates.json` 将产品目录、竞品分析和模板注册表转成严格六张图计划；每项包含决策问题、消费者需求、策略理由、产品事实、claim、视觉证据、竞品 gap、模板与禁用元素。
5. **图片生成与产品引用约束**：`image_generation/*` 有 typed request/task 编译、provider execution 和 canonical product reference 相关能力；输出物位于 `output/`。
6. **图片 QA、人工校准、再生成与版本历史**：`backend/app.py` 暴露运行、校准、评价、再生成、QA、图片历史、role spec 和问题码接口；`calibration/*` 有人审 verdict、问题码、反馈、再生成任务、版本与 role spec revision。
7. **视频 Prompt 构建**：`video_generation/models.py` 与 `prompt_builder.py` 能基于产品、卖点、消费者关注点、目标场景、参考图片、视频目标与风格构建 15 秒三段式视频 Prompt；`output/video/` 有请求/响应/评审输出。

## 当前观察结果

- 项目已有可追溯的产品事实、竞品输入、图片策略和图片质量闭环。
- 当前前端/HTTP 工作台主要是图片 calibration run browser 与 review form，不是统一 SKU 工作区。
- 当前项目没有可作为业务 KPI 的实测“每 SKU 节省多少小时”“转化提升多少”“ROI 多少”等数据。

## 业务估算/模型化表达

- P2、P4、P8 的重复劳动、沟通和返工逻辑，是根据模块边界和业务流程抽象的效率假设，不是时间研究结论。
- P9 的 10/50/100/500 SKU 仅用于说明规模化逻辑，不代表已测得人员配置、吞吐量或成本曲线。
- “预计可减少重复整理/沟通/试错”可以作为下一阶段业务验证假设，不能当作已验证 ROI。

## 未来规划/建设项

以下内容来自 `docs/system-audit.md` 的“New modules required”与“Recommended implementation order”，在 PPT 中标记为建设中或下一阶段：

- Project/SKU、ProductTruth reference、CompetitorSnapshot、CompetitorInsight、PresentationStrategy、ListingPlan、VideoPlan 等统一领域模型与持久化。
- 研究编排状态（queued/running/completed/failed）与统一工作区 API/前端。
- 一次策略推导同时被 Listing、ImagePlan、VideoPlan 引用。
- Listing 生成/编辑/版本服务。
- VideoPlan 与工作区级视频流程；当前已有视频模型与 Prompt builder，但没有完整 VideoPlan API/UI。
- OpenAPI 合同、生成客户端、mock adapter、端到端 smoke flow。

## 未在 PPT 中声称的能力

- 全自动 Agent、全链路无人值守、自动发布 Amazon、100% 自动生成。
- 已验证的 ROI、转化率提升、上市周期缩短比例。

## 第二轮新增证据

- `image_plan.json` 中六项图片任务已经落到真实消费者问题：产品识别、套装内容、规格选择、材质证据、结构使用、风格投射；每项同时包含 `decision_question`、`customer_need`、策略理由、事实、视觉证据与禁用元素。
- 本轮使用真实 QA 结果 `output/wan_baseline_v1/qa/qa_summary.json`：6 张图全部为 `needs_review`，问题包括 `DECISION_NOT_COVERED` 3、`MISSING_VISUAL_EVIDENCE` 6、`UNSUPPORTED_CLAIM` 3、`UNVERIFIED_SCALE` 5。这被用于说明“业务校正为何必要”，没有包装为成功率。
- `calibration.models.HumanEvaluation`、`RegenerationTask`、`RoleSpecRevision` 证明业务反馈可以保存为 verdict、问题码、保留/修改/禁止项、再生成任务、版本和规则修订；这代表可沉淀反馈，不等于自动学习。
- `output/video/review.json` 当前 `usable: false`，原因是 Seedance submit 未返回 task_id；因此新版 PPT 将完整视频工作区明确标为建设中，只表达当前 Prompt 构建能力。

## 第三轮新增链路证据

- `presentation_domain/models.py` 已定义 `ProductTruth`、`CompetitorSnapshot`、`CompetitorInsight`、`PresentationStrategy`、`ListingPlan`、`ImagePlanRef`、`ImageGenerationRef`、`ImageQARef`、`HumanReview`、`VideoPlan`、`Project`，并对版本引用、状态和来源做校验。
- `contracts/openapi.yaml` 已定义从 `/projects/{project_id}/competitor-research`、`competitor-insight`、`strategy`、`listing`、`images/plan`、`images/generate` 到 `video/plan` 的工作区合同。
- `mock-server/server.mjs` 已提供可跑通的工作区演示链路：竞品抓取 → Insight → Strategy → Listing（标题、5 条 bullet、product description）→ ImagePlan/图片生成状态 → VideoPlan；这属于 mock/workspace 演示，不等同于所有 provider 已生产化。
- `frontend/src/main.tsx` 已有 Research、Listing、Images、Video 页面；Listing 页面显示标题、Bullet 1–5、Description 与版本/strategy 引用；Video 页面明确显示“Video Plan ready — no video API is being called”。
- `output/generation_requests.json` 与 `image_plan.json` 提供主图/橱窗图的 source asset、generation goal、required facts、visual evidence、negative constraints 和模板策略。
- 主图/橱窗图人工接入依据：`calibration.models.HumanEvaluation` 中的 `preserve`、`change`、`dont_introduce`、`regeneration_instruction`；`RegenerationTask` 保存校正快照、Prompt、QA 与生成状态。P19 使用 `output/wan_baseline_v1` 与 `output/gpt_image_2_from_wan` 的真实输出做“首轮/再生成样例”对比，并明确不等于业务验收通过。

## 第五轮竞品比对推导证据

- 第 5 页使用 `c1/s2.jpg`：同一鼻部近景按四个相同构图比较 18g/7mm、18g/8mm、18g/9mm、18g/10mm。可观察事实是重复对比、数字标签和同一解剖位置；“消费者可能在比较尺寸与佩戴效果”属于基于画面结构的业务推断，不冒充用户调研数据。
- 该推断与我方 `image_plan.json` 的 `image_03` 对齐：`decision_question` 为“18G / 20G / 8mm 怎么理解？”，`customer_need` 为减少规格、内径和适用位置选择疑惑，模板为 `SIZE_CHOICE_PROOF`。
- `data/first_party_catalog.json` 只确认我方 18G、20G、8mm 和批准适用位置；产品主图限制明确“不证明佩戴比例”。因此 PPT 明确竞品素材只用于发现消费者问题/表达模式，不能作为我方产品身份、尺寸或 claims 的来源。

## 第六轮内容策略证据

- 内容策略页使用 `data/first_party_catalog.json` 的三件套、材质、结构与规格事实；使用 `docs/competitor-visual-analysis.md` 的套装分组、尺寸近景、结构示意、三联风格等竞品表达模式；使用 `image_plan.json` 的 P0/P1 优先级、decision_question、customer_need、template 与 forbidden elements。
- P0/P1/P2 排序直接来自 catalog 的 `priority_plan`：P0 为产品识别、套装内容、规格选择；P1 为材质、结构、款式/风格；P2 为 lifestyle。PPT 将这一排序翻译为“先解决买到什么、能否选对，再补信任与风格”。
- Listing 标题、五点、描述的映射依据 `presentation_domain.ListingPlan`、`contracts/openapi.yaml` 和 `mock-server/server.mjs` 中的真实字段与示例内容；PPT 同时标注生产级 provider/正式审批边界。
- 图片映射依据 `image_plan.json` 六个任务；视频动作依据 `video_generation/prompt_builder.py` 的三段式动作顺序和 `frontend/src/main.tsx` 的 VideoPlan 场景示例。
- 已完成的统一 Listing 工作区、完整视频工作区、端到端研究编排。
