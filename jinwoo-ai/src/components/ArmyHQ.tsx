import { commanders } from '../data/army'
import type { ArmyStats, Commander, Mission } from '../types/army'
import { CommandOrb } from './CommandOrb'
import { CommanderCard } from './CommanderCard'
import { ShadowGate } from './ShadowGate'

interface ArmyHQProps {
  stats: ArmyStats
  selectedCommander: Commander
  mission?: Mission | null
  onSelectCommander: (commander: Commander) => void
  onOpenMission: () => void
  onOpenArmy: () => void
  onOpenInteraction: () => void
}

export function ArmyHQ({ stats, selectedCommander, mission, onSelectCommander, onOpenMission, onOpenArmy, onOpenInteraction }: ArmyHQProps) {
  const missionState = mission?.status === 'running'
    ? 'Mission flow active'
    : mission?.requiresApproval
      ? 'Approval checkpoint'
      : 'Ready for a safe plan'

  return (
    <section className="army-hq" aria-labelledby="army-hq-title">
      <div className="army-hq__hero panel">
        <div className="hero-copy">
          <p className="eyebrow"><span className="signal-dot" /> LOCAL-FIRST COMMAND NETWORK</p>
          <h1 id="army-hq-title">Jinwoo <em>AI</em></h1>
          <p className="hero-description">
            A visible, approval-first command center. Deploy only the workers a mission needs — never a hidden army.
          </p>
          <div className="hero-pills">
            <span>15 command roles</span>
            <span>45 visible divisions</span>
            <span>450 logical agents</span>
            <span>Consent-based memory</span>
          </div>
          <div className="hero-actions">
            <button className="button" type="button" onClick={onOpenMission}>Open mission desk <span>↗</span></button>
            <button className="button button--ghost" type="button" onClick={onOpenArmy}>Explore army</button>
          </div>
        </div>
        <div className="hero-visuals" aria-label="Jinwoo command visuals">
          <ShadowGate active />
          <CommandOrb mission={mission} />
        </div>
        <div className="hero-readout">
          <span>MONARCH STATUS</span>
          <strong>{mission?.status === 'running' ? 'ACTIVE' : mission?.requiresApproval ? 'GUARDED' : 'READY'}</strong>
          <small>{missionState}</small>
          <button className="hero-readout__link" type="button" onClick={onOpenInteraction}>Interaction safety lab <span>↗</span></button>
        </div>
      </div>

      <div className="stat-grid" aria-label="Army capacity summary">
        <article className="stat-card"><span>Departments</span><strong>{stats.departments}</strong><small>Visible command roles</small></article>
        <article className="stat-card"><span>Sub-departments</span><strong>{stats.subDepartments}</strong><small>Logical team templates</small></article>
        <article className="stat-card"><span>Agent roles</span><strong>{stats.logicalAgents.toLocaleString()}</strong><small>Spawned only when needed</small></article>
        <article className="stat-card"><span>Active workers</span><strong>{stats.activeWorkers}</strong><small>Planner · Executor · Verifier</small></article>
      </div>

      <div className="section-heading">
        <div>
          <p className="eyebrow">COMMANDER DIRECTORY</p>
          <h2>Choose a department</h2>
        </div>
        <span className="section-note">Logical capacity: {stats.workerSlots.toLocaleString()} worker slots</span>
      </div>

      <div className="commander-grid">
        {commanders.map((commander) => (
          <CommanderCard
            commander={commander}
            key={commander.id}
            selected={commander.id === selectedCommander.id}
            onSelect={onSelectCommander}
          />
        ))}
      </div>
    </section>
  )
}
