export type EvidenceStatus = 'Implemented' | 'Prototype' | 'Experimental' | 'Blocked';

export type WorkflowNode = {
  id: string;
  label: string;
  eyebrow: string;
  input: string[];
  decision: string;
  output: string[];
  validation: string[];
};

export type ImageEvidence = {
  id: string;
  label: string;
  role: string;
  priority: 'P0' | 'P1';
  decisionQuestion: string;
  customerNeed: string;
  strategyReason: string;
  before: string;
  versions: Array<{ label: string; src: string; status: string; change: string }>;
  prompt: string;
  requiredEvidence: string[];
  constraints: string[];
  qaStatus: 'NEEDS_REVIEW';
  qaIssues: string[];
};

export type PortfolioEvidence = {
  product: {
    id: string;
    name: string;
    category: string;
    material: string;
    finish: string;
    sizes: string[];
    contents: string[];
    claims: Array<{ claim: string; source: string }>;
    canonicalImage: string;
  };
  workflow: WorkflowNode[];
  images: ImageEvidence[];
  listing: {
    status: EvidenceStatus;
    title: string;
    bullets: string[];
    trace: Array<{ evidence: string; concern: string; decision: string; output: string }>;
  };
  video: {
    status: EvidenceStatus;
    model: string;
    goal: string;
    sequence: string[];
    source: string;
    failure: string;
  };
  qa: {
    generated: number;
    needsReview: number;
    passed: number;
    failed: number;
    failureCounts: Array<{ label: string; count: number }>;
  };
  architecture: Array<{ layer: string; technology: string; businessFunction: string }>;
  capabilities: Array<{ group: string; items: string[] }>;
  sources: string[];
};

const asset = (path: string) => `/api/assets/${path}`;

