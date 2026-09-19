import { useRef, useState } from 'react'
import { createResearchTask } from '../api'

interface NewTaskFormProps {
  onTaskCreated: (taskId: string) => void
  onError: (message: string) => void
}

export function NewTaskForm({ onTaskCreated, onError }: NewTaskFormProps) {
  const [query, setQuery] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [submitting, setSubmitting] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const canSubmit = query.trim().length > 0 && !submitting

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    try {
      const res = await createResearchTask(query.trim(), files)
      setQuery('')
      setFiles([])
      if (fileRef.current) fileRef.current.value = ''
      onTaskCreated(res.id)
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to create research task')
    } finally {
      setSubmitting(false)
    }
  }

  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(Array.from(e.target.files ?? []))
  }

  return (
    <form className="new-task" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor="research-query">
        Research question
      </label>
      <textarea
        id="research-query"
        rows={3}
        placeholder="e.g. What is the state of ocean plastic pollution in 2025?"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={submitting}
      />
      <div className="form-row">
        <label className="file-picker">
          <input ref={fileRef} type="file" multiple onChange={handleFiles} disabled={submitting} />
          <span className="file-btn">Upload documents</span>
          {files.length > 0 && <span className="file-count">{files.length} selected</span>}
        </label>
        <button className="submit-btn" type="submit" disabled={!canSubmit}>
          {submitting ? 'Starting…' : 'Start research'}
        </button>
      </div>
    </form>
  )
}