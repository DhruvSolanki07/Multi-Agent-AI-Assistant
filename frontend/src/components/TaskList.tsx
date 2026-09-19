import { deleteTask, reportUrl } from '../api'
import { timeAgo } from '../format'
import type { ResearchTask } from '../types'
import { StatusBadge } from './StatusBadge'

interface TaskListProps {
  tasks: ResearchTask[]
  selectedId: string | null
  onSelect: (taskId: string) => void
  onDeleted: (taskId: string) => void
  onError: (message: string) => void
}

export function TaskList({ tasks, selectedId, onSelect, onDeleted, onError }: TaskListProps) {
  if (tasks.length === 0) {
    return <p className="empty-note">No research tasks yet. Create your first one above.</p>
  }

  const handleDelete = async (e: React.MouseEvent, task: ResearchTask) => {
    e.stopPropagation()
    try {
      await deleteTask(task.id)
      onDeleted(task.id)
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to delete task')
    }
  }

  return (
    <ul className="task-list">
      {tasks.map((t) => (
        <li key={t.id}>
          <button
            type="button"
            className={`task-card${t.id === selectedId ? ' selected' : ''}`}
            onClick={() => onSelect(t.id)}
          >
            <div className="task-card-head">
              <StatusBadge status={t.status} />
              <time title={t.created_at}>{timeAgo(t.created_at)}</time>
            </div>
            <div className="task-query">{t.query}</div>
            <div className="task-meta">
              <span>{t.sources.length} sources</span>
              <span>·</span>
              <span>{t.findings.length} findings</span>
            </div>
          </button>
          <div className="task-actions">
            {t.status === 'done' && (
              <a href={reportUrl(t.id)} download={`${t.id}.md`}>
                Report
              </a>
            )}
            <button type="button" className="link-danger" onClick={(e) => handleDelete(e, t)}>
              Delete
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}