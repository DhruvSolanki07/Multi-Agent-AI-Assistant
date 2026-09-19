import { agentLabel } from '../format'
import type { AgentEvent } from '../types'

export function AgentWall({ events }: { events: AgentEvent[] }) {
  return (
    <section className="wall">
      <h2>Agent activity</h2>
      {events.length === 0 ? (
        <p className="empty-note">No activity yet — the pipeline is starting up.</p>
      ) : (
        <ul className="event-list">
          {events.map((ev) => (
            <li key={ev.seq} className={`event event-${ev.stage}`}>
              <div className="event-dot" aria-hidden="true" />
              <div className="event-body">
                <div className="event-head">
                  <span className="event-agent">{agentLabel(ev.agent)}</span>
                  <span className="event-stage">{ev.stage}</span>
                </div>
                <p>{ev.message}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}