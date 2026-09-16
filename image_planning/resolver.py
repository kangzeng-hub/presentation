"""Image Plan -> Template Registry resolver."""

from __future__ import annotations

from typing import Any

from .models import ImagePlan, ResolvedTemplate, ValidationError


def resolve_image_plan(plan: ImagePlan, registry: dict[str, Any]) -> list[ResolvedTemplate]:
    templates = {item["template_id"]: item for item in registry["templates"]}
    resolved = []
    for item in plan.images:
        template = templates.get(item.template_id)
        if template is None:
            raise ValidationError(f"unknown template_id: {item.template_id}")
        resolved.append(ResolvedTemplate(
            image_id=item.image_id,
            template_id=item.template_id,
            layout=template["layout"]["canvas"],
            composition="; ".join(template["layout"]["major_regions"]),
            visual_hierarchy=template["layout"]["information_hierarchy"],
            required_elements=[*template["result"]["required_visual_evidence"], *item.required_visual_evidence],
            allowed_style_elements=[template["style"][key] for key in ("camera_feel", "lighting", "background", "color_treatment", "realism")],
            forbidden_elements=[*template["information_layer"]["forbidden_content"], *item.forbidden_elements],
        ))
    return resolved
