import {client,request} from './client';
import type {components} from '../generated/api';

export type Workspace = components['schemas']['ProjectWorkspace'] & {
  competitors?: components['schemas']['CompetitorSnapshot'][];
  research?: components['schemas']['Job'];
  listing?: components['schemas']['ListingPlan'];
  image_plan?: components['schemas']['ImagePlanRef'];
  image_generation?: components['schemas']['Job'];
  qa?: components['schemas']['QAReport'][];
  video?: components['schemas']['VideoPlan'];
  approvals?: components['schemas']['Approval'][];
  active_jobs?: components['schemas']['Job'][];
};

export const apiService={
 getProject:async(projectId='demo-project')=>request(await client.GET('/projects/{project_id}',{params:{path:{project_id:projectId}}})),
 getProjects:async()=>request(await client.GET('/projects',{})),
 startResearch:async(projectId:string,urls:string[])=>request(await client.POST('/projects/{project_id}/competitor-research',{params:{path:{project_id:projectId}},body:{urls}})),
 generateInsight:async(projectId:string)=>request(await client.POST('/projects/{project_id}/competitor-insight',{params:{path:{project_id:projectId}}})),
 generateStrategy:async(projectId:string)=>request(await client.POST('/projects/{project_id}/strategy',{params:{path:{project_id:projectId}}})),
 generateListing:async(projectId:string)=>request(await client.POST('/projects/{project_id}/listing',{params:{path:{project_id:projectId}}})),
 generateImagePlan:async(projectId:string)=>request(await client.POST('/projects/{project_id}/images/plan',{params:{path:{project_id:projectId}}})),
 generateImages:async(projectId:string)=>request(await client.POST('/projects/{project_id}/images/generate',{params:{path:{project_id:projectId}}})),
 getQA:async(projectId:string)=>request(await client.GET('/projects/{project_id}/qa',{params:{path:{project_id:projectId}}})),
 approveArtifact:async(projectId:string,artifactId:string,version:number,approvedBy:string,comment='')=>request(await client.POST('/projects/{project_id}/artifacts/{artifact_id}/versions/{version}/approval',{params:{path:{project_id:projectId,artifact_id:artifactId,version}},body:{decision:'approved',approved_by:approvedBy,comment}})),
 createExport:async(projectId:string)=>request(await client.POST('/projects/{project_id}/exports',{params:{path:{project_id:projectId}}})),
 getExport:async(projectId:string,exportId:string)=>request(await client.GET('/projects/{project_id}/exports/{export_id}',{params:{path:{project_id:projectId,export_id:exportId}}})),
 generateVideo:async(projectId:string,body:components['schemas']['VideoPlanInput'])=>request(await client.POST('/projects/{project_id}/video/plan',{params:{path:{project_id:projectId}},body})),
 getJob:async(jobId:string)=>request(await client.GET('/jobs/{job_id}',{params:{path:{job_id:jobId}}})),
 waitForJob:async(jobId:string, onUpdate?:(job:components['schemas']['Job'])=>void)=>{
   for(let attempt=0;attempt<30;attempt+=1){const job=await apiService.getJob(jobId); onUpdate?.(job); if(['completed','failed','cancelled'].includes(job.status)) return job; await new Promise(resolve=>setTimeout(resolve,250));}
   return apiService.getJob(jobId);
 }
};
