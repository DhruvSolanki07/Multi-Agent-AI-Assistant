import { useCallback, useEffect, useRef, useState } from 'react'
import { health, listTasks } from './api'
import { NewTaskForm } from './components/NewTaskForm'
import { TaskDetail } from './components/TaskDetail'
import { TaskList } from './components/TaskList'
import type { HealthInfo, ResearchTask } from './types'
import './App.css'

export default function App() {
  const [tasks, setTasks] = useState<ResearchTask[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [healthInfo, setHealthInfo] = useState<HealthInfo | null>(null)
  const [backendUp, setBackendUp] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false
    void health()
      .then((h) => {
        if (cancelled) return
        setHealthInfo(h)
        setBackendUp(true)
      })
      .catch(() => {
        if (!cancelled) setBackendUp(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const refresh = useCallback(async () => {
    try {
      setTasks(await listTasks())
    } catch (err) {
      setBackendUp(false)
      setError(err instanceof Error ? err.message : 'Backend unreachable')
    }
  }, [])

  useEffect(() => {
    void refresh()
    timerRef.current = window.setInterval(() => void refresh(), 4000)
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current)
    }
  }, [refresh])

  const handleTaskCreated = (taskId: string) => {
    setSelectedId(taskId)
    void refresh()
  }

  const handleDeleted = (taskId: string) => {
    if (selectedId === taskId) setSelectedId(null)
    void refresh()
  }

  const handleDone = () => {
    void refresh()
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <h1>Multi-Agent Research Assistant</h1>
            <p className="subtitle">Planner · Searcher · Documenter · Summarizer · Writer · Critic</p>
          </div>
        </div>
        <div className="health">
          {healthInfo ? (
            <>
              <span className={`health-pill ${healthInfo.llm_configured ? 'ok' : 'fallback'}`}>
                LLM: {healthInfo.llm_configured ? 'connected' : 'fallback'}
              </span>
              <span className={`health-pill ${healthInfo.search_configured ? 'ok' : 'fallback'}`}>
                Search: {healthInfo.search_configured ? 'connected' : 'fallback'}
              </span>
            </>
          ) : (
            <span className={`health-pill ${backendUp === false ? 'fallback' : 'ok'}`}>
              {backendUp === false ? 'backend offline' : 'checking…'}
            </span>
          )}
        </div>
      </header>

      {backendUp === false && (
        <div className="error-banner">
          Cannot reach the backend API on port 8000. Start it with
          <code> uvicorn app.main:app --port 8000 </code> from <code>backend/</code>.
        </div>
      )}
      {error && backendUp !== false && (
        <div className="error-banner">
          {error}
          <button type="button" className="error-dismiss" onClick={() => setError(null)}>
            dismiss
          </button>
        </div>
      )}

      <div className="layout">
        <aside className="sidebar">
          <NewTaskForm onTaskCreated={handleTaskCreated} onError={setError} />
          <h2 className="sidebar-title">Tasks</h2>
          <TaskList
            tasks={tasks}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onDeleted={handleDeleted}
            onError={setError}
          />
        </aside>

        <main className="main">
          {selectedId ? (
            <TaskDetail key={selectedId} taskId={selectedId} onDone={handleDone} />
          ) : (
            <section className="detail placeholder">
              <p className="empty-note">
                Select a task from the list, or start a new research question to watch the agents
                work in real time.
              </p>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}