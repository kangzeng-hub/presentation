# Presentation Demo Calibration Audit

## A. Can the demo run end to end?

Not reliably. The visible flow starts at a seeded project and can display Product Truth, research, Listing, Images, and Video, but the current server does not persist all generated objects through every GET/POST path. The UI also has no Overview route, no visible Generate Insight or Generate Strategy actions, and the research POST jumps directly to `completed`.

## B. Functional but weak business meaning

- Research is presented as URL capture and cards; evidence, pain points, and priority ranking are too thin.
- Listing shows editable fields but does not map bullets to strategy decisions.
- Images show generic prompts and repeated `product_identity`; role/purpose does not explain the purchase driver.
- Video shows a prompt but does not show its Product Truth, strategy, Listing, or Image context.

## C. Navigation without data linkage

All sections share a project fetch, but the current UI does not visibly show Insight -> Strategy -> output mappings. There are service methods for Insight and Strategy, but no buttons or rendered strategy transition. Images and Video are therefore mostly navigation destinations rather than downstream expressions of the same decision.

## D. Mock placeholder content

- One seeded project is used and research initially has no competitors.
- Competitors have one generic bullet, empty reviews/images, and no negative/neutral/positive examples.
- Insight/Strategy are absent until their endpoints are called, while the UI has no controls to call them.
- Image cards repeat one role and generic prompt; QA and human review are labels/buttons without persisted review actions.
- The Video plan is generic and has only two scenes.

## E. What a business lead may not understand

The current screen reads as four AI utilities. It does not answer: what customer problem was found, why a specific priority was chosen, and how that priority changed the Listing, ImagePlan, and Video prompt. The absence of a compact overview and explicit source-to-output mapping is the biggest demo risk.

## Priority

### P0: must fix before tomorrow

1. Seed one coherent SKU plus two credible competitor snapshots with review evidence, then expose Insight and Strategy generation in the Research flow.
2. Add a lightweight Overview/current-strategy block showing `Competitor Evidence -> Customer Need -> Priority -> Strategy -> Listing/Image/Video`.
3. Render explicit Strategy -> Listing and Strategy -> Image mappings; ensure six image cards have distinct business purposes and purchase drivers.
4. Make Video visibly consume the same strategy and show a four-step scene plan; remove any implication that a video was generated.
5. Add button feedback and persisted review state labels so the demo can show Generate -> QA -> Human Review.

### P1: fix if time permits

- Show clickable evidence excerpts and competitor review buckets.
- Add an Overview route and progress indicators for Listing, Images, and Video.
- Support edited Listing content without losing generated content in the demo.

### P2: do not fix for tomorrow

- Real crawler/LLM/image/video integrations.
- Production persistence, authentication, full contract test infrastructure.
- Reworking existing ImagePlan, generation, QA, or calibration internals.

