import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { apiService, type Workspace } from './api/service';
import type { components } from './generated/api';

type Competitor = components['schemas']['CompetitorSnapshot'];
type Insight = components['schemas']['CompetitorInsight'];
type Strategy = components['schemas']['PresentationStrategy'];
type Listing = components['schemas']['ListingPlan'];
type Video = components['schemas']['VideoPlan'];
type VideoInput = components['schemas']['VideoPlanInput'];
type Scene = { scene?: number; action?: string; [key: string]: unknown };
type ImageItem = { image_id: string; role?: string; priority?: string; prompt?: string; generation_status?: string; qa_status?: string; human_review_status?: string };
type ImagePlanPayload = { images: ImageItem[]; plan_version?: string; product_id?: string; strategy_summary?: string };
type WorkspaceProps = { w: Workspace; refresh: () => Promise<void> };

const nav = [['overview', '00 Overview'], ['research', '01 Research'], ['listing', '02 Listing'], ['images', '03 Images'], ['video', '04 Video']];
const messageOf = (error: unknown) => error instanceof Error ? error.message : 'Request failed.';

function App() {
  const [workspace, setWorkspace] = useState<Workspace | undefined>();
  const [stage, setStage] = useState(location.pathname.split('/').pop() || 'overview');
  const refresh = async () => { if (workspace?.project_id) setWorkspace(await apiService.getProject(workspace.project_id)); };
  useEffect(() => {
    const projectId = location.pathname.match(/^\/projects\/([^/]+)/)?.[1] || 'demo-project';
    apiService.getProject(projectId).then(setWorkspace).catch(() => setWorkspace(undefined));
  }, []);
  if (!workspace) return <main>Loading workspace...</main>;
  const go = (nextStage: string) => { history.pushState({}, '', `/projects/${workspace.project_id}/${nextStage}`); setStage(nextStage); };
  return <div className="app"><header><b>Presentation</b><span>{workspace.project_name}</span><span>SKU {workspace.sku}</span><span>Stage {workspace.current_stage}</span><span>Status {workspace.overall_status}</span></header><div className="shell"><aside><h3>Project Workspace</h3>{nav.map(([id, label]) => <button className={stage === id ? 'active' : ''} onClick={() => go(id)} key={id}>{label}</button>)}<Context w={workspace} /></aside><section className="content">{stage === 'overview' ? <Overview w={workspace} /> : stage === 'research' ? <Research w={workspace} refresh={refresh} /> : stage === 'listing' ? <ListingView w={workspace} refresh={refresh} /> : stage === 'images' ? <Images w={workspace} refresh={refresh} /> : <VideoView w={workspace} refresh={refresh} />}</section></div></div>;
}

function Overview({ w }: { w: Workspace }) { return <><h1>Presentation Overview</h1><article><h2>{w.product_truth?.product_name}</h2><p>SKU {w.sku}</p><h3>Current Strategy</h3><ol>{(w.strategy?.priority_order || ['Generate Insight to establish priorities']).map((value: string) => <li key={value}>{value}</li>)}</ol><p className="flow">Competitor Evidence → Customer Needs → Strategy → Listing → Images → Video</p><p>Outputs: {w.listing ? 'Listing ready' : 'Listing pending'} · {w.image_plan ? '6 image plans' : 'ImagePlan pending'} · {w.video ? 'Prompt ready' : 'Video pending'}</p></article></>; }

function Context({ w }: { w: Workspace }) { return <details open><summary>Product Context</summary><h4>Product Truth</h4><p><b>{w.product_truth?.product_name}</b><br />SKU {w.sku}<br />Material {String(w.product_truth?.material?.base || 'n/a')}</p><h4>Competitor Insight</h4><p>{(w.competitor_insight?.purchase_drivers || ['Not generated']).join(' · ')}</p><h4>Presentation Strategy</h4><p>{(w.strategy?.core_differentiators || ['Not generated']).join(' · ')}</p></details>; }

