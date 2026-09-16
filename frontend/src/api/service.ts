import {client,request} from './client';
export const apiService={
 getProject:async(projectId='demo-project')=>request(await (client as any).GET('/projects/{project_id}',{params:{path:{project_id:projectId}}})),
 getProjects:async()=>request(await (client as any).GET('/projects',{})),
 startResearch:async(projectId:string,urls:string[])=>request(await (client as any).POST('/projects/{project_id}/competitor-research',{params:{path:{project_id:projectId}},body:{urls}})),
 generateInsight:async(projectId:string)=>request(await (client as any).POST('/projects/{project_id}/competitor-insight',{params:{path:{project_id:projectId}}})),
 generateStrategy:async(projectId:string)=>request(await (client as any).POST('/projects/{project_id}/strategy',{params:{path:{project_id:projectId}}})),
 generateListing:async(projectId:string)=>request(await (client as any).POST('/projects/{project_id}/listing',{params:{path:{project_id:projectId}}})),
 generateImagePlan:async(projectId:string)=>request(await (client as any).POST('/projects/{project_id}/images/plan',{params:{path:{project_id:projectId}}})),
 generateImages:async(projectId:string)=>request(await (client as any).POST('/projects/{project_id}/images/generate',{params:{path:{project_id:projectId}}})),
 generateVideo:async(projectId:string,body:any)=>request(await (client as any).POST('/projects/{project_id}/video/plan',{params:{path:{project_id:projectId}},body}))
};
