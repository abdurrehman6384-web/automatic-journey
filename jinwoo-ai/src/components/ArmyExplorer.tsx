import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { commanders } from '../data/army'
import type { Commander } from '../types/army'

interface ArmyExplorerProps {
  selectedCommander: Commander
  onSelectCommander: (commander: Commander) => void
}

const safetyLabel: Record<Commander['defaultSafety'], string> = {
  'read-only': 'Read-only',
  'approval-required': 'Approval required',
  sandboxed: 'Sandboxed',
  'no-direct-tools': 'Command only',
}

const statusLabel: Record<Commander['status'], string> = {
  ready: 'Standing by',
  working: 'Mission active',
  offline: 'Opt-in offline',
  guarded: 'Safety guarded',
}

export function ArmyExplorer({ selectedCommander, onSelectCommander }: ArmyExplorerProps) {
  const [expandedId, setExpandedId] = useState(selectedCommander.id)

  useEffect(() => {
    setExpandedId(selectedCommander.id)
  }, [selectedCommander.id])

  const select = (commander: Commander) => {
    setExpandedId(commander.id)
    onSelectCommander(commander)
  }

  return (
    <section className="army-explorer" aria-labelledby="army-explorer-title">
      <header className="explorer-hero panel">
        <div>
          <p className="eyebrow">VISIBLE HIERARCHY · NO HIDDEN SPAWN</p>
          <h1 id="army-explorer-title">Army explorer</h1>
          <p>Fifteen commanders coordinate 45 specialist divisions. Each division represents ten logical agents, but Jinwoo proposes no more than the Planner, Executor and Verifier roles a mission needs.</p>
        </div>
        <div className="explorer-hero__stats" aria-label="Army hierarchy totals">
          <span><b>15</b> commanders</span>
          <span><b>45</b> divisions</span>
          <span><b>450</b> logical agents</span>
        </div>
      </header>

      <div className="army-explorer__directory">
        {commanders.map((commander) => {
          const expanded = expandedId === commander.id
          const style = {
            '--commander-color': commander.color,
            '--commander-glow': commander.glow,
          } as CSSProperties
          return (
            <article className={`explorer-commander ${expanded ? 'explorer-commander--expanded' : ''}`} style={style} key={commander.id}>
              <button
                className="explorer-commander__toggle"
                type="button"
                aria-expanded={expanded}
                aria-controls={`${commander.id}-divisions`}
                onClick={() => select(commander)}
              >
                <span className="explorer-commander__number">{String(commander.number).padStart(2, '0')}</span>
                <span className="explorer-commander__icon" aria-hidden="true">{commander.icon}</span>
                <span className="explorer-commander__identity">
                  <small>{commander.department}</small>
                  <strong>{commander.name}</strong>
                  <em>{commander.title}</em>
                </span>
                <span className={`explorer-commander__status explorer-commander__status--${commander.status}`}>{statusLabel[commander.status]}</span>
                <span className="explorer-commander__chevron" aria-hidden="true">{expanded ? '−' : '+'}</span>
              </button>
              {expanded && (
                <div id={`${commander.id}-divisions`} className="explorer-commander__body">
                  <p>{commander.description}</p>
                  <div className="explorer-commander__meta">
                    <span>{safetyLabel[commander.defaultSafety]}</span>
                    <span>3 divisions</span>
                    <span>30 logical agents</span>
                  </div>
                  <ol className="division-grid">
                    {commander.subDepartments.map((division, index) => (
                      <li key={division.id}>
                        <span>Division {index + 1} · 10 agents</span>
                        <strong>{division.name}</strong>
                        <p>{division.focus}</p>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}
