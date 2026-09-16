from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

OUT = "presentation_system_business_review.pptx"
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

BG = RGBColor(11, 23, 38)
PANEL = RGBColor(23, 42, 61)
PANEL2 = RGBColor(30, 58, 78)
TEAL = RGBColor(43, 205, 187)
ORANGE = RGBColor(255, 181, 87)
WHITE = RGBColor(243, 247, 250)
MUTED = RGBColor(161, 181, 198)
RED = RGBColor(235, 111, 104)
GREEN = RGBColor(98, 216, 157)
FONT = "PingFang SC"

def txt(s, x, y, w, h, text, size=16, color=WHITE, bold=False, align=PP_ALIGN.LEFT):
    shp = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = shp.text_frame; tf.clear(); tf.word_wrap = True
    tf.margin_left = Inches(.05); tf.margin_right = Inches(.05)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text; r.font.name = FONT; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return shp

def rect(s, x, y, w, h, fill=PANEL, line=None, radius=True):
    typ = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    q = s.shapes.add_shape(typ, Inches(x), Inches(y), Inches(w), Inches(h))
    q.fill.solid(); q.fill.fore_color.rgb = fill; q.line.color.rgb = line or fill
    return q

def arrow(s, x1, y1, x2, y2, color=TEAL, width=2):
    q = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    q.line.color.rgb = color; q.line.width = Pt(width); q.line.end_arrowhead = True
    return q

def image(s, path, x, y, w, h):
    try: s.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    except Exception: rect(s, x, y, w, h, PANEL2)

def pill(s, x, y, w, label, color=TEAL):
    rect(s, x, y, w, .30, color, color); txt(s, x, y, w, .30, label, 10, BG, True, PP_ALIGN.CENTER)

