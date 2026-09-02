import type { FrameworkStatus } from '../types/army'
import { batchTwelveUpgradeReview } from '../data/upgradeReview'

interface UpgradeReviewPanelProps {
  frameworks: FrameworkStatus[]
}

const statusLabel = (framework: FrameworkStatus | undefined) => {
  if (!framework) return 'record pending'
  if (framework.implementationStatus === 'reference-only') return 'reference only'
  return framework.implementationStatus.replaceAll('-', ' ')
}

const shortRevision = (revision: string) => `${revision.slice(0, 12)}…`

export function UpgradeReviewPanel({ frameworks }: UpgradeReviewPanelProps) {
  const frameworkById = new Map(frameworks.map((framework) => [framework.id, framework]))

  return (
    <section className="upgrade-intake panel" aria-labelledby="upgrade-intake-title">
      <header className="upgrade-intake__heading">
        <div>
          <p className="eyebrow">BATCH 12 · BOUNDED NEXT-TEN DISCOVERY PASS</p>
          <h2 id="upgrade-intake-title">Upgrade review queue</h2>
          <p>Ten candidate lanes are visible for deliberate review. This completed pass is a finite metadata queue—not a background discovery worker, automatic upgrade mechanism or permission to install anything.</p>
        </div>
        <div className="upgrade-intake__locks" aria-label="Upgrade review safety locks">
          <span>Metadata only</span>
          <span>No runtime installed</span>
          <span>No unattended loop</span>
        </div>
      </header>

      <p className="upgrade-intake__notice">Only public repository metadata and a default-branch revision were recorded for these candidates. No repository tree, source file, archive, installer, package, provider, model, scan, telemetry route or external runtime was retrieved, copied, installed or executed.</p>

      <div className="upgrade-intake__grid">
        {batchTwelveUpgradeReview.map((entry) => {
          const framework = frameworkById.get(entry.frameworkId)
          const revision = framework?.reviewCommit ?? entry.revision
          return (
            <article className="upgrade-source-card" key={entry.frameworkId}>
              <div className="upgrade-source-card__topline">
                <span className="upgrade-source-card__sequence">Queue {String(entry.sequence).padStart(2, '0')}</span>
                <span className={`framework-state framework-state--${framework?.implementationStatus ?? 'queued'}`}>{statusLabel(framework)}</span>
              </div>
              <h3>{entry.repository}</h3>
              <p className="upgrade-source-card__target"><b>Future upgrade target</b>{entry.upgradeTarget}</p>
              <div className="upgrade-source-card__categories" aria-label={`${entry.repository} review categories`}>
                {entry.categories.map((category) => <span key={category}>{category}</span>)}
              </div>
              <dl className="upgrade-source-card__evidence">
                <div>
                  <dt>Observed revision</dt>
                  <dd title={revision}>{shortRevision(revision)}</dd>
                </div>
                <div>
                  <dt>Licence signal</dt>
                  <dd>{entry.licenceSignal}</dd>
                </div>
              </dl>
              <p className="upgrade-source-card__note">{entry.note}</p>
              <div className="upgrade-source-card__footer">
                <a href={entry.sourceUrl} target="_blank" rel="noreferrer">Review metadata source <span aria-hidden="true">↗</span></a>
                <span>{framework?.ownerCommander ?? 'Owner pending'}</span>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
