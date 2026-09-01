import type { Commander, Mission } from '../types/army'

interface MissionPanelProps {
  mission: Mission | null
  selectedCommander: Commander
  onApprove: () => void
  onCancel: () => void
}

export function MissionPanel({ mission, selectedCommander, onApprove, onCancel }: MissionPanelProps) {
  if (!mission) {
    return (
      <section className="panel mission-panel mission-panel--empty">
        <p className="eyebrow">MISSION CONSOLE</p>
        <h2>{selectedCommander.name} is standing by</h2>
        <p>{selectedCommander.description}</p>
        <div className="team-preview">
          {selectedCommander.subDepartments.slice(0, 3).map((team) => <span key={team.id}>{team.name}</span>)}
        </div>
      </section>
    )
  }

  return (
    <section className="panel mission-panel" aria-live="polite">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">MISSION {mission.id.slice(-6).toUpperCase()}</p>
          <h2>{mission.commander} has the order</h2>
        </div>
        <span className={`risk-badge risk-badge--${mission.risk}`}>{mission.risk} risk</span>
      </div>
      <p className="mission-prompt">“{mission.prompt}”</p>
      <ol className="mission-steps">
        {mission.steps.map((step, index) => <li key={step}><span>{index + 1}</span>{step}</li>)}
      </ol>
      <div className="worker-row">
        {mission.workers.map((worker) => <span key={worker.id}><b>{worker.name}</b>{worker.responsibility}</span>)}
      </div>
      {mission.requiresApproval && mission.status === 'awaiting_approval' ? (
        <div className="approval-callout">
          <div><strong>Approval required</strong><p>This request may change files, run a command, send data, or control the desktop.</p></div>
          <div className="button-row"><button className="button button--ghost" type="button" onClick={onCancel}>Reject</button><button className="button" type="button" onClick={onApprove}>Approve mission</button></div>
        </div>
      ) : (
        <div className="mission-ready"><span className="status-dot status-dot--ready" /><span>{mission.status === 'complete' ? mission.result ?? 'Mission complete.' : 'Safe plan prepared. Connect a provider to execute this mission.'}</span></div>
      )}
    </section>
  )
}
