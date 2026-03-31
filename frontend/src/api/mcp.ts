import api from './index'
import type { ApiResponse, McpServer, McpTool, McpResource, LogEntry, SystemInfo } from '../types'

export const serverApi = {
  list(status?: string) {
    return api.get<any, ApiResponse<McpServer[]>>('/servers', { params: { status } })
  },
  get(id: number) {
    return api.get<any, ApiResponse<McpServer>>(`/servers/${id}`)
  },
  create(data: {
    name?: string
    github_url?: string
    local_path?: string
    command?: string
    args?: string[]
    env?: Record<string, string>
    auto_update?: boolean
    auto_restart?: boolean
  }) {
    return api.post<any, ApiResponse<McpServer>>('/servers', data)
  },
  update(id: number, data: Record<string, any>) {
    return api.put<any, ApiResponse<McpServer>>(`/servers/${id}`, data)
  },
  delete(id: number, deleteRepo = false) {
    return api.delete<any, ApiResponse>(`/servers/${id}`, { params: { delete_repo: deleteRepo } })
  },
  start(id: number) {
    return api.post<any, ApiResponse>(`/servers/${id}/start`)
  },
  stop(id: number) {
    return api.post<any, ApiResponse>(`/servers/${id}/stop`)
  },
  restart(id: number) {
    return api.post<any, ApiResponse>(`/servers/${id}/restart`)
  },
  updateRepo(id: number) {
    return api.post<any, ApiResponse>(`/servers/${id}/update`)
  },
  getTools(id: number) {
    return api.get<any, ApiResponse<McpTool[]>>(`/servers/${id}/tools`)
  },
  getLogs(id: number, limit = 100) {
    return api.get<any, ApiResponse<LogEntry[]>>(`/servers/${id}/logs`, { params: { limit } })
  },
}

export const toolApi = {
  listAll() {
    return api.get<any, ApiResponse<McpTool[]>>('/tools')
  },
  listResources() {
    return api.get<any, ApiResponse<McpResource[]>>('/tools/resources')
  },
}

export const systemApi = {
  health() {
    return api.get<any, ApiResponse>('/system/health')
  },
  info() {
    return api.get<any, ApiResponse<SystemInfo>>('/system/info')
  },
}
