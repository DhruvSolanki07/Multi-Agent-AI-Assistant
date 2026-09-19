const AGENT_LABELS: Record<string, string> = {
  planner: 'Planner',
  searcher: 'Searcher',
  documenter: 'Documenter',
  summarizer: 'Summarizer',
  writer: 'Writer',
  critic: 'Critic',
}

export function agentLabel(agent: string): string {
  return AGENT_LABELS[agent] ?? agent
}

export function timeAgo(iso: string): string {
  if (!iso) return ''
  const then = new Date(iso).getTime()
  const diff = Math.max(0, Date.now() - then)
  const s = Math.floor(diff / 1000)
  if (s < 5) return 'just now'
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  return `${d}d ago`
}

export function formatTime(iso: string): string {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}