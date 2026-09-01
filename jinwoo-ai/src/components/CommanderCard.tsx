import type { CSSProperties } from 'react'
import type { Commander } from '../types/army'

interface CommanderCardProps {
  commander: Commander
  selected: boolean
  onSelect: (commander: Commander) => void
}

const safetyLabels = {
  'read-only': 'Read-only',
  'approval-required': 'Approval required',
  sandboxed: 'Sandboxed',
  'no-direct-tools': 'Command only',
}

export function CommanderCard({ commander, selected, onSelect }: CommanderCardProps) {
  return (
    <button
      className={`commander-card commander-card--${commander.status} ${selected ? 'commander-card--selected' : ''}`}
      style={{ '--commander-color': commander.color, '--commander-glow': commander.glow } as CSSProperties}
      type="button"
      onClick={() => onSelect(commander)}
      aria-pressed={selected}
    >
      <span className="commander-card__number">{String(commander.number).padStart(2, '0')}</span>
      <span className="commander-card__icon">{commander.icon}</span>
      <span className="commander-card__copy">
        <span className="commander-card__department">{commander.department}</span>
        <strong>{commander.name}</strong>
        <span className="commander-card__title">{commander.title}</span>
      </span>
      <span className="commander-card__footer">
        <span className={`status-dot status-dot--${commander.status}`} />
        <span>{commander.status === 'working' ? 'Mission active' : commander.status === 'offline' ? 'Opt-in offline' : 'Standing by'}</span>
      </span>
      <span className="commander-card__safety">{safetyLabels[commander.defaultSafety]}</span>
    </button>
  )
}
