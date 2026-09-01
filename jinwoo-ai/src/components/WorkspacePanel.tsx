import { useState } from 'react'
import type { FormEvent } from 'react'
import type { WorkspaceAnalysis, WorkspaceEntry, WorkspaceStatus } from '../types/army'

interface WorkspacePanelProps {
  status: WorkspaceStatus
  entries: WorkspaceEntry[]
  analysis: WorkspaceAnalysis | null
  busy: boolean
  onSelect: (path: string) => Promise<boolean>
  onClear: () => Promise<void>
  onBrowse: (relativePath: string) => Promise<void>
  onAnalyze: (relativePath: string) => Promise<void>
}

const formatBytes = (bytes?: number) => {
  if (bytes === undefined) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.ceil(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function WorkspacePanel({ status, entries, analysis, busy, onSelect, onClear, onBrowse, onAnalyze }: WorkspacePanelProps) {
  const [path, setPath] = useState('')
  const [currentPath, setCurrentPath] = useState('.')
  const [formError, setFormError] = useState('')

  const selectWorkspace = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const clean = path.trim()
    if (!clean) {
      setFormError('Enter the full path of a project folder you own or are allowed to inspect.')
      return
    }
    setFormError('')
    if (await onSelect(clean)) {
      setPath('')
      setCurrentPath('.')
      await onBrowse('.')
    }
  }

  const openEntry = (entry: WorkspaceEntry) => {
    if (entry.kind === 'directory') {
      setCurrentPath(entry.relativePath)
      void onBrowse(entry.relativePath)
      return
    }
    void onAnalyze(entry.relativePath)
  }

  const goRoot = () => {
    setCurrentPath('.')
    void onBrowse('.')
  }

  const clearWorkspace = async () => {
    await onClear()
    setCurrentPath('.')
  }

  return (
    <section className="panel workspace-panel" aria-labelledby="workspace-title">
      <div className="panel-heading">
        <div><p className="eyebrow">IGRIS WORKSPACE GUARD</p><h2 id="workspace-title">Read-only project diagnostics</h2></div>
        <span className="subtle-badge">{status.configured ? 'BOUND' : 'NO ACCESS'}</span>
      </div>
      <p className="workspace-panel__hint">Select one folder before Igris can inspect it. This V1 tool only lists files and calculates source diagnostics; it cannot write, delete, run commands, or leave the selected folder.</p>

      {!status.configured ? (
        <form className="workspace-form" onSubmit={selectWorkspace}>
          <label htmlFor="workspace-path">Project folder path</label>
          <div><input id="workspace-path" value={path} onChange={(event) => setPath(event.target.value)} placeholder="/Users/you/projects/my-app" /><button className="button" type="submit" disabled={busy}>{busy ? 'Binding…' : 'Select workspace'}</button></div>
          {formError && <p className="form-error" role="alert">{formError}</p>}
          <p className="panel-hint">Electron will replace this text field with the operating-system folder picker in the desktop release.</p>
        </form>
      ) : (
        <div className="workspace-browser">
          <div className="workspace-browser__toolbar"><span><b>{status.rootLabel}</b><small>{currentPath === '.' ? 'root' : currentPath}</small></span><div><button type="button" onClick={goRoot} disabled={busy}>{currentPath === '.' ? 'Refresh' : 'Root'}</button><button type="button" className="workspace-clear" onClick={() => { void clearWorkspace() }} disabled={busy}>Clear</button></div></div>
          <p className="workspace-status">{status.detail}</p>
          <ul className="workspace-entries" aria-label="Selected workspace files">
            {entries.length ? entries.map((entry) => <li key={`${entry.kind}-${entry.relativePath}`}><button type="button" onClick={() => openEntry(entry)} disabled={busy}><span className={`workspace-entry__icon workspace-entry__icon--${entry.kind}`}>{entry.kind === 'directory' ? '⌁' : '▱'}</span><span><b>{entry.name}</b><small>{entry.kind === 'directory' ? 'Open folder' : `${entry.relativePath} · ${formatBytes(entry.sizeBytes)}`}</small></span><i>{entry.kind === 'directory' ? '→' : 'Analyze'}</i></button></li>) : <li className="workspace-empty">No safe entries found in this folder.</li>}
          </ul>
          {analysis && <div className="workspace-analysis"><div><p className="eyebrow">LATEST IGRIS READOUT</p><strong>{analysis.relativePath}</strong><small>{analysis.language} · {formatBytes(analysis.sizeBytes)}{analysis.truncated ? ' · first 500 KB analysed' : ''}</small></div><div className="workspace-analysis__metrics"><span><b>{analysis.lineCount}</b> lines</span><span><b>{analysis.todoCount}</b> TODO</span><span><b>{analysis.fixmeCount}</b> FIXME</span><span><b>{analysis.importCount}</b> imports</span><span><b>{analysis.symbolCount}</b> symbols</span></div><p>SHA-256 (analysed content): <code>{analysis.sha256}</code></p></div>}
        </div>
      )}
    </section>
  )
}
