import type { TaskStatus } from '../types'

const LABELS: Record<TaskStatus, string> = {
  queued: 'Queued',
  running: 'Running',
  done: 'Done',
  failed: 'Failed',
}

export function StatusBadge({ status }: { status: TaskStatus }) {
  return <span className={`badge badge-${status}`}>{LABELS[status] ?? status}</span>
}