function Research({ w, refresh }: WorkspaceProps) {
  const [urls, setUrls] = useState('https://www.amazon.com/dp/COMPETITOR_A\nhttps://www.amazon.com/dp/COMPETITOR_B');
  const [message, setMessage] = useState('');
  const run = async () => { try { setMessage(''); const job = await apiService.startResearch(w.project_id, urls.split('\n').filter(Boolean)); if (job.job_id) await apiService.waitForJob(job.job_id); await refresh(); } catch (error) { setMessage(messageOf(error)); } };
  const insight = async () => { try { setMessage(''); await apiService.generateInsight(w.project_id); await refresh(); } catch (error) { setMessage(messageOf(error)); } };
  const strategy = async () => { try { setMessage(''); await apiService.generateStrategy(w.project_id); await refresh(); } catch (error) { setMessage(messageOf(error)); } };
  return <><h1>Competitor Research</h1><p>Evidence → Customer Needs → Purchase Drivers</p><textarea value={urls} onChange={event => setUrls(event.target.value)} /><button onClick={run}>Start Research</button>{message && <p>{message}</p>}<p>Research status: <b>{w.research?.status || 'queued'}</b></p><div className="grid">{(w.competitors || []).map((competitor: Competitor) => <article key={competitor.competitor_id}><h3>{competitor.title}</h3><p>{competitor.url}</p><p>Rating {competitor.rating} · ${competitor.price}</p><ul>{(competitor.bullet_points || []).map((value: string) => <li key={value}>{value}</li>)}</ul><small>Evidence source: {competitor.competitor_id}</small></article>)}</div>{(w.competitors || []).length > 0 && <><button onClick={insight}>Generate Insight</button>{w.competitor_insight && <article><InsightView insight={w.competitor_insight} /><button onClick={strategy}>Generate Presentation Strategy</button></article>}</>}</>;
}

function InsightView({ insight }: { insight: Insight }) { return <><h2>Competitor Insight</h2><p>Purchase Drivers: {insight.purchase_drivers.join(' · ')}</p><p>Pain Points: {insight.customer_pain_points.join(' · ')}</p><p>Strengths: {insight.competitor_strengths.join(' · ')}</p><p>Weaknesses: {insight.competitor_weaknesses.join(' · ')}</p><p>Opportunity Gaps: {insight.opportunity_gaps.join(' · ')}</p><p>Evidence: {insight.evidence.map(evidence => <button key={evidence.snapshot_id} onClick={() => alert(`${evidence.snapshot_id}: ${String(evidence.excerpt || '')}`)}>View {evidence.snapshot_id}</button>)}</p></>; }

