import { useState } from 'react'
import type { SecurityScanPlan, WorkspaceStatus } from '../types/army'

interface SecurityScanPanelProps {
  workspace: WorkspaceStatus
  plan: SecurityScanPlan | null
  busy: boolean
  onPlan: (scannerId: SecurityScanPlan['scannerId'], confirmAuthorized: boolean) => Promise<boolean>
}

const scannerOptions: Array<{ id: SecurityScanPlan['scannerId']; label: string; note: string }> = [
  { id: 'gitleaks', label: 'Gitleaks', note: 'MIT · no scanner process is installed or started' },
  { id: 'trufflehog', label: 'TruffleHog', note: 'AGPL-3.0 · licence review is required before any future runtime use' },
]

export function SecurityScanPanel({ workspace, plan, busy, onPlan }: SecurityScanPanelProps) {
  const [scannerId, setScannerId] = useState<SecurityScanPlan['scannerId']>('gitleaks')
  const [confirmAuthorized, setConfirmAuthorized] = useState(false)
  const [formError, setFormError] = useState('')
  const selected = scannerOptions.find((option) => option.id === scannerId)

  const submit = async () => {
    if (!workspace.configured) {
      setFormError('Select a workspace above before preparing a bounded security review.')
      return
    }
    if (!confirmAuthorized) {
      setFormError('Confirm that you are authorised to review the selected workspace.')
      return
    }
    setFormError('')
    await onPlan(scannerId, confirmAuthorized)
  }

  return (
    <section className="panel security-scan" aria-labelledby="security-scan-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">GREED // NO-SCAN SECURITY GATE</p>
          <h2 id="security-scan-title">Prepare a secret-review boundary</h2>
        </div>
        <span className="subtle-badge">NO FILE READ</span>
      </div>
      <p className="security-scan__copy">This creates only a later-review preflight. It does not inspect files, Git history, credentials or scanner output; it does not start Gitleaks or TruffleHog.</p>
      <div className="security-scan__form">
        <label htmlFor="security-scanner">Controlled scanner</label>
        <select id="security-scanner" value={scannerId} onChange={(event) => setScannerId(event.target.value as SecurityScanPlan['scannerId'])} disabled={busy}>
          {scannerOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </select>
        <small>{selected?.note}</small>
        <label className="security-scan__confirm"><input type="checkbox" checked={confirmAuthorized} onChange={(event) => setConfirmAuthorized(event.target.checked)} disabled={busy} /><span>I am authorised to review the selected workspace. I understand this creates no scan and no findings.</span></label>
        {formError && <p className="form-error" role="alert">{formError}</p>}
        <button className="button" type="button" onClick={() => { void submit() }} disabled={busy}>{busy ? 'Validating…' : 'Create no-scan plan'}</button>
      </div>
      {plan && (
        <div className={`security-scan__result ${plan.licenseReviewRequired ? 'security-scan__result--licence' : ''}`} aria-live="polite">
          <p className="eyebrow">LATEST NO-SCAN PLAN · {plan.scannerLabel}</p>
          <div className="security-scan__flags"><span>{plan.externalScanStarted ? 'Scan started' : 'No scan started'}</span><span>{plan.requiresApprovalForScan ? 'Future approval required' : 'No future approval'}</span>{plan.licenseReviewRequired && <span>Licence review required</span>}</div>
          <ul>{plan.safeguards.map((safeguard) => <li key={safeguard}>{safeguard}</li>)}</ul>
        </div>
      )}
    </section>
  )
}
