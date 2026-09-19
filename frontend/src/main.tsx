import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowRight,
  BarChart3,
  Check,
  CheckCircle2,
  CircleDot,
  Clapperboard,
  ClipboardCheck,
  Copy,
  Database,
  FileText,
  Image as ImageIcon,
  Layers3,
  LoaderCircle,
  PackageCheck,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react';
import './styles.css';
import { apiService, type Workspace } from './api/service';
import type { components } from './generated/api';
import PortfolioApp from './PortfolioApp';

type Competitor = components['schemas']['CompetitorSnapshot'];
type Insight = components['schemas']['CompetitorInsight'];
type Listing = components['schemas']['ListingPlan'];
type Video = components['schemas']['VideoPlan'];
type VideoInput = components['schemas']['VideoPlanInput'];
type Scene = { scene?: number; action?: string; [key: string]: unknown };
type ImageItem = {
  image_id: string;
  role?: string;
  action?: string;
  priority?: string;
  prompt?: string;
  generation_status?: string;
  qa_status?: string;
  human_review_status?: string;
};
type ImagePlanPayload = { images: ImageItem[]; plan_version?: string; product_id?: string; strategy_summary?: string };
type WorkspaceProps = { w: Workspace; refresh: () => Promise<void> };
type NavItem = { id: string; label: string; shortLabel: string; icon: LucideIcon };

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
const nav: NavItem[] = [
  { id: 'overview', label: '项目总览', shortLabel: '总览', icon: BarChart3 },
  { id: 'research', label: '竞品研究', shortLabel: '研究', icon: Search },
  { id: 'listing', label: '商品文案', shortLabel: '文案', icon: FileText },
  { id: 'images', label: '图片规划', shortLabel: '图片', icon: ImageIcon },
  { id: 'video', label: '视频方案', shortLabel: '视频', icon: Clapperboard },
];

const stageLabels: Record<string, string> = {
  product_truth: '产品资料', research: '竞品研究', insight: '洞察提炼', strategy: '内容策略', listing: '商品文案', images: '图片生产', video: '视频方案',
};
const statusLabels: Record<string, string> = {
  queued: '等待中', running: '处理中', completed: '已完成', failed: '失败', cancelled: '已取消', pending: '待处理', pending_review: '待审核', approved: '已批准', rejected: '已驳回', NEEDS_REVIEW: '待复核',
};
const roleLabels: Record<string, string> = {
  identity: '主视觉', feature: '核心卖点', usage: '使用场景', material: '材质证明', size: '尺寸与适配', package: '包装与价值',
};

const messageOf = (error: unknown) => error instanceof Error ? error.message : '请求失败，请稍后重试。';
const statusLabel = (status?: string | null) => statusLabels[status || ''] || status || '未开始';
const statusTone = (status?: string | null) => ['completed', 'approved', 'PASS'].includes(status || '') ? 'success' : ['failed', 'rejected'].includes(status || '') ? 'danger' : status === 'running' ? 'running' : 'neutral';
const assetUrl = (path?: string) => path ? `${apiBaseUrl}/api/assets/${path.split('/').map(encodeURIComponent).join('/')}` : '';

function StatusBadge({ status, label }: { status?: string | null; label?: string }) {
  return <span className={`status-badge ${statusTone(status)}`}><CircleDot size={12} />{label || statusLabel(status)}</span>;
}

function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return <div className="page-header"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>{action && <div className="page-actions">{action}</div>}</div>;
}

