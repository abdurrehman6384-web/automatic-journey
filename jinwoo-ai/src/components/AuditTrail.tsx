import type { AuditEvent } from '../types/army'

interface AuditTrailProps {
  events: AuditEvent[]
  missionId?: string
}

const eventLabel = (eventType: string) => eventType.replace('.', ' · ').replaceAll('-', ' ')

export function AuditTrail({ events, missionId }: AuditTrailProps) {
  const visibleEvents = events.filter((event) => !missionId || event.missionId === missionId).slice(0, 8)

  return (
    <section className="panel audit-panel" aria-labelledby="audit-title">
      <div className="panel-heading">
        <div><p className="eyebrow">LOCAL AUDIT TRAIL</p><h2 id="audit-title">Visible decisions</h2></div>
        <span className="subtle-badge">REDACTED</span>
      </div>
      {visibleEvents.length ? (
        <ol className="audit-list">
          {visibleEvents.map((event) => (
            <li key={event.id}>
              <span className="audit-event-type">{eventLabel(event.eventType)}</span>
              <strong>{event.detail}</strong>
              <small>{event.actor} · {new Date(event.createdAt).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</small>
            </li>
          ))}
        </ol>
      ) : (
        <p className="audit-empty">Mission routing, approvals and completion decisions will appear here. Raw prompts and provider secrets are not logged.</p>
      )}
    </section>
  )
}
