import type { ControlReview } from '../types/army'

interface ControlReviewPanelProps {
  review: ControlReview | null
  busy: boolean
  onRun: () => Promise<boolean>
}

export function ControlReviewPanel({ review, busy, onRun }: ControlReviewPanelProps) {
  const passedCount = review?.checks.filter((check) => check.passed).length ?? 0

  return (
    <section className="panel control-review" aria-labelledby="control-review-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">JINWOO // FINAL CONTROL LANE</p>
          <h2 id="control-review-title">Control &amp; audit review</h2>
        </div>
        <span className="subtle-badge">LOCAL ONLY</span>
      </div>
      <p className="control-review__copy">Run a zero-side-effect check of Army capacity, native command ownership, external-runtime locks, licence gates, workspace containment and local audit availability. It cannot enable an adapter, read project files or invoke a tool.</p>
      <button className="button" type="button" onClick={() => { void onRun() }} disabled={busy}>{busy ? 'Reviewing…' : 'Run local control review'}</button>
      {review && (
        <div className={`control-review__result ${review.allPassed ? 'control-review__result--pass' : 'control-review__result--attention'}`} aria-live="polite">
          <div className="control-review__summary">
            <div>
              <p className="eyebrow">LATEST REVIEW</p>
              <strong>{review.summary}</strong>
            </div>
            <span>{passedCount}/{review.checks.length} passed</span>
          </div>
          <div className="control-review__flags"><span>{review.externalRuntimeInvoked ? 'External runtime invoked' : 'No external runtime invoked'}</span><span>{new Date(review.reviewedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>
          <ul className="control-review__checks">
            {review.checks.map((check) => (
              <li key={check.id} className={check.passed ? 'control-check--pass' : 'control-check--attention'}>
                <span aria-hidden="true">{check.passed ? '✓' : '!'}</span>
                <div><b>{check.label}</b><p>{check.detail}</p></div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
