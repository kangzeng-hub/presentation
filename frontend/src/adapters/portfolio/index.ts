import { rawPortfolioEvidence, type PortfolioEvidence } from '../../data/portfolio';

export type PortfolioViewModel = PortfolioEvidence & {
  headline: string;
  subtitle: string;
  imageRunLabel: string;
  evidenceNote: string;
};

const assertEvidence = (data: PortfolioEvidence) => {
  if (data.images.length !== data.qa.generated) {
    throw new Error('Portfolio evidence mismatch: image plan and generated count differ.');
  }
  if (data.qa.passed + data.qa.failed + data.qa.needsReview !== data.qa.generated) {
    throw new Error('Portfolio evidence mismatch: QA totals are inconsistent.');
  }
};

export function buildPortfolioViewModel(data = rawPortfolioEvidence): PortfolioViewModel {
  assertEvidence(data);
  return {
    ...data,
    headline: 'AI-NATIVE CROSS-BORDER CONTENT PRODUCTION',
    subtitle: 'From SKU understanding to AI generation, quality validation and final delivery.',
    imageRunLabel: `${data.qa.generated} generated · ${data.qa.needsReview} need human review`,
    evidenceNote: 'All claims on this page are mapped to repository code, metadata, assets, or project records.',
  };
}

export async function discoverRecordedRuns(): Promise<Array<{ run_id: string; image_count: number; has_qa: boolean }>> {
  try {
    const response = await fetch('/api/artifacts/runs');
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
}
