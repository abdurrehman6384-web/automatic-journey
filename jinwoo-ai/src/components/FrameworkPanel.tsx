import type { FrameworkStatus } from '../types/army'

interface FrameworkPanelProps {
  frameworks: FrameworkStatus[]
}

const runtimeIcon = (runtime: FrameworkStatus['runtime']) => {
  if (runtime === 'builtin') return '♛'
  if (runtime === 'typescript-mcp') return '⌘'
  return '◈'
}

export function FrameworkPanel({ frameworks }: FrameworkPanelProps) {
  return (
    <section className="panel framework-panel" aria-labelledby="frameworks-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ORCHESTRATION ADAPTERS</p>
          <h2 id="frameworks-title">Framework boundaries</h2>
        </div>
        <span className="subtle-badge">CONTROLLED</span>
      </div>
      <div className="framework-list">
        {frameworks.map((framework) => (
          <div className="framework-row" key={framework.id}>
            <span className={`framework-mark framework-mark--${framework.runtime}`}>{runtimeIcon(framework.runtime)}</span>
            <div>
              <strong>{framework.label}</strong>
              <p>{framework.detail}</p>
            </div>
            <span className={`framework-state framework-state--${framework.state}`}>
              {framework.executionEnabled ? 'active' : framework.state.replace('-', ' ')}
            </span>
          </div>
        ))}
      </div>
      <p className="panel-hint">Optional frameworks cannot run missions or bypass Jinwoo’s approval, privacy, workspace and audit controls.</p>
    </section>
  )
}
