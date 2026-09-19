import { useEffect, useMemo, useState } from 'react';
import {
  ArrowDown, ArrowRight, Check, ChevronRight, CircleAlert, Code2,
  ExternalLink, FileCheck2, GitBranch, Image as ImageIcon, Layers3, Maximize2,
  Menu, Pause, Play, ScanSearch, ShieldCheck, Sparkles, X, ZoomIn,
} from 'lucide-react';
import { buildPortfolioViewModel, discoverRecordedRuns } from './adapters/portfolio';
import type { ImageEvidence, WorkflowNode } from './data/portfolio';
import './portfolio.css';

const portfolio = buildPortfolioViewModel();

function scrollToId(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function AssetImage({ src, alt, className = '', eager = false }: { src: string; alt: string; className?: string; eager?: boolean }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  return (
    <span className={`asset-frame ${className} ${loaded ? 'is-loaded' : ''}`}>
      {!loaded && !failed && <span className="asset-loading">Loading evidence…</span>}
      {failed ? <span className="asset-error"><ImageIcon size={20} /> Evidence asset unavailable</span> : (
        <img src={src} alt={alt} loading={eager ? 'eager' : 'lazy'} onLoad={() => setLoaded(true)} onError={() => setFailed(true)} />
      )}
    </span>
  );
}

function SectionHeading({ index, eyebrow, title, copy }: { index: string; eyebrow: string; title: string; copy?: string }) {
  return <div className="section-heading"><span className="section-index">{index}</span><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2>{copy && <p className="section-copy">{copy}</p>}</div></div>;
}

function WorkflowExplorer({ nodes, compact = false }: { nodes: WorkflowNode[]; compact?: boolean }) {
  const [selected, setSelected] = useState(nodes[0].id);
  const node = nodes.find(item => item.id === selected) || nodes[0];
  return (
    <div className={`workflow-explorer ${compact ? 'compact' : ''}`}>
      <div className="workflow-rail" role="tablist" aria-label="Content workflow">
        {nodes.map((item, index) => <div className="workflow-step" key={item.id}>
          <button type="button" role="tab" aria-selected={item.id === selected} className={item.id === selected ? 'active' : ''} onClick={() => setSelected(item.id)}>
            <span>{String(index + 1).padStart(2, '0')}</span>{item.label}
          </button>
          {index < nodes.length - 1 && <ChevronRight aria-hidden="true" size={15} />}
        </div>)}
      </div>
      <div className="workflow-detail" role="tabpanel" aria-live="polite">
        <div className="workflow-detail-lead"><p className="eyebrow">{node.eyebrow}</p><h3>{node.label}</h3><p>{node.decision}</p></div>
        <DetailColumn label="Input" items={node.input} />
        <DetailColumn label="Output" items={node.output} />
        <DetailColumn label="Validation" items={node.validation} />
      </div>
    </div>
  );
}

function DetailColumn({ label, items }: { label: string; items: string[] }) {
  return <div className="detail-column"><span>{label}</span>{items.map(item => <p key={item}>{item}</p>)}</div>;
}

function BeforeAfter({ before, after, label }: { before: string; after: string; label: string }) {
  const [position, setPosition] = useState(46);
  return (
    <div className="compare-wrap">
      <div className="compare-stage" style={{ '--compare': `${position}%` } as React.CSSProperties}>
        <AssetImage src={before} alt={`Source evidence for ${label}`} />
        <div className="compare-after"><AssetImage src={after} alt={`Generated version for ${label}`} /></div>
        <div className="compare-line" aria-hidden="true"><span><ArrowRight size={14} /></span></div>
        <span className="compare-label before">Source</span><span className="compare-label after">Generated</span>
      </div>
      <label className="sr-only" htmlFor={`compare-${label}`}>Compare source and generated image</label>
      <input id={`compare-${label}`} className="compare-range" type="range" min="0" max="100" value={position} onChange={event => setPosition(Number(event.target.value))} />
    </div>
  );
}

function ImageModal({ image, onClose }: { image: ImageEvidence; onClose: () => void }) {
  const [version, setVersion] = useState(image.versions.length - 1);
  const [zoom, setZoom] = useState(false);
  const [tab, setTab] = useState<'decision' | 'prompt' | 'qa' | 'versions'>('decision');
  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === 'Escape' && onClose();
    document.addEventListener('keydown', close);
    document.body.classList.add('modal-open');
    return () => { document.removeEventListener('keydown', close); document.body.classList.remove('modal-open'); };
  }, [onClose]);
  return <div className="image-modal" role="dialog" aria-modal="true" aria-label={`${image.label} evidence viewer`}>
    <button className="icon-button modal-close" type="button" onClick={onClose} aria-label="Close viewer"><X /></button>
    <div className="modal-media">
      <button type="button" className={`zoom-stage ${zoom ? 'zoomed' : ''}`} onClick={() => setZoom(value => !value)} aria-label={zoom ? 'Zoom out' : 'Zoom in'}>
        <AssetImage src={image.versions[version].src} alt={`${image.label} ${image.versions[version].label}`} eager />
        <span className="zoom-hint"><ZoomIn size={16} /> {zoom ? 'Fit' : 'Inspect'}</span>
      </button>
      <div className="version-switcher" aria-label="Image versions">
        {image.versions.map((item, index) => <button type="button" className={index === version ? 'active' : ''} onClick={() => setVersion(index)} key={item.label}>{item.label}</button>)}
      </div>
    </div>
    <aside className="modal-detail">
      <p className="eyebrow">{image.id} · {image.priority}</p><h2>{image.label}</h2>
      <div className="status-line"><span className="status review"><CircleAlert size={14} /> {image.qaStatus}</span><span>{image.role}</span></div>
      <div className="viewer-tabs" role="tablist" aria-label="Evidence details">
        {(['decision', 'prompt', 'qa', 'versions'] as const).map(item => <button type="button" role="tab" aria-selected={tab === item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)} key={item}>{item}</button>)}
      </div>
      <div className="viewer-panel">
        {tab === 'decision' && <><MetaBlock label="Purpose" text={image.decisionQuestion} /><MetaBlock label="Customer need" text={image.customerNeed} /><MetaBlock label="Decision" text={image.strategyReason} /><TagList label="Required evidence" items={image.requiredEvidence} /></>}
        {tab === 'prompt' && <><MetaBlock label="Prompt objective" text={image.prompt} /><TagList label="Restrictions" items={image.constraints} /></>}
        {tab === 'qa' && <><MetaBlock label="Verdict" text="AI QA did not approve this output. It remains queued for human review." /><TagList label="Observed issues" items={image.qaIssues} /></>}
        {tab === 'versions' && <div className="version-timeline">{image.versions.map((item, index) => <button type="button" onClick={() => setVersion(index)} className={index === version ? 'active' : ''} key={item.label}><span>V{index + 1}</span><div><b>{item.change}</b><small>{item.status}</small></div></button>)}</div>}
      </div>
      <p className="source-note">Evidence: repository image plan, generation metadata, and QA records.</p>
    </aside>
  </div>;
}

