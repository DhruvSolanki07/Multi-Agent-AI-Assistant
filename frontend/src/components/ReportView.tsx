import ReactMarkdown from 'react-markdown'
import { reportUrl } from '../api'
import type { ResearchTask } from '../types'

export function ReportView({ task }: { task: ResearchTask }) {
  const body = task.report_markdown || task.report

  return (
    <section className="report">
      <div className="report-head">
        <h2>Research report</h2>
        <a className="download-btn" href={reportUrl(task.id)} download={`${task.id}.md`}>
          Download .md
        </a>
      </div>
      {body ? (
        <div className="markdown">
          <ReactMarkdown>{body}</ReactMarkdown>
        </div>
      ) : (
        <p className="empty-note">The report has not been written yet.</p>
      )}
    </section>
  )
}