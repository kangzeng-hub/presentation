from __future__ import annotations

import json
from .models import ProductVideoInput


def _value(value):
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value or "未提供")


def build_video_prompt(input: ProductVideoInput) -> str:
    p = input.product
    truth = "\n".join(f"- {k}: {_value(v)}" for k, v in p.items())
    refs = "\n".join(f"- {_value(x)}" for x in input.reference_images) or "- 未提供"
    selling = "\n".join(f"- {x}" for x in input.selling_points) or "- 未提供"
    concerns = "\n".join(f"- {x}" for x in input.customer_concerns) or "- 未提供"
    return f"""VIDEO GOAL
{input.video_goal}

PRODUCT TRUTH
{truth}
Selling points:
{selling}
Customer concerns:
{concerns}
Target scene: {input.target_scene or 'clean neutral product-demo setting'}
Reference images:
{refs}

PRODUCT DEMONSTRATION SEQUENCE
Create a dynamic 15-second Amazon listing video in one clean neutral setting with a real adult model and the exact product from the reference image. Begin with the complete set of exactly 3 products clearly visible on a small display surface. The model picks up one ring, briefly shows the hinge, flush seam, and press-to-close clasp, opens and closes it once, then carefully places it on the septum and finishes with a natural close-up wearing the ring. Use three clear consecutive actions in this order: show the three products, demonstrate the clasp, put on the ring and show the result. Keep the actions physically realistic and easy to follow. Use simple camera movement only: a slow push-in with a gentle close-up transition. Keep the same model, setting, lighting, product design, and gold finish throughout.

VISUAL STYLE
{input.video_style}. 15 seconds total, three clear consecutive actions, simple camera movement, clean commercial product video, realistic material and lighting, no distracting effects or text overlays.

PRODUCT CONSISTENCY CONSTRAINTS
Product facts override creative styling. Use the reference image for identity and keep exactly 3 products with the same shape, finish, and proportions. Preserve the hinged segmented ring, flush seam, and press clasp during the demonstration; do not invent unsupported details or change the product while it is being worn.

FORBIDDEN CONTENT
No invented product features, mechanisms, materials, stones, logos, claims, dimensions, or packaging. No quantity changes, product morphing, extra jewelry, awkward hands, incorrect anatomy, wrong piercing location, abrupt scene changes, excessive camera movement, sports, showering, sleeping, medical claims, or competitor products."""
