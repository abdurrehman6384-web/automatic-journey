import type { Mission } from '../types/army'

type OrbState = 'ready' | 'working' | 'guarded'

interface CommandOrbProps {
  mission?: Mission | null
  state?: OrbState
  compact?: boolean
}

const statusLabel: Record<OrbState, string> = {
  ready: 'Command link ready',
  working: 'Mission flow active',
  guarded: 'Safety gate engaged',
}

export function CommandOrb({ mission, state = 'ready', compact = false }: CommandOrbProps) {
  const resolvedState: OrbState = mission?.status === 'running'
    ? 'working'
    : mission?.requiresApproval
      ? 'guarded'
      : state

  return (
    <div className={`command-orb command-orb--${resolvedState} ${compact ? 'command-orb--compact' : ''}`} role="img" aria-label={statusLabel[resolvedState]}>
      <span className="command-orb__halo command-orb__halo--one" />
      <span className="command-orb__halo command-orb__halo--two" />
      <span className="command-orb__halo command-orb__halo--three" />
      <span className="command-orb__arc command-orb__arc--one" />
      <span className="command-orb__arc command-orb__arc--two" />
      <span className="command-orb__spark command-orb__spark--one" />
      <span className="command-orb__spark command-orb__spark--two" />
      <span className="command-orb__spark command-orb__spark--three" />
      <span className="command-orb__core">
        <b>J</b>
        <small>{resolvedState === 'working' ? 'FLOW' : resolvedState === 'guarded' ? 'GUARD' : 'READY'}</small>
      </span>
      {!compact && <span className="command-orb__caption">{statusLabel[resolvedState]}</span>}
    </div>
  )
}
