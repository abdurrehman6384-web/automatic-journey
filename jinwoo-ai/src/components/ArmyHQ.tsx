import { commanders } from '../data/army'
import type { ArmyStats, Commander } from '../types/army'
import { CommanderCard } from './CommanderCard'
import { ShadowGate } from './ShadowGate'

interface ArmyHQProps {
  stats: ArmyStats
  selectedCommander: Commander
  onSelectCommander: (commander: Commander) => void
}

export function ArmyHQ({ stats, selectedCommander, onSelectCommander }: ArmyHQProps) {
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
            <span>3 teams / commander</span>
            <span>10 agents / team</span>
            <span>Local memory active</span>
          </div>
        </div>
        <ShadowGate active />
        <div className="hero-readout">
          <span>MONARCH STATUS</span>
          <strong>READY</strong>
          <small>Bellion is synchronising the command flow.</small>
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