export const rawPortfolioEvidence: PortfolioEvidence = {
  product: {
    id: 'G23STUDIO_ASTMF136_HINGED_SEPTUM_RING_3PCS',
    name: 'ASTM F136 Titanium Hinged Ring · 3PCS',
    category: 'Cross-border piercing jewelry demo SKU',
    material: 'ASTM F136 implant-grade titanium',
    finish: 'Titanium base + 18K Gold PVD finish',
    sizes: ['18G', '20G', '8mm inner diameter'],
    contents: ['Classic hoop', 'Double-layer hoop', 'CZ accent hoop'],
    claims: [
      { claim: 'ASTM F136 titanium', source: 'claim_f136_titanium' },
      { claim: '18K Gold PVD finish', source: 'claim_gold_pvd' },
      { claim: '3PCS multi-style set', source: 'claim_three_styles' },
      { claim: 'Hinged press clasp', source: 'claim_click_top' },
    ],
    canonicalImage: asset('p1/p1.jpg'),
  },
  workflow: [
    { id: 'truth', label: 'Product Truth', eyebrow: '01 · Source', input: ['Catalog record', 'Canonical asset', 'Approved claims'], decision: 'Which facts are safe to use?', output: ['Versioned SKU facts', 'Claim IDs', 'Asset policy'], validation: ['Schema', 'Source reference', 'Forbidden claims'] },
    { id: 'evidence', label: 'Competitor Evidence', eyebrow: '02 · Research', input: ['Product snapshots', 'Review buckets', 'Visual patterns'], decision: 'What questions are competitors answering?', output: ['Purchase drivers', 'Pain points', 'Opportunity gaps'], validation: ['Evidence excerpt', 'Source snapshot', 'No identity borrowing'] },
    { id: 'needs', label: 'Customer Needs', eyebrow: '03 · Interpret', input: ['Evidence patterns', 'Selection friction'], decision: 'What must the shopper understand first?', output: ['Identity', 'Fit', 'Material trust'], validation: ['Evidence linkage', 'Confidence', 'Scope'] },
    { id: 'strategy', label: 'Presentation Strategy', eyebrow: '04 · Prioritize', input: ['Product facts', 'Customer needs', 'Opportunity gaps'], decision: 'What gets P0, P1, or P2 priority?', output: ['Priority order', 'Channel mappings', 'Proof plan'], validation: ['Fact coverage', 'Claim safety', 'Business relevance'] },
    { id: 'planning', label: 'AI Content Planning', eyebrow: '05 · Plan', input: ['Product Truth', 'Competitor insight', 'Presentation strategy'], decision: 'What should each asset communicate?', output: ['Scene', 'Composition', 'Prompt', 'Restrictions'], validation: ['Product consistency', 'Visual objective', 'Claim safety'] },
    { id: 'generation', label: 'Image / Video', eyebrow: '06 · Generate', input: ['Typed requests', 'Canonical reference', 'Provider policy'], decision: 'Which provider request executes the plan?', output: ['Generated image', 'Provider metadata', 'Prompt hash'], validation: ['Request hash', 'Output checksum', 'Retry policy'] },
    { id: 'qa', label: 'AI QA', eyebrow: '07 · Evaluate', input: ['Generated asset', 'Plan requirements', 'Product Truth'], decision: 'Is the visual evidence sufficient and safe?', output: ['PASS / FAIL / NEEDS_REVIEW', 'Findings', 'Failure types'], validation: ['Parser', 'Deterministic rules', 'Raw response archive'] },
    { id: 'calibration', label: 'Human Calibration', eyebrow: '08 · Correct', input: ['QA findings', 'Image version', 'Reviewer feedback'], decision: 'Accept, revise, or reject?', output: ['Evaluation', 'Revision task', 'Version history'], validation: ['Human verdict', 'Explicit changes', 'No silent overwrite'] },
    { id: 'delivery', label: 'Approval / Delivery', eyebrow: '09 · Ship', input: ['Exact artifact versions', 'Approvals', 'Source assets'], decision: 'Is this exact version eligible to export?', output: ['Immutable ZIP', 'Manifest', 'SHA-256 records'], validation: ['Exact-version approval', 'Project scope', 'Export gate'] },
  ],
  listing: {
    status: 'Prototype',
    title: 'ASTM F136 Titanium Hinged Septum Ring 3PCS',
    bullets: ['Implant-grade titanium', 'Three wearable styles', 'Secure hinged closure', '18G / 20G options', 'Gold PVD finish'],
    trace: [
      { evidence: 'Material claims require proof', concern: 'Skin sensitivity', decision: 'Lead with source-linked material', output: 'ASTM F136 titanium' },
      { evidence: 'Repeated size comparison', concern: 'Size uncertainty', decision: 'Make selection data explicit', output: '18G / 20G · 8mm' },
      { evidence: 'Grouped assortment pattern', concern: 'What is included?', decision: 'Name all three styles', output: 'Classic · Double-layer · CZ' },
    ],
  },
  images: [
    {
      id: 'image_01', label: 'Product Identity', role: 'PRODUCT_IDENTITY_MAIN', priority: 'P0',
      decisionQuestion: 'What is the product and its included set?', customerNeed: 'Keep the main product presentation while fixing language.',
      strategyReason: 'Product identity is the first purchase blocker; preserve the three canonical configurations.',
      before: asset('p1/p1.jpg'),
      versions: [
        { label: 'V1 · Wan', src: asset('output/wan_baseline_v1/image_01.png'), status: 'NEEDS_REVIEW', change: 'Canonical-first generation baseline' },
        { label: 'V2 · GPT Image', src: asset('output/gpt_image_2_from_wan/image_01.png'), status: 'Pending calibration', change: 'English-copy optimization attempted' },
        { label: 'V3 · Revision', src: asset('output/gpt_image_2_new/image_01.png'), status: 'Pending calibration', change: 'English hierarchy revised' },
      ],
      prompt: 'Replace all Chinese copy with natural English without changing the existing product composition.',
      requiredEvidence: ['Three configurations visible', 'Color-accurate metallic finish', 'Product-dominant white field'],
      constraints: ['Do not alter product appearance', 'Do not add people', 'Do not change quantity'],
      qaStatus: 'NEEDS_REVIEW', qaIssues: ['Decision coverage partial', 'Material proof unsupported', 'Scale unverified'],
    },
    {
      id: 'image_02', label: 'On-body Wearing', role: 'WEAR_STYLE_TRIPTYCH', priority: 'P0',
      decisionQuestion: 'How does the product look when worn?', customerNeed: 'Show a realistic product-to-face relationship.',
      strategyReason: 'Use a human-scene reference for composition while preserving first-party product identity.',
      before: asset('p1/pic02.jpg'),
      versions: [
        { label: 'V1 · Wan', src: asset('output/wan_baseline_v1/image_02.png'), status: 'NEEDS_REVIEW', change: 'Baseline visual generation' },
        { label: 'V2 · GPT Image', src: asset('output/gpt_image_2_from_wan/image_02.png'), status: 'Pending calibration', change: 'Rebuilt on-body composition' },
        { label: 'V3 · Revision', src: asset('output/gpt_image_2_new/image_02.png'), status: 'Pending calibration', change: 'Reference-guided revision' },
      ],
      prompt: 'Show the realistic on-face effect, expression, and atmosphere of a person wearing the nose ring.',
      requiredEvidence: ['On-body appearance', 'Realistic placement', 'Product-to-face relationship'],
      constraints: ['Reference is not an identity source', 'No redundant set explanation', 'Preserve geometry'],
      qaStatus: 'NEEDS_REVIEW', qaIssues: ['Label/content mismatch observation', 'Human review required'],
    },
    {
      id: 'image_03', label: 'Size Choice', role: 'SIZE_CHOICE_PROOF', priority: 'P0',
      decisionQuestion: 'How should 18G / 20G / 8mm be understood?', customerNeed: 'Reduce size and placement selection uncertainty.',
      strategyReason: 'Keep confirmed dimensions explicit without inferring worn scale from a product-only image.',
      before: asset('p1/s2.jpg'),
      versions: [
        { label: 'V1 · Wan', src: asset('output/wan_baseline_v1/image_03.png'), status: 'NEEDS_REVIEW', change: 'Size-choice proof baseline' },
        { label: 'V2 · GPT Image', src: asset('output/gpt_image_2_from_wan/image_03.png'), status: 'Pending calibration', change: 'English fact presentation' },
        { label: 'V3 · Revision', src: asset('output/gpt_image_2_new/image_03.png'), status: 'Pending calibration', change: 'Revised selection layout' },
      ],
      prompt: 'Preserve the size and piercing guide while replacing Chinese copy with English.',
      requiredEvidence: ['18G / 20G labels', '8mm inner diameter', 'Approved placements only'],
      constraints: ['Do not invent measurements', 'No inferred worn scale', 'Keep Product Truth unchanged'],
      qaStatus: 'NEEDS_REVIEW', qaIssues: ['Scale unverified', 'Missing visual evidence', 'Unsupported claim detected'],
    },
    {
      id: 'image_04', label: 'Material Evidence', role: 'MATERIAL_EVIDENCE', priority: 'P1',
      decisionQuestion: 'What supports the material and finish story?', customerNeed: 'Reduce doubt about titanium, PVD, and CZ information.',
      strategyReason: 'Use approved claim IDs; do not fabricate a certificate that the repository does not contain.',
      before: asset('p1/s3.jpg'),
      versions: [
        { label: 'V1 · Wan', src: asset('output/wan_baseline_v1/image_04.png'), status: 'NEEDS_REVIEW', change: 'Material-evidence baseline' },
        { label: 'V2 · GPT Image', src: asset('output/gpt_image_2_from_wan/image_04.png'), status: 'Pending calibration', change: 'Material close-up revision' },
        { label: 'V3 · Revision', src: asset('output/gpt_image_2_new/image_04.png'), status: 'Pending calibration', change: 'Copy and detail revision' },
      ],
      prompt: 'Preserve the material and craft close-up while replacing Chinese copy with English.',
      requiredEvidence: ['ASTM F136 text', '18K Gold PVD finish', 'Visible CZ detail'],
      constraints: ['No certificate proof', 'No fabricated test report', 'No medical cure claim'],
      qaStatus: 'NEEDS_REVIEW', qaIssues: ['Decision not covered', 'Visual evidence missing', 'Unsupported claim detected'],
    },
    {
      id: 'image_05', label: 'Multi-scene Wearing', role: 'STRUCTURE_USE_DETAIL', priority: 'P1',
      decisionQuestion: 'How does the product read across wearing contexts?', customerNeed: 'Compare realistic looks and placements.',
      strategyReason: 'Rebuild the composition from a scene reference without copying competitor product identity.',
      before: asset('p1/pic05.jpg'),
      versions: [
        { label: 'V1 · Wan', src: asset('output/wan_baseline_v1/image_05.png'), status: 'NEEDS_REVIEW', change: 'Structure/use baseline' },
        { label: 'V2 · GPT Image', src: asset('output/gpt_image_2_from_wan/image_05.png'), status: 'Pending calibration', change: 'Multi-person rebuild' },
        { label: 'V3 · Revision', src: asset('output/gpt_image_2_new/image_05.png'), status: 'Pending calibration', change: 'Scene diversity revision' },
      ],
      prompt: 'Show realistic wearing effects across multiple people, piercing positions, and scenes.',
      requiredEvidence: ['Multiple people', 'Placement variation', 'Product identity consistency'],
      constraints: ['No mechanism explanation', 'Do not copy reference identity', 'Preserve material appearance'],
      qaStatus: 'NEEDS_REVIEW', qaIssues: ['Decision coverage partial', 'Scale unverified', 'Human review required'],
    },
    {
      id: 'image_06', label: 'Hinge Operation', role: 'HINGE_OPERATION_DEMO', priority: 'P1',
      decisionQuestion: 'How does the hinged clasp operate?', customerNeed: 'Understand opening, positioning, and closing.',
      strategyReason: 'Use a hand-operation reference for sequence and angle, not product identity.',
      before: asset('p1/pic06.jpg'),
      versions: [
        { label: 'V1 · Wan', src: asset('output/wan_baseline_v1/image_06.png'), status: 'NEEDS_REVIEW', change: 'Wear-style baseline' },
        { label: 'V2 · GPT Image', src: asset('output/gpt_image_2_from_wan/image_06.png'), status: 'Pending calibration', change: 'Operation composition rebuilt' },
        { label: 'V3 · Revision', src: asset('output/gpt_image_2_new/image_06.png'), status: 'Pending calibration', change: 'Step sequence revision' },
      ],
      prompt: 'Show by hand-operation steps how the hinged nose ring opens, is positioned, and closes.',
      requiredEvidence: ['Hand operation', 'Visible hinge', 'Opening / closing sequence'],
      constraints: ['Keep anatomy plausible', 'No product morphing', 'Reference is not identity source'],
      qaStatus: 'NEEDS_REVIEW', qaIssues: ['Visual evidence missing', 'Scale unverified', 'Human review required'],
    },
  ],
  video: {
    status: 'Blocked', model: 'doubao-seedance-2-5-260628',
    goal: 'Show the three-product set, hinge operation, and worn result in a 15-second Amazon listing sequence.',
    sequence: ['Show exact 3PCS set', 'Demonstrate hinge clasp', 'Place and show worn result'],
    source: asset('p1/p1.jpg'),
    failure: 'Provider returned ModelNotOpen (HTTP 404); no task_id and no final video asset were produced.',
  },
  qa: {
    generated: 6, needsReview: 6, passed: 0, failed: 0,
    failureCounts: [
      { label: 'Missing visual evidence', count: 6 },
      { label: 'Unverified scale', count: 5 },
      { label: 'Decision not covered', count: 3 },
      { label: 'Unsupported claim', count: 3 },
    ],
  },
  architecture: [
    { layer: 'Frontend', technology: 'React · TypeScript · OpenAPI client', businessFunction: 'Workspace interaction and evidence inspection' },
    { layer: 'API', technology: 'FastAPI · Pydantic', businessFunction: 'Typed project and artifact operations' },
    { layer: 'Workflow', technology: 'Python services · job state', businessFunction: 'Research, planning, generation, QA orchestration' },
    { layer: 'AI providers', technology: 'Wan · OpenAI-compatible image · Qwen-VL · Seedance adapter', businessFunction: 'Generation and visual evaluation; providers are opt-in' },
    { layer: 'Validation', technology: 'Schema · deterministic rules · QA parser', businessFunction: 'Fact, plan, response, and claim checks' },
    { layer: 'Storage', technology: 'SQLite · JSON artifacts · checksums', businessFunction: 'Versions, provenance, jobs, and review state' },
    { layer: 'Delivery', technology: 'Exact-version approval · manifest export', businessFunction: 'Prevent unapproved artifacts from shipping' },
  ],
  capabilities: [
    { group: 'Business', items: ['Cross-border e-commerce', 'SKU truth modeling', 'Competitor evidence', 'Listing strategy', 'Marketing assets'] },
    { group: 'AI', items: ['Image generation', 'Vision QA', 'Prompt planning', 'Video prompt workflow', 'Provider adapters'] },
    { group: 'Engineering', items: ['Python', 'FastAPI', 'Typed schema', 'Async job state', 'Versioning', 'Deterministic validation'] },
    { group: 'Production', items: ['Human calibration', 'Revision tasks', 'Exact-version approval', 'Manifest export', 'Failure transparency'] },
  ],
  sources: [
    'data/first_party_catalog.json',
    'examples/demo_sku/generated-fixtures/image_plan.json',
    'output/wan_baseline_v1/manifest.json',
    'output/wan_baseline_v1/qa/qa_summary.json',
    'output/calibration/session_cal_gpt_image_2.json',
    'output/video/response.json',
    'docs/phase3-implementation.md',
  ],
};