function MetaBlock({ label, text }: { label: string; text: string }) { return <div className="meta-block"><span>{label}</span><p>{text}</p></div>; }
function TagList({ label, items }: { label: string; items: string[] }) { return <div className="meta-block"><span>{label}</span><ul>{items.map(item => <li key={item}><Check size={14} />{item}</li>)}</ul></div>; }

function ImageCase() {
  const [selected, setSelected] = useState(portfolio.images[0].id);
  const [modal, setModal] = useState<ImageEvidence | null>(null);
  const current = portfolio.images.find(item => item.id === selected) || portfolio.images[0];
  return <section className="case-block image-case" id="image-case">
    <div className="case-kicker"><span>02</span><p>AI Image Production</p><span className="status review">Recorded run · NEEDS_REVIEW</span></div>
    <div className="case-title"><h3>Before → Decision → Generation → QA</h3><p>Six business questions become six constrained image tasks. Outputs remain visible even when QA does not approve them.</p></div>
    <div className="image-thumbs" role="tablist" aria-label="Image case selection">
      {portfolio.images.map(item => <button type="button" role="tab" aria-selected={item.id === selected} className={item.id === selected ? 'active' : ''} onClick={() => setSelected(item.id)} key={item.id}>
        <AssetImage src={item.versions[item.versions.length - 1].src} alt="" /><span>{item.id.replace('_', ' ')}</span><b>{item.label}</b>
      </button>)}
    </div>
    <div className="image-inspector">
      <BeforeAfter before={current.before} after={current.versions[current.versions.length - 1].src} label={current.id} />
      <div className="inspector-copy">
        <div><p className="eyebrow">Objective</p><h4>{current.decisionQuestion}</h4><p>{current.customerNeed}</p></div>
        <div className="decision-strip"><span>Decision</span><p>{current.strategyReason}</p></div>
        <div className="qa-summary"><span className="status review"><CircleAlert size={14} /> {current.qaStatus}</span><p>{current.qaIssues.join(' · ')}</p></div>
        <button type="button" className="text-button" onClick={() => setModal(current)}>Inspect plan, prompt & versions <Maximize2 size={16} /></button>
      </div>
    </div>
    {modal && <ImageModal image={modal} onClose={() => setModal(null)} />}
  </section>;
}

