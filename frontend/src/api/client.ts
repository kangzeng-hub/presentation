import createClient from 'openapi-fetch';
import type {paths} from '../generated/api';
const baseUrl=import.meta.env.VITE_API_BASE_URL||'http://127.0.0.1:4010';
export const client=createClient<paths>({baseUrl});
export async function request<T>(result: {data?: T; error?: unknown; response: Response}) { if(!result.response.ok) throw result.error||new Error(`HTTP ${result.response.status}`); return result.data as T; }