def base(title, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid(); s.background.fill.fore_color.rgb = BG
    txt(s, .65, .26, 11, .20, "PRESENTATION SYSTEM  /  业务主管汇报", 10, TEAL, True)
    txt(s, .65, .55, 12, .65, title, 26, WHITE, True)
    txt(s, .65, 7.10, 8, .18, "Presentation System  |  SKU 内容生产与业务校正", 9, MUTED)
    txt(s, 12.25, 7.08, .45, .18, f"{n:02d}", 10, TEAL, True, PP_ALIGN.RIGHT)
    return s

def notes(s, text):
    tf = s.notes_slide.notes_text_frame; tf.clear(); tf.text = text

# 1 — title
s = base("从 SKU 到内容，再从内容回到业务判断", 1)
txt(s, .78, 1.55, 7.2, .95, "一个 SKU，只理解一次。\n一个判断，贯穿所有内容。", 29, WHITE, True)
txt(s, .80, 3.05, 6.3, .45, "SKU 驱动的跨境电商 AI 内容生产与校正系统", 17, MUTED)
rect(s, 8.15, 1.42, 4.45, 4.55, PANEL)
txt(s, 8.45, 1.72, 3.85, .3, "业务决策链", 18, TEAL, True, PP_ALIGN.CENTER)
chain = ["SKU", "统一判断", "Listing / 图片 / 视频", "业务校正", "经验复用"]
for i, t in enumerate(chain):
    y = 2.23 + i*.62; rect(s, 8.55, y, 3.55, .38, TEAL if i in (0, 1) else PANEL2, TEAL)
    txt(s, 8.60, y, 3.45, .38, t, 13, BG if i in (0,1) else WHITE, True, PP_ALIGN.CENTER)
    if i < 4: arrow(s, 10.32, y+.40, 10.32, y+.57, ORANGE)
txt(s, .80, 5.78, 7.1, .4, "内容不是孤立生成，而是同一套业务判断的不同表达。", 18, ORANGE, True)
notes(s, "这一页先建立认知：我们讨论的不是模型数量，而是一个 SKU 如何被理解、执行、校正并复用。后面所有页面都沿着这条链展开。")

# 2 — pain
s = base("问题不是“不会生成”，而是“生成前没有统一判断”", 2)
txt(s, .82, 1.28, 5.4, .32, "传统内容生产", 17, RED, True)
rect(s, .78, 1.72, 5.55, 3.95, PANEL)
old = ["SKU", "运营分别理解", "写 Listing", "设计图片", "制作视频", "结果层反复修改"]
for i, t in enumerate(old):
    y = 2.02 + i*.52; rect(s, 1.14, y, 4.80, .33, BG if i not in (0,5) else PANEL2, RED if i==5 else PANEL2)
    txt(s, 1.2, y, 4.68, .33, t, 13, WHITE, True, PP_ALIGN.CENTER)
    if i < len(old)-1: arrow(s, 3.54, y+.34, 3.54, y+.48, MUTED)
txt(s, 7.00, 1.28, 5.4, .32, "Presentation System", 17, TEAL, True)
rect(s, 6.93, 1.72, 5.60, 3.95, RGBColor(20, 55, 60))
new = ["SKU", "统一产品事实", "市场 / 消费者问题", "Presentation Strategy", "共享到三种内容", "业务校正上游判断"]
for i, t in enumerate(new):
    y = 2.02 + i*.52; rect(s, 7.28, y, 4.90, .33, TEAL if i in (0,3,5) else PANEL2, TEAL)
    txt(s, 7.34, y, 4.78, .33, t, 13, BG if i in (0,3,5) else WHITE, True, PP_ALIGN.CENTER)
    if i < len(new)-1: arrow(s, 9.73, y+.34, 9.73, y+.48, ORANGE)
txt(s, .9, 6.15, 11.5, .35, "传统方式改的是某句话、某张图；系统方式改的是背后的业务判断。", 17, ORANGE, True, PP_ALIGN.CENTER)
notes(s, "向主管解释失控的根因：每个内容环节都在重新理解 SKU，导致不一致和返工。系统的关键改变是把统一判断放到内容之前，并允许业务回到判断层修改。")

# 3 — core model
s = base("一个 SKU，只建立一次核心判断，后面的内容全部复用", 3)
rect(s, 5.15, 1.14, 3.05, .62, TEAL, TEAL); txt(s, 5.22, 1.31, 2.90, .25, "SKU", 18, BG, True, PP_ALIGN.CENTER)
inputs = [(1.0, "ProductTruth", "我们有什么"), (5.15, "CompetitorInsight", "市场强调什么"), (9.30, "Customer Needs", "消费者关心什么")]
for x, h, v in inputs:
    rect(s, x, 2.18, 3.05, 1.05, PANEL); txt(s, x+.10, 2.40, 2.85, .26, h, 15, TEAL, True, PP_ALIGN.CENTER); txt(s, x+.10, 2.78, 2.85, .24, v, 12, WHITE, False, PP_ALIGN.CENTER); arrow(s, 6.68, 1.78, x+1.52, 2.12, TEAL)
rect(s, 4.02, 3.90, 5.30, .82, ORANGE, ORANGE); txt(s, 4.12, 4.17, 5.10, .28, "Presentation Strategy：我们应该怎么卖？", 18, BG, True, PP_ALIGN.CENTER)
for i, t in enumerate(["Listing Strategy", "Image Strategy", "Video Strategy"]):
    x = 1.0 + i*4.16; rect(s, x, 5.35, 3.05, .68, PANEL2, TEAL); txt(s, x+.08, 5.56, 2.89, .25, t, 14, WHITE, True, PP_ALIGN.CENTER); arrow(s, 6.68, 4.78, x+1.52, 5.30, ORANGE)
txt(s, .90, 6.34, 11.45, .3, "上游负责理解，下游负责执行。内容模块不再各自猜测产品。", 16, ORANGE, True, PP_ALIGN.CENTER)
notes(s, "这是全套 PPT 的中枢图。ProductTruth、CompetitorInsight、Customer Needs 是不同层；它们共同推导 Presentation Strategy，再分别映射到 Listing、图片和视频。")

# 4 — competitor to needs concrete
s = base("竞品不是用来模仿，而是用来发现消费者在担心什么", 4)
image(s, "c1/s2.jpg", .78, 1.42, 3.10, 2.38); txt(s, .86, 3.88, 2.95, .28, "真实竞品画面：四宫格尺寸标签", 12, MUTED, False, PP_ALIGN.CENTER)
rect(s, 4.25, 1.42, 3.55, 2.38, PANEL); txt(s, 4.45, 1.68, 3.15, .28, "画面事实", 15, TEAL, True, PP_ALIGN.CENTER); txt(s, 4.48, 2.18, 3.08, 1.15, "同一鼻部位置\n7 / 8 / 9 / 10mm 数字标签\n重复构图、对比明确", 16, WHITE, True, PP_ALIGN.CENTER)
arrow(s, 3.98, 2.60, 4.18, 2.60, ORANGE)
rect(s, 8.18, 1.42, 4.35, 2.38, RGBColor(47, 43, 31)); txt(s, 8.38, 1.68, 3.95, .28, "可推断的购买问题", 15, ORANGE, True, PP_ALIGN.CENTER); txt(s, 8.40, 2.18, 3.90, 1.15, "我该选多大？\n尺寸与佩戴效果有什么关系？\n我方能证明到什么程度？", 16, WHITE, True, PP_ALIGN.CENTER)
txt(s, .85, 4.36, 11.5, .35, "竞品提供“消费者问题”；ProductTruth 才能决定我方是否可以表达。", 18, ORANGE, True, PP_ALIGN.CENTER)
rect(s, 1.10, 5.03, 4.95, .90, PANEL); txt(s, 1.25, 5.23, 4.65, .22, "消费者问题 → 规格选择疑虑", 14, TEAL, True, PP_ALIGN.CENTER)
rect(s, 7.28, 5.03, 4.95, .90, PANEL); txt(s, 7.43, 5.23, 4.65, .22, "我方事实 → 18G / 20G / 8mm", 14, TEAL, True, PP_ALIGN.CENTER)
arrow(s, 6.18, 5.47, 7.12, 5.47, ORANGE)
txt(s, .9, 6.28, 11.4, .3, "规则：不复制竞品 claim，不从竞品图擅自推断我方身份、比例或安全性。", 13, MUTED, False, PP_ALIGN.CENTER)
notes(s, "用 c1/s2.jpg 讲一个具体推导：我们观察到竞品在反复做尺寸对比，因此提出‘消费者可能在比较尺寸与佩戴效果’。这只是问题线索，最终能否表达，要回到我方 ProductTruth 的 18G、20G、8mm 事实。")

# 5 — prioritization
s = base("从“消费者在意什么”到“我们优先解决什么”", 5)
txt(s, .85, 1.25, 5.6, .30, "G23Studio ASTM F136 铰链鼻中隔环 3 件套", 16, TEAL, True)
qs = [("P0", "产品识别", "我买到的到底是哪三种？"), ("P0", "套装内容", "一套里面到底包含什么？"), ("P0", "规格选择", "18G / 20G / 8mm 怎么理解？"), ("P1", "材质证据", "材质可靠吗？"), ("P1", "结构使用", "铰链卡扣怎么用？"), ("P2", "风格投射", "戴上是什么效果？")]
for i,(p,h,v) in enumerate(qs):
    x = .78 + (i%3)*4.15; y = 1.83 + (i//3)*1.47; rect(s, x, y, 3.65, 1.10, PANEL); pill(s, x+.15, y+.16, .52, p, ORANGE if p=="P0" else (TEAL if p=="P1" else MUTED)); txt(s, x+.82, y+.16, 2.58, .25, h, 15, WHITE, True); txt(s, x+.15, y+.56, 3.28, .30, v, 12, WHITE)
txt(s, .88, 5.42, 11.4, .4, "排序依据：反馈强度 × 竞品强调 × 我方差异化 × ProductTruth 可验证程度 × 业务目标", 15, WHITE, True, PP_ALIGN.CENTER)
txt(s, .92, 6.16, 11.3, .30, "系统决定的不是“做几张图”，而是“哪些购买问题必须被解决”。", 17, ORANGE, True, PP_ALIGN.CENTER)
notes(s, "这里把问题转成优先级。G23 的首版先解决‘买到什么、包含什么、怎么选规格’，再补材质、结构和风格。优先级直接来自 image_plan.json 的 P0/P1/P2。")

# 6 — strategy to three content types
s = base("同一个业务判断，如何同时驱动 Listing、图片和视频？", 6)
rect(s, 4.10, 1.25, 5.15, .76, ORANGE, ORANGE); txt(s, 4.22, 1.49, 4.90, .28, "策略判断：一套多种佩戴方式，先让人看懂材质、结构与效果", 16, BG, True, PP_ALIGN.CENTER)
cards = [("Listing", "标题 / 五点 / 描述\n套装内容、材质、佩戴方式、场景"), ("Images", "六个 Image Task\n识别 → 套装 → 规格 → 材质 → 结构 → 风格"), ("Video", "三段式动作\n展示套装 → 演示结构 → 佩戴结果")]
for i,(h,v) in enumerate(cards):
    x = .92 + i*4.15; rect(s, x, 3.18, 3.42, 1.60, PANEL); txt(s, x+.15, 3.40, 3.12, .28, h, 17, TEAL, True, PP_ALIGN.CENTER); txt(s, x+.18, 3.90, 3.06, .68, v, 13, WHITE, True, PP_ALIGN.CENTER); arrow(s, 6.68, 2.10, x+1.71, 3.12, TEAL)
txt(s, .88, 5.55, 11.5, .42, "不是三个模块分别理解产品，而是一个判断被翻译成三种内容语言。", 18, ORANGE, True, PP_ALIGN.CENTER)
txt(s, .9, 6.20, 11.45, .26, "技术落点（次级信息）：PresentationStrategy → ListingPlan / ImagePlan / VideoPlan", 11, MUTED, False, PP_ALIGN.CENTER)
notes(s, "业务主管最关心‘同一判断是否真的贯穿内容’。以佩戴方式为例，Listing 用文字解释，图片用任务拆解，视频用动作顺序演示；底层引用同一套策略版本。")

# 7 — image task
s = base("图片不是“生成 6 张”，而是“解决 6 个购买问题”", 7)
image(s, "p1/p1.jpg", .78, 1.33, 3.30, 1.65); txt(s, .83, 3.06, 3.18, .28, "一方 canonical asset：三种真实款式", 12, MUTED, False, PP_ALIGN.CENTER)
rows = [("01", "我买到什么？", "产品识别 / 套装展示", "ProductTruth"), ("02", "怎么佩戴？", "多种佩戴方式", "ProductTruth"), ("03", "材质可靠吗？", "材质 / 结构特写", "批准 claim"), ("04", "尺寸适合吗？", "18G / 20G / 8mm", "产品参数"), ("05", "戴起来什么效果？", "真人 / 局部佩戴", "使用场景"), ("06", "实际使用怎样？", "结构 / 场景表达", "使用逻辑")]
for i,(n,q,t,e) in enumerate(rows):
    x=.4+(i%2)*6.20; y=1.30+(i//2)*1.12; rect(s,x+3.8,y,5.55,.84,PANEL); pill(s,x+3.95,y+.16,.42,n,ORANGE if n in ("01","02","04") else TEAL); txt(s,x+4.55,y+.14,1.55,.23,q,13,WHITE,True); txt(s,x+6.08,y+.14,2.25,.23,t,12,WHITE); txt(s,x+8.42,y+.14,.80,.23,e,11,MUTED,False,PP_ALIGN.RIGHT)
txt(s, 4.55, 5.92, 7.62, .34, "消费者问题 → Image Task → Prompt constraints → 生成 → QA → Human Review", 15, ORANGE, True, PP_ALIGN.CENTER)
notes(s, "这一页证明 AI 应用工程化落在‘任务可检查’上。image_plan.json 已为每张图保存 decision_question、customer_need、required facts、模板和 forbidden elements。业务审核时可以问：这张图是否完成了它的购买任务？")

# 8 — full SKU case
s = base("用一个 SKU 看完整决策链：系统一步一步做判断", 8)
stages = [("输入", "G23Studio 3 件套\n产品图 / 规格 / 竞品链接与评论"), ("ProductTruth", "ASTM F136 钛\n18K Gold PVD / 3PCS / 18G·20G / 8mm"), ("CompetitorInsight", "竞品强调材质、舒适、佩戴方式\n低星反馈暴露尺寸与佩戴疑虑"), ("Customer Needs", "我能怎么戴？适合我吗？安全吗？\n戴起来怎样？会不会松？"), ("Presentation Strategy", "P0：识别 + 套装 + 规格\nP1：材质 + 结构 + 风格"), ("Content Tasks", "Listing：标题/五点/描述\nImages：六个任务；Video：动作顺序")]
for i,(h,v) in enumerate(stages):
    x=.52+(i%3)*4.24; y=1.35+(i//3)*2.32; rect(s,x,y,3.75,1.55,TEAL if h in ("ProductTruth","Presentation Strategy") else PANEL,TEAL if h in ("ProductTruth","Presentation Strategy") else PANEL)
    txt(s,x+.15,y+.18,3.45,.28,h,15,BG if h in ("ProductTruth","Presentation Strategy") else TEAL,True,PP_ALIGN.CENTER); txt(s,x+.18,y+.65,3.38,.62,v,12,BG if h in ("ProductTruth","Presentation Strategy") else WHITE,True,PP_ALIGN.CENTER)
for x,y in [(4.32,2.10),(8.56,2.10),(4.32,4.42),(8.56,4.42)]: arrow(s,x,y,x+.38,y,ORANGE)
txt(s,.9,6.30,11.4,.26,"结果重点不是“生成了什么”，而是“为什么优先生成这些内容”。",17,ORANGE,True,PP_ALIGN.CENTER)
notes(s, "这是贯穿全套的 G23 案例。请按输入、事实、竞品、消费者问题、策略、内容任务的顺序讲，突出每向下一层都做了一次业务判断，而不是直接跳到生成。")

# 9 — human calibration
s = base("人工审核不是挑一张好看的，而是定位哪一个判断错了", 9)
image(s, "output/wan_baseline_v1/image_01.png", .75, 1.35, 2.48, 2.25); image(s, "output/wan_baseline_v1/image_02.png", 3.45, 1.35, 2.48, 2.25)
rect(s, 6.45, 1.35, 5.95, 2.25, PANEL); txt(s, 6.68, 1.62, 5.48, .30, "真实 QA：6 张全部 NEEDS_REVIEW", 16, ORANGE, True, PP_ALIGN.CENTER); txt(s, 6.75, 2.08, 5.25, 1.20, "DECISION_NOT_COVERED ×3\nMISSING_VISUAL_EVIDENCE ×6\nUNSUPPORTED_CLAIM ×3\nUNVERIFIED_SCALE ×5", 14, WHITE, True, PP_ALIGN.CENTER)
txt(s, .86, 4.05, 11.4, .32, "结果问题 → 问题归因 → 修改对应变量 → 再执行", 18, TEAL, True, PP_ALIGN.CENTER)
types = [("判断错了", "改 Customer Need Priority"), ("ProductTruth 不充分", "补事实 / 证据"), ("内容任务错误", "改 Image Task"), ("执行偏差", "改约束并重新生成")]
for i,(h,v) in enumerate(types):
    x=.80+(i%2)*6.15; y=4.55+(i//2)*.85; rect(s,x,y,5.55,.62,RGBColor(47, 43, 31) if i==0 else PANEL); txt(s,x+.15,y+.13,1.65,.25,h,14,ORANGE if i==0 else TEAL,True); txt(s,x+1.95,y+.13,3.25,.25,v,13,WHITE,True)
txt(s,.88,6.34,11.4,.27,"系统不是让人修改结果，而是帮助人定位“哪个业务判断需要被修正”。",16,ORANGE,True,PP_ALIGN.CENTER)
notes(s, "这里要诚实呈现真实输出：六张图目前全部需要复审，问题码也很具体。价值不在于假装一次通过，而在于把问题分类到判断、事实、任务或执行层，业务可据此改动。")

# 10 — reuse
s = base("每一次人工校正，都不应该只服务当前 SKU", 10)
items = [("当前 SKU", "生成内容"), ("业务审核", "问题分类"), ("修改变量", "事实 / 问题 / 策略 / 任务 / 约束"), ("再生成", "验证结果"), ("经验沉淀", "Business Rule / Strategy Pattern")]
for i,(h,v) in enumerate(items):
    x=.68+i*2.50; rect(s,x,2.05,2.05,1.28,TEAL if i in (1,4) else PANEL); txt(s,x+.12,2.30,1.80,.25,h,14,BG if i in (1,4) else TEAL,True,PP_ALIGN.CENTER); txt(s,x+.12,2.70,1.80,.27,v,11,BG if i in (1,4) else WHITE,True,PP_ALIGN.CENTER)
    if i<4: arrow(s,x+2.10,2.69,x+2.40,2.69,ORANGE)
txt(s,1.05,4.25,11.2,.52,"SKU A：判断 → 校正 → 沉淀经验\nSKU B：复用已有经验，再根据当前 SKU 调整\nSKU C：继续累积",19,WHITE,True,PP_ALIGN.CENTER)
txt(s,.92,5.78,11.4,.30,"从“人驱动内容生产”，走向“SKU 驱动内容生产”。",20,ORANGE,True,PP_ALIGN.CENTER)
notes(s, "强调长期价值：当前项目已经能保存 HumanEvaluation、问题码、RegenerationTask、版本和 RoleSpec revision。下一步是把这些反馈提炼成品类规则、模板和策略模式，用于下一个 SKU。")

# 11 — manager controls/status
s = base("业务主管不需要管理 AI，而只需要管理几个关键判断", 11)
controls = [("①", "产品事实", "我们到底有什么？"), ("②", "市场问题", "消费者为什么买 / 犹豫？"), ("③", "优先级", "现在最应该解决什么？"), ("④", "内容表达", "Listing / 图片 / 视频是否回答问题？"), ("⑤", "反馈归因", "应改事实、策略、任务还是执行？")]
for i,(n,h,v) in enumerate(controls):
    x=.78+(i%3)*4.15; y=1.45+(i//3)*1.55; rect(s,x,y,3.65,1.12,TEAL if i==4 else PANEL,TEAL if i==4 else PANEL); txt(s,x+.16,y+.18,.42,.26,n,15,BG if i==4 else ORANGE,True); txt(s,x+.70,y+.18,2.72,.26,h,15,BG if i==4 else TEAL,True); txt(s,x+.16,y+.58,3.25,.27,v,12,BG if i==4 else WHITE,True)
txt(s,.88,5.15,11.5,.35,"事实 → 问题 → 优先级 → 内容 → 校正",20,ORANGE,True,PP_ALIGN.CENTER)
txt(s,.92,5.78,11.35,.48,"系统把复杂的 AI 生产过程，压缩成少数可以被业务管理的判断点。",18,WHITE,True,PP_ALIGN.CENTER)
txt(s,.95,6.42,11.3,.20,"可调变量：ProductTruth / Customer Need / Strategy / Image Task / Prompt Constraint / QA 阈值 / 反馈标签",11,MUTED,False,PP_ALIGN.CENTER)
notes(s, "这页把系统交还给业务主管。主管不需要理解模型内部，只要能确认五个判断点是否正确，并能看到哪些变量可调。")

# 12 — close with status
s = base("最终目标：让一个 SKU 的业务判断贯穿整个内容生命周期", 12)
stages = ["SKU", "ProductTruth\n+ CompetitorInsight\n+ + Customer Needs", "Presentation\nStrategy", "Listing\nImages\nVideo", "Business Review", "Correction", "Experience / Rules", "Next SKU"]
for i,t in enumerate(stages):
    x=.52+i*1.58; col=TEAL if i in (0,2,6) else PANEL; rect(s,x,2.18,1.30,1.18,col,TEAL); txt(s,x+.06,2.43,1.18,.65,t,12,BG if col==TEAL else WHITE,True,PP_ALIGN.CENTER)
    if i<7: arrow(s,x+1.32,2.77,x+1.53,2.77,ORANGE)
txt(s,.75,4.35,11.85,.62,"当前已实现：产品事实、竞品采集 MVP、消费者问题/六图 ImagePlan、图片生成、QA、人工校准。",15,WHITE,True,PP_ALIGN.CENTER)
txt(s,.75,5.00,11.85,.62,"建设中：统一 SKU 工作区、Listing 生产/审批、视频工作区、端到端编排。",15,ORANGE,True,PP_ALIGN.CENTER)
txt(s,.88,5.95,11.5,.40,"内容不是独立创作，而是业务判断的表达载体。",22,ORANGE,True,PP_ALIGN.CENTER)
notes(s, "收束时让观众复述完整逻辑：先理解 SKU，再判断消费者问题与卖法，驱动 Listing/图片/视频，业务在关键节点校正，经验继续复用。并明确当前建设边界，保证汇报可信。")

prs.save(OUT)
print(OUT)
