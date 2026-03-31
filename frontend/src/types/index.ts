export interface McpServer {
  id: number
  name: string
  github_url: string | null
  local_path: string
  project_type: string | null
  command: string
  args: string[]
  env: Record<string, string>
  enabled: boolean
  auto_update: boolean
  auto_restart: boolean
  status: string
  last_commit: string | null
  created_at: string | null
  updated_at: string | null
  tools_count: number
}

export interface McpTool {
  name: string
  original_name?: string
  description: string
  input_schema: Record<string, any>
}

export interface McpResource {
  uri: string
  original_uri?: string
  name: string
  description: string
}

export interface LogEntry {
  timestamp: string
  server_id: number
  level: string
  message: string
}

export interface SystemInfo {
  total_servers: number
  running: number
  stopped: number
  error: number
  total_tools: number
  total_resources: number
  total_prompts: number
  gateway_endpoint: string
}

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}
