import type { HealthInfo, NewTaskResponse, ResearchTask } from './types'

export const API_BASE = '/api'

async function parseError(res: Response): Promise<never> {
  let detail = `Request failed (${res.status})`
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') detail = body.detail
    else if (Array.isArray(body.detail)) detail = JSON.stringify(body.detail)
  } catch {
    // ignore parsing errors, keep default message
  }
  throw new Error(detail)
}

export async function health(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) await parseError(res)
  return res.json() as Promise<HealthInfo>
}

export async function createResearchTask(query: string, files: File[]): Promise<NewTaskResponse> {
  const form = new FormData()
  form.append('query', query)
  for (const file of files) form.append('documents', file, file.name)
  const res = await fetch(`${API_BASE}/research`, { method: 'POST', body: form })
  if (!res.ok) await parseError(res)
  return res.json() as Promise<NewTaskResponse>
}

export async function listTasks(): Promise<ResearchTask[]> {
  const res = await fetch(`${API_BASE}/tasks`)
  if (!res.ok) await parseError(res)
  return res.json() as Promise<ResearchTask[]>
}

export async function getTask(taskId: string): Promise<ResearchTask> {
  const res = await fetch(`${API_BASE}/tasks/${encodeURIComponent(taskId)}`)
  if (!res.ok) await parseError(res)
  return res.json() as Promise<ResearchTask>
}

export async function deleteTask(taskId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/tasks/${encodeURIComponent(taskId)}`, { method: 'DELETE' })
  if (!res.ok) await parseError(res)
}

export function reportUrl(taskId: string): string {
  return `${API_BASE}/tasks/${encodeURIComponent(taskId)}/report`
}

export type SSEHandler = {
  onEvent: (ev: { seq: number; agent: string; stage: string; message: string; detail?: unknown }) => void
  onDone: (status: string) => void
  onError: (message: string) => void
}

export function subscribeToTask(taskId: string, handler: SSEHandler): () => void {
  const es = new EventSource(`${API_BASE}/tasks/${encodeURIComponent(taskId)}/events`)

  const onMessage = (raw: MessageEvent) => {
    let data: Record<string, unknown>
    try {
      data = JSON.parse(raw.data as string)
    } catch {
      return
    }
    if (data.type === 'event') {
      handler.onEvent({
        seq: Number(data.seq ?? 0),
        agent: String(data.agent ?? ''),
        stage: String(data.stage ?? ''),
        message: String(data.message ?? ''),
        detail: data.detail,
      })
    } else if (data.type === 'done') {
      handler.onDone(String(data.status ?? 'done'))
      es.close()
    } else if (data.type === 'closed') {
      es.close()
    }
  }

  es.onerror = () => {
    handler.onError('Live stream disconnected')
    es.close()
  }

  es.addEventListener('message', onMessage)

  return () => {
    es.removeEventListener('message', onMessage)
    es.close()
  }
}