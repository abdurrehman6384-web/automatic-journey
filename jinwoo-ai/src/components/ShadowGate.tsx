interface ShadowGateProps {
  active?: boolean
}

export function ShadowGate({ active = true }: ShadowGateProps) {
  return (
    <div className={`shadow-gate ${active ? 'shadow-gate--active' : ''}`} aria-label="Animated shadow gate">
      <div className="gate-aura gate-aura--outer" />
      <div className="gate-aura gate-aura--middle" />
      <div className="gate-aura gate-aura--inner" />
      <div className="gate-core">
        <span className="gate-crown">♛</span>
        <span className="gate-label">SHADOW<br />MONARCH</span>
      </div>
      <span className="gate-particle particle-one" />
      <span className="gate-particle particle-two" />
      <span className="gate-particle particle-three" />
    </div>
  )
}
