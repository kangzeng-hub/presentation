import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const contractPath = process.env.CONTRACT_PATH || resolve(here, "../contracts/openapi.yaml");
const contract = readFileSync(contractPath, "utf8");
if (!contract.startsWith("openapi: 3.1.0")) throw Error("contract missing");
const demoProduct = JSON.parse(readFileSync(resolve(here, "../examples/demo_sku/product.json"), "utf8"));
const projects = new Map();
const now = () => new Date().toISOString();
const advance = (project, stage) => {
  project.current_stage = stage;
  project.overall_status = "completed";
};
const seed = (id, sku, name) => {
  const p = {
    project_id: id,
    sku,
    project_name: name,
    overall_status: "queued",
    current_stage: "product_truth",
    created_at: now(),
    product_truth: {
      project_id: id,
      sku,
      product_name: demoProduct.product_name,
      category: "piercing jewelry",
      material: { base: "ASTM F136 titanium" },
      dimensions: { gauges: ["18G", "20G"] },
      variants: [],
      package_contents: ["classic hoop", "double-layer hoop", "CZ accent hoop"],
      product_features: ["hinged closure"],
      verified_claims: [
        {
          kind: "CLAIM",
          text: "ASTM F136 implant-grade titanium",
          source: "catalog",
        },
      ],
      product_images: demoProduct.product_images,
      source: ["examples/demo_sku/product.json"],
      version: 1,
    },
  };
  projects.set(id, p);
  return p;
};
seed(
  "demo-project",
  demoProduct.sku,
  "Synthetic Demo Presentation",
);
const send = (r, s, b) => {
  r.writeHead(s, {
    "content-type": "application/json",
    "access-control-allow-origin": "*",
  });
  r.end(JSON.stringify(b));
};
const error = (r, s, c, m) =>
  send(r, s, { error: { code: c, message: m, details: {} } });
const read = (req) =>
  new Promise((ok) => {
    let x = "";
    req.on("data", (d) => (x += d));
    req.on("end", () => {
      try {
        ok(x ? JSON.parse(x) : {});
      } catch {
        ok(null);
      }
    });
  });
