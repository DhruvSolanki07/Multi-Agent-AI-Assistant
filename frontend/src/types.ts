export type AgentType =
  | 'planner'
  | 'searcher'
  | 'documenter'
  | 'summarizer'
  | 'writer'
  | 'critic'

export type AgentStage = 'pending' | 'running' | 'done' | 'failed'

export type TaskStatus = 'queued' | 'running' | 'done' | 'failed'

export interface SourceRef {
  title: string
  url?: string | null
  snippet?: string
  source_type: 'web' | 'document' | 'local'
  doc_id?: string | null
}

export interface AgentEvent {
  seq: number
  agent: AgentType
  stage: AgentStage
  message: string
  detail?: Record<string, unknown> | null
}

export interface ResearchTask {
  id: string
  query: string
  status: TaskStatus
  created_at: string
  updated_at: string
  agent_events: AgentEvent[]
  plan: string[]
  sources: SourceRef[]
  findings: string[]
  report: string
  report_markdown: string
  gaps: string[]
  error?: string | null
}

export interface NewTaskResponse {
  id: string
  status: TaskStatus
}

export interface HealthInfo {
  ok: boolean
  llm_configured: boolean
  search_configured: boolean
  agents: string[]
}

export type SSEEvent =
  | { type: 'event'; task_id: string; seq: number; agent: AgentType; stage: AgentStage; message: string; detail?: unknown }
  | { type: 'done'; task_id: string; status: TaskStatus }
  | { type: 'closed'; task_id: string }