function PortfolioApp() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [recordedRuns, setRecordedRuns] = useState(0);
  const [videoStep, setVideoStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  useEffect(() => { discoverRecordedRuns().then(runs => setRecordedRuns(runs.length)); }, []);
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setVideoStep(step => (step + 1) % portfolio.video.sequence.length), 1500);
    return () => window.clearInterval(timer);
  }, [playing]);
  const calibrationFlow = useMemo(() => ['AI output', 'AI QA', 'Human review', 'Feedback', 'Plan revision', 'Regenerate', 'Approval'], []);

  return <div className="portfolio">
    <nav className="top-nav" aria-label="Portfolio navigation">
      <a className="brand" href="#top"><span>QX</span><b>AIGC SYSTEMS</b></a>
      <button className="icon-button menu-button" type="button" onClick={() => setMenuOpen(value => !value)} aria-label="Toggle navigation"><Menu /></button>
      <div className={`nav-links ${menuOpen ? 'open' : ''}`}>
        <button onClick={() => scrollToId('system')}>System</button><button onClick={() => scrollToId('cases')}>Cases</button><button onClick={() => scrollToId('architecture')}>Engineering</button><a href="/workspace">Open Workspace <ExternalLink size={14} /></a>
      </div>
    </nav>

    <main id="top">
      <section className="hero" aria-labelledby="hero-title">
        <AssetImage className="hero-media" src={portfolio.product.canonicalImage} alt="Gold three-piece hinged ring set, canonical product evidence" eager />
        <div className="hero-scrim" />
        <div className="hero-content">
          <p className="eyebrow">AI-Native · Cross-Border E-commerce</p>
          <h1 id="hero-title"><span>AI-NATIVE</span><span>CROSS-BORDER</span><span>CONTENT PRODUCTION</span></h1>
          <p className="hero-subtitle">{portfolio.subtitle}</p>
          <p className="hero-cn">面向跨境电商的 AI 内容生产与工程化工作流。</p>
          <div className="hero-actions"><button className="primary-button" onClick={() => scrollToId('system')}>Explore System <ArrowDown size={17} /></button><button className="secondary-button" onClick={() => scrollToId('cases')}>View Cases <ArrowRight size={17} /></button></div>
        </div>
        <div className="hero-proof"><span>Verified demo SKU</span><b>{portfolio.product.id}</b><span>Source → decision → delivery</span></div>
      </section>

      <section className="section system-section" id="system">
        <SectionHeading index="01" eyebrow="System overview" title="One SKU → Complete Content System" copy="Click any node to inspect its inputs, decision responsibility, structured output, and validation boundary." />
        <WorkflowExplorer nodes={portfolio.workflow} />
        <div className="principle-band"><div><Sparkles /><span>AI decides</span><p>semantic understanding · planning · classification · content suggestions</p></div><ArrowRight /><div><ShieldCheck /><span>System decides</span><p>state · validation · approval · version · rendering · delivery</p></div><b>AI + Deterministic Engineering</b></div>
      </section>

      <section className="section cases-section" id="cases">
        <SectionHeading index="02" eyebrow="Case studies" title="Evidence, not a gallery" copy="Each case exposes the business question, decision trail, model output, validation state, and known gap." />
        <section className="case-block listing-case">
          <div className="case-kicker"><span>01</span><p>Listing Optimization</p><span className="status prototype">Prototype · deterministic demo</span></div>
          <div className="case-title"><h3>From Product Data → Conversion-Oriented Content</h3><p>The generated listing is traceable to approved facts and shopper questions. It is not presented as measured conversion lift.</p></div>
          <div className="listing-layout">
            <div className="truth-sheet"><p className="eyebrow">Product Truth · v1</p><h4>{portfolio.product.name}</h4><dl><dt>Material</dt><dd>{portfolio.product.material}</dd><dt>Finish</dt><dd>{portfolio.product.finish}</dd><dt>Size</dt><dd>{portfolio.product.sizes.join(' · ')}</dd><dt>Package</dt><dd>{portfolio.product.contents.join(' · ')}</dd></dl><div className="claim-list">{portfolio.product.claims.map(item => <span key={item.source}><FileCheck2 size={14} /> {item.claim}<small>{item.source}</small></span>)}</div></div>
            <div className="trace-list">{portfolio.listing.trace.map((item, index) => <div className="trace-row" key={item.decision}><span>0{index + 1}</span><div><small>Evidence</small><p>{item.evidence}</p></div><ArrowRight /><div><small>Concern</small><p>{item.concern}</p></div><ArrowRight /><div><small>Decision</small><p>{item.decision}</p></div><ArrowRight /><div><small>Listing output</small><b>{item.output}</b></div></div>)}</div>
            <div className="listing-output"><p className="eyebrow">Generated Listing · pending review</p><h4>{portfolio.listing.title}</h4><ol>{portfolio.listing.bullets.map(item => <li key={item}>{item}</li>)}</ol><p className="source-note">Model field in persisted demo: deterministic-config</p></div>
          </div>
        </section>
        <ImageCase />
        <section className="case-block video-case" id="video-case">
          <div className="case-kicker"><span>03</span><p>AI-Assisted Video Production</p><span className="status blocked">Experimental · blocked run</span></div>
          <div className="case-title"><h3>Plan, request, review — no fabricated final</h3><p>The repository contains a complete prompt and provider trace, but the provider rejected the model request. No playable asset is claimed.</p></div>
          <div className="video-layout">
            <div className="video-stage">
              <AssetImage src={portfolio.video.source} alt="Canonical product source for video prompt" />
              <div className="video-overlay"><span>VIDEO PLAN · 15S</span><h4>{portfolio.video.sequence[videoStep]}</h4><p>Step {videoStep + 1} / {portfolio.video.sequence.length}</p></div>
              <button className="video-control" type="button" onClick={() => setPlaying(value => !value)} aria-label={playing ? 'Pause sequence preview' : 'Play sequence preview'}>{playing ? <Pause /> : <Play />}</button>
            </div>
            <div className="video-plan"><p className="eyebrow">Structured sequence</p>{portfolio.video.sequence.map((item, index) => <button type="button" className={index === videoStep ? 'active' : ''} onClick={() => { setVideoStep(index); setPlaying(false); }} key={item}><span>0{index + 1}</span><p>{item}</p></button>)}<div className="failure-note"><CircleAlert /><div><b>Recorded provider result</b><p>{portfolio.video.failure}</p></div></div><dl><dt>Adapter</dt><dd>Seedance</dd><dt>Model request</dt><dd>{portfolio.video.model}</dd><dt>Final video</dt><dd>Not available</dd></dl></div>
          </div>
        </section>
      </section>

      <section className="section calibration-section" id="calibration">
        <SectionHeading index="03" eyebrow="Human calibration" title="AI Generates. Humans Calibrate." copy="The system keeps uncertainty visible and turns review feedback into a versioned revision path." />
        <div className="calibration-flow">{calibrationFlow.map((item, index) => <div key={item}><span>{String(index + 1).padStart(2, '0')}</span><b>{item}</b>{index < calibrationFlow.length - 1 && <ArrowRight size={16} />}</div>)}</div>
        <div className="calibration-example">
          <div><p className="eyebrow">Issue</p><h3>Product evidence is incomplete</h3><p>Baseline QA found missing visual evidence, unverified scale, incomplete decision coverage, and unsupported claims.</p></div>
          <div><p className="eyebrow">Human feedback</p><h3>Keep product facts bounded</h3><p>Preserve geometry and quantity. Do not infer worn scale or fabricate material certificates.</p></div>
          <div><p className="eyebrow">Revision rule</p><h3>Change the plan, then regenerate</h3><p>Revision tasks keep the original image, evaluation, provider, and generation version traceable.</p></div>
          <div className="calibration-result"><span className="status review">Current state · draft</span><p>No inspected calibration session establishes an approved final set.</p></div>
        </div>
      </section>

      <section className="section architecture-section" id="architecture">
        <SectionHeading index="04" eyebrow="Engineering architecture" title="Engineering the AI Workflow" copy="Technology is shown by the business control it provides, not as a logo wall." />
        <div className="architecture-flow">{portfolio.architecture.map((item, index) => <div className="architecture-row" key={item.layer}><span>{String(index + 1).padStart(2, '0')}</span><h3>{item.layer}</h3><p>{item.technology}</p><ArrowRight size={16} /><b>{item.businessFunction}</b></div>)}</div>
        <div className="engineering-proof"><div><GitBranch /><span>Version</span><p>Append-only artifact history with input references and checksums.</p></div><div><ShieldCheck /><span>Approval</span><p>Approval is bound to the exact artifact version and never inherited.</p></div><div><Layers3 /><span>Export</span><p>Unapproved artifacts block delivery; export records a manifest and hashes.</p></div><div><Code2 /><span>Contract</span><p>OpenAPI defines the backend contract and generated TypeScript types.</p></div></div>
      </section>

      <section className="section evidence-section" id="evidence">
        <SectionHeading index="05" eyebrow="Evidence / results" title="What the records actually prove" copy="Counts below are repository observations, not business impact claims." />
        <div className="evidence-grid">
          <div className="evidence-number"><strong>6 / 6</strong><span>images generated</span><p>Wan baseline v1 · zero generation failures</p></div>
          <div className="evidence-number warning"><strong>6 / 6</strong><span>need human review</span><p>Zero PASS and zero FAIL in the recorded QA summary</p></div>
          <div className="evidence-number"><strong>{recordedRuns || '—'}</strong><span>discoverable image runs</span><p>{recordedRuns ? 'Read live from /api/artifacts/runs' : 'Backend not connected; metric hidden'}</p></div>
          <div className="evidence-number blocked-metric"><strong>0</strong><span>final videos</span><p>Recorded provider request was blocked by model access</p></div>
        </div>
        <div className="qa-breakdown"><div><p className="eyebrow">QA failure distribution · overlapping categories</p><h3>Uncertainty becomes structured work</h3></div>{portfolio.qa.failureCounts.map(item => <div className="qa-bar" key={item.label}><span>{item.label}</span><div><i style={{ width: `${(item.count / portfolio.qa.generated) * 100}%` }} /></div><b>{item.count}</b></div>)}</div>
      </section>

      <section className="section capabilities-section" id="capabilities">
        <SectionHeading index="06" eyebrow="Capability map" title="Business → AI → Engineering → Production" />
        <div className="capability-grid">{portfolio.capabilities.map((group, index) => <div key={group.group}><span>0{index + 1}</span><h3>{group.group}</h3><ul>{group.items.map(item => <li key={item}>{item}</li>)}</ul></div>)}</div>
        <div className="evidence-footer"><ScanSearch /><p>{portfolio.evidenceNote}</p><a href="/workspace">Inspect the working system <ArrowRight size={15} /></a></div>
      </section>
    </main>
    <footer><div><span>AI-NATIVE CONTENT SYSTEM</span><p>Cross-border AIGC · evidence-led planning · deterministic delivery</p></div><div><span>Scope</span><p>Portfolio adapter over an existing production-workflow prototype</p></div><a href="#top">Back to top <ArrowDown className="rotate" size={15} /></a></footer>
  </div>;
}

export default PortfolioApp;