const server = createServer(async (req, res) => {
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET,POST,PUT,OPTIONS",
      "access-control-allow-headers": "content-type",
    });
    return res.end();
  }
  const path = req.url.split("?")[0];
  if (path === "/health" && req.method === "GET")
    return send(res, 200, {
      status: "ok",
      service: "presentation-demo-backend",
    });
  if (path === "/projects" && req.method === "GET")
    return send(res, 200, [...projects.values()]);
  if (path === "/projects" && req.method === "POST") {
    const b = await read(req);
    if (!b?.sku || !b?.project_name)
      return error(
        res,
        400,
        "VALIDATION_ERROR",
        "sku and project_name are required",
      );
    return send(
      res,
      201,
      seed(`project-${projects.size + 1}`, b.sku, b.project_name),
    );
  }
  const m = path.match(/^\/projects\/([^/]+)(?:\/(.*))?$/);
  if (!m) return error(res, 404, "NOT_FOUND", "Route not found");
  const p = projects.get(m[1]);
  if (!p) return error(res, 404, "NOT_FOUND", "Project not found");
  const sub = m[2] || "";
  if (!sub) return send(res, 200, p);
  if (sub === "product-truth" && req.method === "GET")
    return send(res, 200, p.product_truth);
  if (sub === "product-truth" && req.method === "PUT") {
    const b = await read(req);
    if (!b) return error(res, 400, "VALIDATION_ERROR", "Invalid JSON");
    p.product_truth = {
      ...b,
      project_id: p.project_id,
      version: p.product_truth.version + 1,
    };
    ["strategy", "listing", "image_plan", "video"].forEach(
      (k) => {
        if (p[k]) p[k].stale = true;
      },
    );
    return send(res, 200, p.product_truth);
  }
  if (sub === "competitors" && req.method === "GET")
    return send(res, 200, p.competitors || []);
  if (sub === "competitor-research" && req.method === "POST") {
    const b = await read(req);
    if (!Array.isArray(b?.urls) || !b.urls.length)
      return error(res, 400, "VALIDATION_ERROR", "urls required");
    p.competitors = b.urls.map((url, i) => ({
      competitor_id: `${p.project_id}-c${i + 1}`,
      url,
      title: `Competitor ${i + 1}`,
      bullet_points: ["Visible assortment"],
      rating: 4.2,
      price: 19.99,
      reviews: [],
      negative_reviews: [],
      neutral_reviews: [],
      positive_reviews: [],
      images: [],
      crawl_status: "completed",
      raw_source: { mock: true },
    }));
    p.research = {
      job_id: `${p.project_id}-research`,
      status: "completed",
      competitor_ids: p.competitors.map((x) => x.competitor_id),
    };
    advance(p, "research");
    return send(res, 202, p.research);
  }
  if (sub === "competitor-insight" && req.method === "GET")
    return p.competitor_insight
      ? send(res, 200, p.competitor_insight)
      : error(res, 404, "NOT_FOUND", "Insight not found");
  if (sub === "competitor-insight" && req.method === "POST") {
    p.competitor_insight = {
      project_id: p.project_id,
      purchase_drivers: ["material safety"],
      customer_pain_points: ["size uncertainty"],
      competitor_claims: ["hypoallergenic"],
      competitor_strengths: ["clear assortment"],
      competitor_weaknesses: ["weak proof"],
      opportunity_gaps: ["source-linked proof"],
      priority_ranking: ["material safety"],
      evidence: (p.competitors || []).map((x) => ({
        snapshot_id: x.competitor_id,
        field: "bullet_points",
        excerpt: x.bullet_points[0],
      })),
      confidence: 0.85,
      version: (p.competitor_insight?.version || 0) + 1,
    };
    advance(p, "insight");
    return send(res, 202, p.competitor_insight);
  }
  if (sub === "strategy" && req.method === "GET")
    return p.strategy
      ? send(res, 200, p.strategy)
      : error(res, 404, "NOT_FOUND", "Strategy not found");
  if (sub === "strategy" && req.method === "POST") {
    if (!p.competitor_insight)
      return error(res, 409, "DEPENDENCY_ERROR", "Insight required");
    p.strategy = {
      project_id: p.project_id,
      primary_purchase_drivers: ["material safety", "comfort", "fit"],
      customer_pain_points: ["skin sensitivity"],
      core_differentiators: ["ASTM F136 titanium", "secure hinged closure"],
      product_claims: ["claim_f136_titanium"],
      proof_points: ["catalog-backed claim"],
      priority_order: ["material safety", "fit"],
      listing_mapping: {},
      image_mapping: {},
      video_mapping: {},
      version: (p.strategy?.version || 0) + 1,
      product_truth_version: p.product_truth.version,
      competitor_insight_version: p.competitor_insight.version,
      status: "completed",
    };
    advance(p, "strategy");
    return send(res, 202, p.strategy);
  }
  if (
    req.method === "POST" &&
    ["listing", "images/plan", "images/generate", "video/plan"].includes(sub)
  ) {
    if (sub === "listing" && !p.strategy)
      return error(res, 409, "DEPENDENCY_ERROR", "Strategy required");
    if (sub === "listing")
      p.listing = {
        project_id: p.project_id,
        product_truth_version: p.product_truth.version,
        insight_version: p.competitor_insight?.version || 1,
        strategy_version: p.strategy.version,
        title:
          "Demo Studio ASTM F136 Titanium Hinged Ring 3PCS, 18K Gold PVD Set, 18G/20G 8mm Multi-Style Rings",
        bullet_points: [
          "MATERIAL SAFETY: Made with ASTM F136 implant-grade titanium, finished with 18K Gold PVD; nickel-free and lead-free material details are clearly stated for shoppers who prioritize skin comfort.",
          "3PCS MULTI-STYLE SET: Includes one classic hoop, one double-layer hoop, and one CZ accent hoop so you can switch your look without buying separate pieces.",
          "SECURE HINGED CLOSURE: Precision hinged segmented ring with a flush seam and press-to-close clasp helps make opening, positioning, and closing straightforward.",
          "FIND YOUR FIT: Includes 18G and 20G gauge options with an 8mm inner diameter, giving you a clear starting point for septum, nostril, and other approved placements.",
          "ONE SET, MORE WAYS TO WEAR: A compact Gold-3PCS collection designed for everyday styling, gifting, and easy rotation between minimalist, layered, and CZ-accent looks.",
        ],
        product_description:
          "Explore the synthetic Demo Studio Gold-3PCS hinged ring set. This three-piece collection includes a classic hoop, double-layer hoop, and CZ accent hoop in an 18K Gold PVD finish over ASTM F136 implant-grade titanium. The hinged segmented construction uses a flush seam and press-to-close clasp for a clear closure design. With 18G and 20G options and an 8mm inner diameter, the set supports a clear fit comparison. The package includes exactly three rings.",
        claims_used: ["claim_f136_titanium"],
        strategy_refs: [`strategy:v${p.strategy.version}`],
        version: (p.listing?.version || 0) + 1,
        generated_content: {},
        edited_content: null,
        approved_content: null,
        status: "pending_review",
        model: "mock",
      };
      advance(p, "listing");
    if (sub === "images/plan")
      p.image_plan = {
        project_id: p.project_id,
        product_truth_version: p.product_truth.version,
        strategy_version: p.strategy?.version || 1,
        version: (p.image_plan?.version || 0) + 1,
        status: "completed",
        image_plan: {
          plan_version: "1.0.0",
          product_id: p.sku,
          images: Array.from({ length: 6 }, (_, i) => ({
            image_id: `image_${String(i + 1).padStart(2, "0")}`,
            role: "product_identity",
            prompt: "Strategy-backed prompt",
            generation_status: "queued",
            qa_status: "NEEDS_REVIEW",
            human_review_status: "pending_review",
          })),
        },
      };
      advance(p, "images");
    if (sub === "images/generate")
      p.image_generation = {
        project_id: p.project_id,
        strategy_version: p.image_plan?.strategy_version,
        status: "completed",
        version: (p.image_generation?.version || 0) + 1,
        model: "mock",
      };
    if (sub === "video/plan") {
      const b = await read(req);
      p.video = {
        ...(b || {}),
        project_id: p.project_id,
        strategy_version: p.strategy?.version || 1,
        listing_version: p.listing?.version || null,
        image_plan_version: p.image_plan?.version || null,
        status: "pending_review",
        version: (p.video?.version || 0) + 1,
        strategy_refs: [`strategy:v${p.strategy?.version || 1}`],
        final_prompt: b?.final_prompt || "Create a product demo.",
      };
      advance(p, "video");
    }
    return send(
      res,
      202,
      p[
        sub === "listing"
          ? "listing"
          : sub === "images/plan"
            ? "image_plan"
            : sub === "images/generate"
              ? "image_generation"
              : "video"
      ],
    );
  }
  if (sub === "listing" && req.method === "GET")
    return p.listing
      ? send(res, 200, p.listing)
      : error(res, 404, "NOT_FOUND", "Listing not found");
  if (sub === "images" && req.method === "GET")
    return send(res, 200, p.image_plan ? [p.image_plan] : []);
  if (sub === "video" && req.method === "GET")
    return p.video
      ? send(res, 200, p.video)
      : error(res, 404, "NOT_FOUND", "Video not found");
  return error(res, 404, "NOT_FOUND", "Route not found");
});
const host = process.env.HOST || "0.0.0.0";
const port = Number(process.env.PORT || 4010);
server.listen(port, host, () =>
  console.log(`Stateful demo backend on http://${host}:${port}`),
);