function ListingView({ w, refresh }: WorkspaceProps) {
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  const generate = async () => { setBusy(true); setMessage(''); try { if (!w.competitors?.length) await apiService.startResearch(w.project_id, ['https://www.amazon.com/dp/COMPETITOR_A', 'https://www.amazon.com/dp/COMPETITOR_B']); if (!w.competitor_insight) await apiService.generateInsight(w.project_id); if (!w.strategy) await apiService.generateStrategy(w.project_id); await apiService.generateListing(w.project_id); await refresh(); setMessage('Listing generated from the shared Presentation Strategy.'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(false); } };
  return <><h1>Listing</h1><p>Presentation Strategy → Listing Expression</p><button onClick={generate} disabled={busy}>{busy ? 'Generating…' : 'Generate Listing'}</button>{message && <p>{message}</p>}{w.listing && <ListingCard listing={w.listing} />}</>;
}

function ListingCard({ listing }: { listing: Listing }) { return <article><p>Strategy mapping: Material Safety → Bullet 1 · Comfort → Bullet 2 · Fit → Bullet 3</p><label>Title<input defaultValue={listing.title} /></label>{listing.bullet_points.map((bullet: string, index: number) => <label key={index}>Bullet {index + 1}<input defaultValue={bullet} /></label>)}<label>Description<textarea defaultValue={listing.product_description} /></label><p>Version {listing.version} · Strategy v{listing.strategy_version} · Generated content preserved</p></article>; }

function Images({ w, refresh }: WorkspaceProps) {
  const [message, setMessage] = useState('');
  const plan = async () => { try { setMessage(''); await apiService.generateImagePlan(w.project_id); await refresh(); } catch (error) { setMessage(messageOf(error)); } };
  const generate = async () => { try { setMessage(''); const job = await apiService.generateImages(w.project_id); if (job.job_id) await apiService.waitForJob(job.job_id); await refresh(); } catch (error) { setMessage(messageOf(error)); } };
  const imagePlan = w.image_plan?.image_plan as ImagePlanPayload | undefined;
  const purposes = ['Primary Product Representation · confirm what it is', 'Material / Safety · resolve material safety', 'Usage / Comfort · show wearing comfort', 'Size / Fit · resolve selection uncertainty', 'Feature / Differentiator · prove hinged closure', 'Package / Value · clarify 3PCS value'];
  return <><h1>Image Studio</h1><p>Presentation Strategy → Image Expression</p><button onClick={plan}>Generate ImagePlan</button>{message && <p>{message}</p>}{imagePlan && <><button onClick={generate}>Generate Images</button><div className="grid">{imagePlan.images.map((image: ImageItem, index: number) => <article key={image.image_id}><h3>{image.image_id} · {purposes[index]}</h3><p>Purchase Driver: {(w.strategy?.priority_order || ['Material Safety', 'Comfort', 'Fit'])[index % 3]} · Strategy #{index % 3 + 1}</p><p>Prompt: {image.prompt || 'Strategy-backed prompt'}</p><p>Generation {w.image_generation?.status || image.generation_status || 'queued'} · QA {image.qa_status || 'NEEDS_REVIEW'} · Human {image.human_review_status || 'pending_review'}</p><button>Review</button><button>Approve</button><button>Reject</button></article>)}</div></>}</>;
}

function VideoView({ w, refresh }: WorkspaceProps) {
  const [busy, setBusy] = useState(false); const [message, setMessage] = useState('');
  const generate = async () => { setBusy(true); setMessage(''); try { if (!w.competitors?.length) await apiService.startResearch(w.project_id, ['https://www.amazon.com/dp/COMPETITOR_A', 'https://www.amazon.com/dp/COMPETITOR_B']); if (!w.competitor_insight) await apiService.generateInsight(w.project_id); if (!w.strategy) await apiService.generateStrategy(w.project_id); if (!w.listing) await apiService.generateListing(w.project_id); if (!w.image_plan) await apiService.generateImagePlan(w.project_id); const input: VideoInput = { video_goal: 'Demonstrate fit and material confidence', target_audience: 'Amazon shoppers', duration: 15, hook: 'Resolve material safety and fit uncertainty', selling_points: w.strategy?.core_differentiators || ['ASTM F136 titanium', 'secure hinged closure'], scene_plan: [{ scene: 1, action: 'show exact 3PCS set' }, { scene: 2, action: 'demonstrate hinged closure' }, { scene: 3, action: 'show comfortable worn result' }, { scene: 4, action: 'reinforce material and value' }] as Scene[], visual_direction: 'Clean commercial product demo', narration: 'Show the set, prove the hinge, show the fit, close on the buying reason.', on_screen_text: ['ASTM F136 titanium', '3PCS multi-style set'], final_prompt: 'Create a 15-second product demonstration using the shared Product Truth and Presentation Strategy.' }; await apiService.generateVideo(w.project_id, input); await refresh(); setMessage('Video Plan ready — no video API is being called.'); } catch (error) { setMessage(messageOf(error)); } finally { setBusy(false); } };
  return <><h1>Video Studio</h1><p>Strategy + Listing + Image context → Video Prompt</p><button onClick={generate} disabled={busy}>{busy ? 'Preparing…' : 'Generate Video Plan'}</button>{message && <p>{message}</p>}{w.video && <VideoCard video={w.video} />}</>;
}

function VideoCard({ video }: { video: Video }) { return <article><h3>Video Strategy</h3><p>Hook: {video.hook}</p><p>Selling points: {video.selling_points.join(', ')}</p><p>Scene plan: {video.scene_plan.map((scene: Scene) => scene.action || '').join(' → ')}</p><p>Visual direction: {video.visual_direction}</p><p>Narration: {video.narration}</p><pre>{video.final_prompt}</pre><button onClick={() => navigator.clipboard?.writeText(video.final_prompt)}>Copy Prompt</button><button onClick={() => alert(video.final_prompt)}>Export Prompt</button></article>; }

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