function App() {
  const [workspace, setWorkspace] = useState<Workspace>();
  const [loadError, setLoadError] = useState('');
  const pathParts = location.pathname.split('/').filter(Boolean);
  const pathStage = pathParts[pathParts.length - 1] || 'overview';
  const [stage, setStage] = useState(nav.some(item => item.id === pathStage) ? pathStage : 'overview');
  const projectId = location.pathname.match(/^\/projects\/([^/]+)/)?.[1] || 'demo-project';

  const loadWorkspace = async () => {
    try { setLoadError(''); setWorkspace(await apiService.getProject(projectId)); }
    catch (error) { setLoadError(messageOf(error)); }
  };
  const refresh = async () => { if (workspace?.project_id) setWorkspace(await apiService.getProject(workspace.project_id)); };
  useEffect(() => { void loadWorkspace(); }, []);
  useEffect(() => {
    const syncStageFromUrl = () => {
      const parts = location.pathname.split('/').filter(Boolean);
      const next = parts[parts.length - 1] || 'overview';
      setStage(nav.some(item => item.id === next) ? next : 'overview');
    };
    window.addEventListener('popstate', syncStageFromUrl);
    return () => window.removeEventListener('popstate', syncStageFromUrl);
  }, []);

  if (loadError) return <main className="center-state"><TriangleAlert size={28} /><h1>工作区加载失败</h1><p>{loadError}</p><button className="button primary" onClick={() => void loadWorkspace()}><RefreshCw size={16} />重新加载</button></main>;
  if (!workspace) return <main className="center-state"><LoaderCircle className="spin" size={28} /><h1>正在加载工作区</h1><p>正在读取项目、产物和任务状态。</p></main>;

  const go = (nextStage: string) => {
    history.pushState({}, '', `/workspace/${nextStage}`);
    setStage(nextStage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return <div className="app">
    <header className="topbar">
      <div className="brand-mark"><Layers3 size={20} /><span>演示内容工作台</span></div>
      <div className="project-heading"><strong>{workspace.project_name}</strong><span>{workspace.sku}</span></div>
      <div className="topbar-meta"><span>当前阶段：{stageLabels[workspace.current_stage] || workspace.current_stage}</span><StatusBadge status={workspace.overall_status} /></div>
    </header>
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-title"><span>生产流程</span><small>SKU 内容生产</small></div>
        <nav>{nav.map(({ id, label, icon: Icon }) => <button className={stage === id ? 'active' : ''} onClick={() => go(id)} key={id}><Icon size={17} /><span>{label}</span><ArrowRight size={15} className="nav-arrow" /></button>)}</nav>
        <Context w={workspace} />
      </aside>
      <main className="content">
        {stage === 'overview' ? <Overview w={workspace} go={go} /> : stage === 'research' ? <Research w={workspace} refresh={refresh} /> : stage === 'listing' ? <ListingView w={workspace} refresh={refresh} /> : stage === 'images' ? <Images w={workspace} refresh={refresh} /> : <VideoView w={workspace} refresh={refresh} />}
      </main>
    </div>
    <nav className="mobile-nav">{nav.map(({ id, shortLabel, icon: Icon }) => <button className={stage === id ? 'active' : ''} onClick={() => go(id)} key={id}><Icon size={18} /><span>{shortLabel}</span></button>)}</nav>
  </div>;
}

function Overview({ w, go }: { w: Workspace; go: (stage: string) => void }) {
  const image = assetUrl(w.product_truth?.product_images?.[0]);
  const stages = [
    { label: '竞品研究', ready: Boolean(w.competitors?.length) },
    { label: '内容策略', ready: Boolean(w.strategy) },
    { label: '商品文案', ready: Boolean(w.listing) },
    { label: '图片规划', ready: Boolean(w.image_plan) },
    { label: '视频方案', ready: Boolean(w.video) },
  ];
  return <>
    <PageHeader eyebrow="项目概览" title="内容生产总览" description="围绕一个 SKU，统一查看产品事实、策略与各类内容产物。" action={<button className="icon-button" title="刷新数据" onClick={() => location.reload()}><RefreshCw size={18} /></button>} />
    <section className="product-hero">
      <div className="product-visual">{image ? <img src={image} alt={w.product_truth?.product_name || '产品图'} /> : <PackageCheck size={44} />}</div>
      <div className="product-summary"><p className="eyebrow">当前产品</p><h2>{w.product_truth?.product_name}</h2><div className="meta-row"><span>SKU：{w.sku}</span><span>版本：v{w.product_truth?.version || 1}</span></div><p>{String(w.product_truth?.material?.base || '尚未填写材质信息')}</p></div>
      <button className="button primary" onClick={() => go('research')}>继续生产<ArrowRight size={16} /></button>
    </section>
    <section className="section-block"><div className="section-heading"><div><p className="eyebrow">流程进度</p><h2>从资料到交付内容</h2></div><span className="completion">{stages.filter(item => item.ready).length} / {stages.length} 已完成</span></div><div className="pipeline">{stages.map((item, index) => <div className={`pipeline-step ${item.ready ? 'done' : ''}`} key={item.label}><span className="step-index">{item.ready ? <Check size={15} /> : index + 1}</span><span>{item.label}</span></div>)}</div></section>
    <section className="summary-grid">
      <div className="summary-item"><Database size={19} /><div><span>竞品证据</span><strong>{w.competitors?.length || 0} 条</strong></div></div>
      <div className="summary-item"><FileText size={19} /><div><span>商品文案</span><strong>{w.listing ? `v${w.listing.version}` : '待生成'}</strong></div></div>
      <div className="summary-item"><ImageIcon size={19} /><div><span>图片方案</span><strong>{w.image_plan ? '已生成' : '待生成'}</strong></div></div>
      <div className="summary-item"><ClipboardCheck size={19} /><div><span>审批记录</span><strong>{w.approvals?.length || 0} 条</strong></div></div>
    </section>
    <section className="section-block"><div className="section-heading"><div><p className="eyebrow">当前策略</p><h2>内容表达优先级</h2></div></div>{w.strategy ? <ol className="priority-list">{w.strategy.priority_order.map((value: string, index: number) => <li key={value}><span>{index + 1}</span><p>{value}</p></li>)}</ol> : <EmptyState icon={Sparkles} title="还没有内容策略" description="完成竞品研究后，系统会在这里给出表达优先级。" action={<button className="button secondary" onClick={() => go('research')}>前往竞品研究</button>} />}</section>
  </>;
}

function Context({ w }: { w: Workspace }) {
  return <details className="context-panel" open><summary>项目上下文</summary><div className="context-section"><span>产品事实</span><strong>{w.product_truth?.product_name}</strong><small>{w.sku}</small></div><div className="context-section"><span>竞品洞察</span><p>{(w.competitor_insight?.purchase_drivers || ['尚未生成']).join(' · ')}</p></div><div className="context-section"><span>表达策略</span><p>{(w.strategy?.core_differentiators || ['尚未生成']).join(' · ')}</p></div></details>;
}

function EmptyState({ icon: Icon, title, description, action }: { icon: LucideIcon; title: string; description: string; action?: React.ReactNode }) {
  return <div className="empty-state"><Icon size={24} /><h3>{title}</h3><p>{description}</p>{action}</div>;
}

function Research({ w, refresh }: WorkspaceProps) {
  const [urls, setUrls] = useState('https://www.amazon.com/dp/COMPETITOR_A\nhttps://www.amazon.com/dp/COMPETITOR_B');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState('');
  const run = async () => { try { setBusy('research'); setMessage(''); const job = await apiService.startResearch(w.project_id, urls.split('\n').map(value => value.trim()).filter(Boolean)); if (job.job_id) await apiService.waitForJob(job.job_id); await refresh(); setMessage('竞品证据已更新。'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(''); } };
  const insight = async () => { try { setBusy('insight'); setMessage(''); await apiService.generateInsight(w.project_id); await refresh(); setMessage('竞品洞察已生成。'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(''); } };
  const strategy = async () => { try { setBusy('strategy'); setMessage(''); await apiService.generateStrategy(w.project_id); await refresh(); setMessage('内容策略已生成。'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(''); } };
  return <>
    <PageHeader eyebrow="01 · 竞品研究" title="从证据提炼购买动机" description="录入竞品链接，形成结构化证据、用户痛点和内容机会。" />
    <section className="action-panel"><label htmlFor="competitor-urls">竞品链接</label><textarea id="competitor-urls" value={urls} onChange={event => setUrls(event.target.value)} placeholder="每行输入一个竞品链接" /><div className="action-row"><p>每行一个链接；当前演示环境返回合成研究数据。</p><button className="button primary" onClick={run} disabled={Boolean(busy)}>{busy === 'research' ? <LoaderCircle className="spin" size={16} /> : <Search size={16} />}开始研究</button></div></section>
    {message && <p className="feedback"><CheckCircle2 size={16} />{message}</p>}
    <div className="section-heading"><div><p className="eyebrow">研究结果</p><h2>竞品证据</h2></div><StatusBadge status={w.research?.status} /></div>
    {(w.competitors || []).length ? <div className="card-grid">{(w.competitors || []).map((competitor: Competitor, index: number) => <article className="evidence-card" key={competitor.competitor_id}><div className="card-topline"><span>竞品 {String(index + 1).padStart(2, '0')}</span><small>{competitor.competitor_id}</small></div><h3>{competitor.title}</h3><a href={competitor.url} target="_blank" rel="noreferrer">{competitor.url}</a><div className="metric-row"><span>评分 <strong>{competitor.rating ?? '-'}</strong></span><span>价格 <strong>{competitor.price ? `$${competitor.price}` : '-'}</strong></span></div><ul>{(competitor.bullet_points || []).map((value: string) => <li key={value}>{value}</li>)}</ul></article>)}</div> : <EmptyState icon={Search} title="等待竞品证据" description="输入竞品链接并开始研究后，结构化证据会显示在这里。" />}
    {(w.competitors || []).length > 0 && <section className="section-block insight-block"><div className="section-heading"><div><p className="eyebrow">洞察与策略</p><h2>把证据转为内容判断</h2></div>{!w.competitor_insight && <button className="button secondary" onClick={insight} disabled={Boolean(busy)}>{busy === 'insight' ? <LoaderCircle className="spin" size={16} /> : <Sparkles size={16} />}生成竞品洞察</button>}</div>{w.competitor_insight ? <><InsightView insight={w.competitor_insight} /><div className="section-footer"><button className="button primary" onClick={strategy} disabled={Boolean(busy)}>{busy === 'strategy' ? <LoaderCircle className="spin" size={16} /> : <Layers3 size={16} />}生成内容策略</button></div></> : <p className="muted">研究数据已准备好，下一步可以提炼购买动机和内容机会。</p>}</section>}
  </>;
}

function InsightView({ insight }: { insight: Insight }) {
  const groups: Array<[string, string[]]> = [['购买动机', insight.purchase_drivers], ['用户痛点', insight.customer_pain_points], ['竞品优势', insight.competitor_strengths], ['竞品弱点', insight.competitor_weaknesses], ['内容机会', insight.opportunity_gaps]];
  return <div className="insight-grid">{groups.map(([label, values]) => <div key={label}><span>{label}</span><p>{values.join(' · ') || '暂无'}</p></div>)}</div>;
}

function ListingView({ w, refresh }: WorkspaceProps) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const generate = async () => { setBusy(true); setMessage(''); try { if (!w.competitors?.length) await apiService.startResearch(w.project_id, ['https://www.amazon.com/dp/COMPETITOR_A', 'https://www.amazon.com/dp/COMPETITOR_B']); if (!w.competitor_insight) await apiService.generateInsight(w.project_id); if (!w.strategy) await apiService.generateStrategy(w.project_id); await apiService.generateListing(w.project_id); await refresh(); setMessage('商品文案已根据当前策略生成。'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(false); } };
  return <>
    <PageHeader eyebrow="02 · 商品文案" title="将策略转成可发布文案" description="标题、卖点和详情描述共享同一份产品事实与内容策略。" action={<button className="button primary" onClick={generate} disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Sparkles size={16} />}{w.listing ? '重新生成文案' : '生成商品文案'}</button>} />
    {message && <p className="feedback"><CheckCircle2 size={16} />{message}</p>}
    {w.listing ? <ListingCard listing={w.listing} /> : <EmptyState icon={FileText} title="尚未生成商品文案" description="系统会自动补齐所需的研究与策略步骤，然后生成第一版文案。" action={<button className="button secondary" onClick={generate}>生成第一版</button>} />}
  </>;
}

function ListingCard({ listing }: { listing: Listing }) {
  return <section className="document-panel"><div className="document-meta"><div><span>当前版本</span><strong>文案 v{listing.version}</strong></div><div><span>策略来源</span><strong>策略 v{listing.strategy_version}</strong></div><StatusBadge status={listing.status} /></div><label>商品标题<input value={listing.title} readOnly /></label><div className="bullet-editor"><span className="field-label">核心卖点</span>{listing.bullet_points.map((bullet: string, index: number) => <div className="bullet-row" key={`${index}-${bullet}`}><span>{index + 1}</span><input value={bullet} readOnly /></div>)}</div><label>商品描述<textarea value={listing.product_description} readOnly /></label><p className="form-note">当前页面展示已持久化版本；重新生成会创建新版本，不覆盖历史记录。</p></section>;
}

function Images({ w, refresh }: WorkspaceProps) {
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState('');
  const plan = async () => { try { setBusy('plan'); setMessage(''); await apiService.generateImagePlan(w.project_id); await refresh(); setMessage('图片方案已生成。'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(''); } };
  const generate = async () => { try { setBusy('generate'); setMessage(''); const job = await apiService.generateImages(w.project_id); if (job.job_id) await apiService.waitForJob(job.job_id); await refresh(); setMessage('图片生成任务已完成。'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(''); } };
  const imagePlan = w.image_plan?.image_plan as ImagePlanPayload | undefined;
  return <>
    <PageHeader eyebrow="03 · 图片规划" title="把购买理由转成图片任务" description="每张图对应一个明确的消费者问题，并保留策略与版本来源。" action={<div className="button-group"><button className="button secondary" onClick={plan} disabled={Boolean(busy)}>{busy === 'plan' ? <LoaderCircle className="spin" size={16} /> : <Layers3 size={16} />}{imagePlan ? '重新规划' : '生成图片方案'}</button>{imagePlan && <button className="button primary" onClick={generate} disabled={Boolean(busy)}>{busy === 'generate' ? <LoaderCircle className="spin" size={16} /> : <Play size={16} />}执行生成</button>}</div>} />
    {message && <p className="feedback"><CheckCircle2 size={16} />{message}</p>}
    {imagePlan ? <div className="image-grid">{imagePlan.images.map((image: ImageItem, index: number) => <article className="image-task" key={image.image_id}><div className="image-placeholder"><span>{String(index + 1).padStart(2, '0')}</span><ImageIcon size={28} /></div><div className="image-task-body"><div className="card-topline"><span>{roleLabels[image.role || ''] || image.role || `图片任务 ${index + 1}`}</span><StatusBadge status={w.image_generation?.status || image.generation_status} /></div><h3>{image.action || `图片任务 ${index + 1}`}</h3><p className="prompt-text">{image.prompt || '等待生成提示词'}</p><div className="qa-row"><span>质量检查：{statusLabel(image.qa_status)}</span><span>人工审核：{statusLabel(image.human_review_status)}</span></div><button className="button tertiary" disabled title="正式审批入口将在交付工作台中提供"><ShieldCheck size={15} />待接入审批</button></div></article>)}</div> : <EmptyState icon={ImageIcon} title="尚未生成图片方案" description="先生成图片方案，系统会按策略拆解每张图的角色和任务。" action={<button className="button secondary" onClick={plan}>生成图片方案</button>} />}
  </>;
}

function VideoView({ w, refresh }: WorkspaceProps) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const generate = async () => { setBusy(true); setMessage(''); try { if (!w.competitors?.length) await apiService.startResearch(w.project_id, ['https://www.amazon.com/dp/COMPETITOR_A', 'https://www.amazon.com/dp/COMPETITOR_B']); if (!w.competitor_insight) await apiService.generateInsight(w.project_id); if (!w.strategy) await apiService.generateStrategy(w.project_id); if (!w.listing) await apiService.generateListing(w.project_id); if (!w.image_plan) await apiService.generateImagePlan(w.project_id); const productName = w.product_truth?.product_name || '当前产品'; const sellingPoints = w.strategy?.core_differentiators || w.product_truth?.product_features || ['产品核心特点']; const input: VideoInput = { video_goal: `展示${productName}的核心卖点与使用方式`, target_audience: '目标电商消费者', duration: 15, hook: `快速看懂${productName}`, selling_points: sellingPoints, scene_plan: [{ scene: 1, action: '展示完整产品与包装内容' }, { scene: 2, action: '演示核心功能或结构' }, { scene: 3, action: '展示实际使用场景' }, { scene: 4, action: '回顾购买理由与价值' }] as Scene[], visual_direction: '清晰、克制的商业产品演示', narration: '先确认产品，再演示核心特点，最后回到购买理由。', on_screen_text: sellingPoints.slice(0, 2), final_prompt: `制作一条 15 秒的${productName}产品演示视频，遵循当前 Product Truth 与内容策略。` }; await apiService.generateVideo(w.project_id, input); await refresh(); setMessage('视频方案已生成；当前不会调用真实视频生成 API。'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(false); } };
  return <>
    <PageHeader eyebrow="04 · 视频方案" title="将内容策略组织成视频脚本" description="复用商品文案和图片策略，形成可交付的视频 Prompt。" action={<button className="button primary" onClick={generate} disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Clapperboard size={16} />}{w.video ? '重新生成方案' : '生成视频方案'}</button>} />
    {message && <p className="feedback"><CheckCircle2 size={16} />{message}</p>}
    {w.video ? <VideoCard video={w.video} /> : <EmptyState icon={Clapperboard} title="尚未生成视频方案" description="系统会复用当前项目上下文，生成镜头计划、旁白和最终 Prompt。" />}
  </>;
}

function VideoCard({ video }: { video: Video }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => { await navigator.clipboard?.writeText(video.final_prompt); setCopied(true); window.setTimeout(() => setCopied(false), 1600); };
  return <section className="video-layout"><div className="video-summary"><div className="section-heading"><div><p className="eyebrow">视频策略</p><h2>{video.hook}</h2></div><span className="duration">{video.duration}秒</span></div><dl><div><dt>目标受众</dt><dd>{video.target_audience}</dd></div><div><dt>核心卖点</dt><dd>{video.selling_points.join(' · ')}</dd></div><div><dt>视觉方向</dt><dd>{video.visual_direction}</dd></div><div><dt>旁白</dt><dd>{video.narration}</dd></div></dl></div><div className="scene-list"><p className="eyebrow">镜头结构</p>{video.scene_plan.map((scene: Scene, index: number) => <div key={index}><span>{String(scene.scene || index + 1).padStart(2, '0')}</span><p>{scene.action || '待补充镜头动作'}</p></div>)}</div><div className="prompt-panel"><div><p className="eyebrow">最终提示词</p><button className="icon-text-button" onClick={copy}>{copied ? <Check size={15} /> : <Copy size={15} />}{copied ? '已复制' : '复制'}</button></div><pre>{video.final_prompt}</pre></div></section>;
}

const isWorkspaceRoute = location.pathname.startsWith('/projects/') || location.pathname.startsWith('/workspace');
createRoot(document.getElementById('root')!).render(<React.StrictMode>{isWorkspaceRoute ? <App /> : <PortfolioApp />}</React.StrictMode>);
