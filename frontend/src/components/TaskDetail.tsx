import { useEffect, useRef, useState } from 'react'
import { getTask, subscribeToTask } from '../api'
import type { AgentEvent, ResearchTask } from '../types'
import { AgentWall } from './AgentWall'
import { ReportView } from './ReportView'
import { StatusBadge } from './StatusBadge'

interface TaskDetailProps {
  taskId: string
  onDone: () => void
}

const LIVE_STATES = ['queued', 'running']

export function TaskDetail({ taskId, onDone }: TaskDetailProps) {
  const [task, setTask] = useState<ResearchTask | null>(null)
  const [error, setError] = useState<string | null>(null)
  const lastSeqRef = useRef(0)

  useEffect(() => {
    lastSeqRef.current = 0
    let cancelled = false

    getTask(taskId)
      .then((t) => {
        if (cancelled) return
        setTask(t)
        lastSeqRef.current = Math.max(...t.agent_events.map((e) => e.seq), 0)
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load task')
      })

    return () => {
      cancelled = true
    }
  }, [taskId])

  const hasTask = task !== null
  const live = hasTask ? LIVE_STATES.includes(task.status) : false

  useEffect(() => {
    if (!live) return

    const unsubscribe = subscribeToTask(taskId, {
      onEvent: (ev) => {
        if ((ev.seq ?? 0) <= lastSeqRef.current) return
        lastSeqRef.current = ev.seq
        setTask((prev) => {
          if (!prev) return prev
          const event: AgentEvent = {
            seq: ev.seq,
            agent: ev.agent as AgentEvent['agent'],
            stage: ev.stage as AgentEvent['stage'],
            message: ev.message,
            detail: ev.detail !== undefined ? (ev.detail as Record<string, unknown>) : null,
          }
          return { ...prev, status: 'running', agent_events: [...prev.agent_events, event] }
        })
      },
      onDone: (status) => {
        setTask((prev) => (prev ? { ...prev, status: status as ResearchTask['status'] } : prev))
        onDone()
      },
      onError: (message) => setError(message),
    })

    return unsubscribe
  }, [live, taskId, hasTask, onDone])

  if (error && !task) {
    return (
      <section className="detail">
        <div className="error-banner">{error}</div>
        <p className="empty-note">Could not load this research task.</p>
      </section>
    )
  }

  if (!task) {
    return (
      <section className="detail">
        <div className="spinner" aria-label="Loading" />
      </section>
    )
  }

  return (
    <section className="detail">
      <div className="detail-head">
        <div>
          <div className="detail-status">
            <StatusBadge status={task.status} />
            {task.status === 'running' && <span className="live-dot">live</span>}
          </div>
          <h1>{task.query}</h1>
        </div>
        <time title={task.created_at}>{new Date(task.created_at).toLocaleString()}</time>
      </div>

      {task.error && <div className="error-banner">{task.error}</div>}

      <div className="detail-grid">
        <AgentWall events={task.agent_events} />

        <div className="detail-results">
          {task.plan.length > 0 && (
            <section className="card">
              <h2>Plan</h2>
              <ol className="chip-list">
                {task.plan.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ol>
            </section>
          )}

          {task.sources.length > 0 && (
            <section className="card">
              <h2>Sources ({task.sources.length})</h2>
              <ul className="source-list">
                {task.sources.map((s, i) => (
                  <li key={i}>
                    {s.url ? (
                      <a href={s.url} target="_blank" rel="noreferrer">
                        {s.title}
                      </a>
                    ) : (
                      <span>{s.title}</span>
                    )}
                    <span className="source-type">{s.source_type}</span>
                    {s.snippet && <p className="snippet">{s.snippet}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {task.findings.length > 0 && (
            <section className="card">
              <h2>Findings ({task.findings.length})</h2>
              <ul className="finding-list">
                {task.findings.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </section>
          )}

          {task.gaps.length > 0 && (
            <section className="card">
              <h2>Gaps &amp; follow-ups</h2>
              <ul className="gap-list">
                {task.gaps.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </section>
          )}

          {task.status === 'done' && <ReportView task={task} />}
        </div>
      </div>
    </section>
  )
}