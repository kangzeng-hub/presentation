from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Response, status

from backend.repositories.workspace import WorkspaceRepository
from backend.schemas.workspace import Approval, ApprovalCreate, ArtifactApprovalCreate, ArtifactVersion, CompetitorInsight, CompetitorSnapshot, CreateProject, ErrorResponse, ExportManifest, ImagePlanRef, Job, ListingPlan, PresentationStrategy, ProductTruth, Project, ProjectWorkspace, QAReport, ResearchRequest, VideoPlan, VideoPlanInput
from backend.services.workspace import WorkspaceService
from backend.services.delivery import DeliveryError


def create_workspace_router(service: WorkspaceService | None = None) -> APIRouter:
    service = service or WorkspaceService(WorkspaceRepository())
    router = APIRouter(tags=["workspace"])

    def not_found(exc: KeyError) -> HTTPException:
        return HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": f"Resource not found: {exc.args[0]}", "details": {}})

    @router.get("/projects", response_model=list[Project], responses={500: {"model": ErrorResponse}})
    def list_projects() -> list[dict]:
        service.ensure_demo_project()
        return service.repository.list_projects()

    @router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
    def create_project(payload: CreateProject) -> dict:
        try:
            return service.create_project(payload)
        except DeliveryError as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "message": exc.message, "details": exc.details})

    @router.get("/projects/{project_id}", response_model=ProjectWorkspace, responses={404: {"model": ErrorResponse}})
    def get_project(project_id: str) -> dict:
        try:
            return service.get_project(project_id)
        except KeyError as exc:
            raise not_found(exc)

    @router.get("/projects/{project_id}/product-truth", response_model=ProductTruth, responses={404: {"model": ErrorResponse}})
    def get_product_truth(project_id: str) -> dict:
        try:
            value = service._artifact(project_id, "product_truth")
            if value is None:
                raise KeyError(project_id)
            return value
        except KeyError as exc:
            raise not_found(exc)

    @router.put("/projects/{project_id}/product-truth", response_model=ProductTruth)
    def update_product_truth(project_id: str, payload: ProductTruth) -> dict:
        try:
            service.get_project(project_id)
            return service.update_product_truth(project_id, payload)
        except KeyError as exc:
            raise not_found(exc)
        except DeliveryError as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "message": exc.message, "details": exc.details})

    @router.get("/projects/{project_id}/competitors", response_model=list[CompetitorSnapshot])
    def list_competitors(project_id: str) -> list[dict]:
        try:
            service.get_project(project_id)
            return service._artifact(project_id, "competitor_snapshot") or []
        except KeyError as exc:
            raise not_found(exc)

    @router.post("/projects/{project_id}/competitor-research", response_model=Job, status_code=status.HTTP_202_ACCEPTED)
    def research(project_id: str, payload: ResearchRequest, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict:
        try:
            service.get_project(project_id)
            return service.research(project_id, payload.urls, idempotency_key)
        except KeyError as exc:
            raise not_found(exc)

    @router.get("/projects/{project_id}/competitor-insight", response_model=CompetitorInsight)
    def get_insight(project_id: str) -> dict:
        try:
            service.get_project(project_id)
            value = service._artifact(project_id, "competitor_insight")
            if value is None:
                raise KeyError(project_id)
            return value
        except KeyError as exc:
            raise not_found(exc)

    @router.post("/projects/{project_id}/competitor-insight", response_model=CompetitorInsight, status_code=status.HTTP_202_ACCEPTED)
    def generate_insight(project_id: str) -> dict:
        try:
            return service.insight(project_id)
        except KeyError as exc:
            raise not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": str(exc), "details": {}})

    @router.get("/projects/{project_id}/strategy", response_model=PresentationStrategy)
    def get_strategy(project_id: str) -> dict:
        try:
            service.get_project(project_id)
            value = service._artifact(project_id, "strategy")
            if value is None:
                raise KeyError(project_id)
            return value
        except KeyError as exc:
            raise not_found(exc)

    @router.post("/projects/{project_id}/strategy", response_model=PresentationStrategy, status_code=status.HTTP_202_ACCEPTED)
    def generate_strategy(project_id: str) -> dict:
        try:
            return service.strategy(project_id)
        except KeyError as exc:
            raise not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": str(exc), "details": {}})

    @router.get("/projects/{project_id}/listing", response_model=ListingPlan)
    def get_listing(project_id: str) -> dict:
        value = service._artifact(project_id, "listing")
        if value is None:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Listing not found", "details": {}})
        return value

    @router.post("/projects/{project_id}/listing", response_model=ListingPlan, status_code=status.HTTP_202_ACCEPTED)
    def generate_listing(project_id: str) -> dict:
        try:
            return service.listing(project_id)
        except KeyError as exc:
            raise not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": str(exc), "details": {}})

    @router.get("/projects/{project_id}/images", response_model=list[ImagePlanRef])
    def list_images(project_id: str) -> list[dict]:
        value = service._artifact(project_id, "image_plan")
        return [value] if value else []

    @router.post("/projects/{project_id}/images/plan", response_model=ImagePlanRef, status_code=status.HTTP_202_ACCEPTED)
    def generate_image_plan(project_id: str) -> dict:
        try:
            return service.image_plan(project_id)
        except KeyError as exc:
            raise not_found(exc)

    @router.post("/projects/{project_id}/images/generate", response_model=Job, status_code=status.HTTP_202_ACCEPTED)
    def generate_images(project_id: str, idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None) -> dict:
        try:
            return service.image_generation(project_id, idempotency_key)
        except KeyError as exc:
            raise not_found(exc)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": str(exc), "details": {}})

    @router.get("/projects/{project_id}/qa", response_model=list[QAReport])
    def get_qa(project_id: str) -> list[dict]:
        try:
            service.get_project(project_id)
            return service.qa(project_id)
        except KeyError as exc:
            raise not_found(exc)

    @router.get("/projects/{project_id}/video", response_model=VideoPlan)
    def get_video(project_id: str) -> dict:
        value = service._artifact(project_id, "video_plan")
        if value is None:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Video plan not found", "details": {}})
        return value

    @router.post("/projects/{project_id}/video/plan", response_model=VideoPlan, status_code=status.HTTP_201_CREATED)
    def generate_video(project_id: str, payload: VideoPlanInput) -> dict:
        try:
            service.get_project(project_id)
            return service.video_plan(project_id, payload)
        except KeyError as exc:
            raise not_found(exc)

    @router.get("/projects/{project_id}/approvals", response_model=list[Approval])
    def list_approvals(project_id: str) -> list[dict]:
        try:
            service.get_project(project_id)
        except KeyError as exc:
            raise not_found(exc)
        return service.repository.list_approvals(project_id)

    @router.post("/projects/{project_id}/approvals", response_model=Approval, status_code=status.HTTP_201_CREATED)
    def create_approval(project_id: str, payload: ApprovalCreate) -> dict:
        try:
            service.get_project(project_id)
            artifact = service.repository.get_artifact(payload.artifact_version_id)
            if artifact is None or artifact["project_id"] != project_id:
                raise HTTPException(status_code=404, detail={"code": "ARTIFACT_VERSION_NOT_FOUND", "message": "Artifact version not found", "details": {}})
            return service.approve_artifact(project_id, artifact.get("artifact_id") or artifact["artifact_type"], artifact["version"], payload.status, payload.reviewer, payload.comment)
        except KeyError as exc:
            raise not_found(exc)
        except DeliveryError as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "message": exc.message, "details": exc.details})

    @router.post("/projects/{project_id}/artifacts/{artifact_id}/versions/{version}/approval", response_model=Approval, status_code=status.HTTP_201_CREATED)
    def approve_exact_version(project_id: str, artifact_id: str, version: int, payload: ArtifactApprovalCreate) -> dict:
        try:
            service.get_project(project_id)
            return service.approve_artifact(project_id, artifact_id, version, payload.decision, payload.approved_by, payload.comment)
        except KeyError as exc:
            raise not_found(exc)
        except DeliveryError as exc:
            raise HTTPException(status_code=404 if exc.code == "ARTIFACT_VERSION_NOT_FOUND" else 409, detail={"code": exc.code, "message": exc.message, "details": exc.details})

    @router.get("/projects/{project_id}/artifacts/{artifact_id}/versions/{version}/approval", response_model=Approval, responses={404: {"model": ErrorResponse}})
    def get_exact_version_approval(project_id: str, artifact_id: str, version: int) -> dict:
        try:
            service.get_project(project_id)
            artifact = service.repository.get_artifact_version(project_id, artifact_id, version)
            if artifact is None:
                raise HTTPException(status_code=404, detail={"code": "ARTIFACT_VERSION_NOT_FOUND", "message": "Artifact version not found", "details": {"artifact_id": artifact_id, "artifact_version": version}})
            approval = service.repository.get_approval_for_version(project_id, artifact.get("artifact_id") or artifact["artifact_type"], version)
            if approval is None:
                raise HTTPException(status_code=404, detail={"code": "APPROVAL_NOT_FOUND", "message": "Approval not found for artifact version", "details": {"artifact_id": artifact_id, "artifact_version": version}})
            return approval
        except KeyError as exc:
            raise not_found(exc)

    @router.post("/projects/{project_id}/export", response_model=ExportManifest)
    def export_project(project_id: str) -> dict:
        try:
            return service.export(project_id)
        except KeyError as exc:
            raise not_found(exc)
        except DeliveryError as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "message": exc.message, "details": exc.details})

    @router.post("/projects/{project_id}/exports", response_model=ExportManifest)
    def create_export(project_id: str) -> dict:
        return export_project(project_id)

    @router.get("/projects/{project_id}/exports", response_model=list[ExportManifest])
    def list_exports(project_id: str) -> list[dict]:
        try:
            service.get_project(project_id)
        except KeyError as exc:
            raise not_found(exc)
        return [item["manifest_json"] for item in service.repository.list_exports(project_id)]

    @router.get("/projects/{project_id}/exports/{export_id}", response_model=ExportManifest)
    def get_export(project_id: str, export_id: str) -> dict:
        try:
            service.get_project(project_id)
        except KeyError as exc:
            raise not_found(exc)
        value = service.repository.get_export(export_id)
        if value is None or value["project_id"] != project_id:
            raise HTTPException(status_code=404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Export not found", "details": {}})
        return value["manifest_json"]

    @router.get("/jobs/{job_id}", response_model=Job)
    def get_job(job_id: str) -> dict:
        value = service.repository.get_job(job_id)
        if value is None:
            raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": "Job not found", "details": {}})
        return value

    @router.post("/jobs/{job_id}/cancel", response_model=Job)
    def cancel_job(job_id: str) -> dict:
        try:
            return service.runner.cancel(job_id)
        except KeyError:
            raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": "Job not found", "details": {}})

    @router.post("/jobs/{job_id}/retry", response_model=Job)
    def retry_job(job_id: str) -> dict:
        job = service.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": "Job not found", "details": {}})
        if job["status"] != "failed":
            raise HTTPException(status_code=409, detail={"code": "CONFLICT", "message": "Only failed jobs can be retried", "details": {}})
        return service.retry_job(job_id)

    return router
