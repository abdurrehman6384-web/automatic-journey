import type { ProviderStatus } from '../types/army'

interface ProviderPanelProps {
  providers: ProviderStatus[]
}

export function ProviderPanel({ providers }: ProviderPanelProps) {
  return (
    <section className="panel provider-panel" aria-labelledby="providers-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">MODEL ROUTER</p>
          <h2 id="providers-title">Provider status</h2>
        </div>
        <span className="subtle-badge">LOCAL FIRST</span>
      </div>
      <div className="provider-list">
        {providers.map((provider) => (
          <div className="provider-row" key={provider.id}>
            <span className={`provider-mark provider-mark--${provider.mode}`}>{provider.mode === 'local' ? '⌁' : provider.mode === 'memory' ? '◌' : '✦'}</span>
            <div>
              <strong>{provider.label}</strong>
              <p>{provider.detail}</p>
            </div>
            <span className={`provider-state provider-state--${provider.state}`}>{provider.state.replace('-', ' ')}</span>
          </div>
        ))}
      </div>
      <p className="panel-hint">Cloud keys stay outside the browser bundle. Configure them locally when you are ready.</p>
    </section>
  )
}
