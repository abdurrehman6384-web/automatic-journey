import { useState } from 'react'
import type { FormEvent } from 'react'
import type { MemoryItem, MemoryKind } from '../types/army'

interface MemoryVaultProps {
  memories: MemoryItem[]
  available: boolean
  busy: boolean
  onCreate: (content: string, kind: MemoryKind) => Promise<boolean>
  onUpdate: (memoryId: number, content: string, kind: MemoryKind) => Promise<boolean>
  onDelete: (memoryId: number) => Promise<void>
  onRefresh: () => Promise<void>
}

const memoryKinds: MemoryKind[] = ['preference', 'project', 'note', 'reminder']

const displayKind = (kind: MemoryKind) => kind[0].toUpperCase() + kind.slice(1)

export function MemoryVault({ memories, available, busy, onCreate, onUpdate, onDelete, onRefresh }: MemoryVaultProps) {
  const [content, setContent] = useState('')
  const [kind, setKind] = useState<MemoryKind>('note')
  const [consent, setConsent] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [pendingDeleteId, setPendingDeleteId] = useState<number | null>(null)
  const [formError, setFormError] = useState('')

  const resetForm = () => {
    setContent('')
    setKind('note')
    setConsent(false)
    setEditingId(null)
    setFormError('')
  }

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = content.trim()
    if (!trimmed) {
      setFormError('Write a memory before saving it.')
      return
    }
    if (!consent) {
      setFormError('Confirm explicit consent before saving a memory.')
      return
    }
    setFormError('')
    const saved = editingId === null
      ? await onCreate(trimmed, kind)
      : await onUpdate(editingId, trimmed, kind)
    if (saved) resetForm()
  }

  const edit = (memory: MemoryItem) => {
    setPendingDeleteId(null)
    setEditingId(memory.id)
    setContent(memory.content)
    setKind(memory.kind)
    setConsent(false)
    setFormError('Confirm consent again before replacing this memory.')
  }

  const requestDelete = (memoryId: number) => {
    if (pendingDeleteId === memoryId) {
      setPendingDeleteId(null)
      void onDelete(memoryId)
      return
    }
    setPendingDeleteId(memoryId)
  }

  const exportMemories = () => {
    const exportDocument = JSON.stringify({ exportedAt: new Date().toISOString(), memories }, null, 2)
    const url = URL.createObjectURL(new Blob([exportDocument], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'jinwoo-memory-vault.json'
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="memory-vault" aria-labelledby="memory-vault-title">
      <div className="memory-vault__intro panel">
        <div>
          <p className="eyebrow">LOCAL MEMORY VAULT</p>
          <h2 id="memory-vault-title">Memory belongs to the user.</h2>
          <p>Only memories you explicitly save are stored in local SQLite. Credentials and one-time codes are rejected before storage; optional Mem0 sync stays off.</p>
        </div>
        <div className="memory-vault__actions">
          <button className="button button--ghost" type="button" onClick={() => { void onRefresh() }} disabled={busy}>Refresh</button>
          <button className="button button--ghost" type="button" onClick={exportMemories} disabled={!memories.length}>Export JSON</button>
        </div>
      </div>

      <div className="memory-vault__grid">
        <section className="panel memory-form-panel">
          <p className="eyebrow">{editingId === null ? 'SAVE A MEMORY' : 'EDIT MEMORY'}</p>
          <h2>{editingId === null ? 'Keep a useful preference' : 'Replace a saved memory'}</h2>
          <form className="memory-form" onSubmit={submit}>
            <label htmlFor="memory-content">Memory</label>
            <textarea id="memory-content" value={content} maxLength={2000} onChange={(event) => setContent(event.target.value)} placeholder="Example: Prefer Roman Urdu for product explanations." />
            <div className="memory-form__options">
              <label htmlFor="memory-kind">Type</label>
              <select id="memory-kind" value={kind} onChange={(event) => setKind(event.target.value as MemoryKind)}>
                {memoryKinds.map((value) => <option key={value} value={value}>{displayKind(value)}</option>)}
              </select>
            </div>
            <label className="consent-check"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /><span>I explicitly consent to save this local memory.</span></label>
            {formError && <p className="form-error" role="alert">{formError}</p>}
            <div className="memory-form__buttons">
              {editingId !== null && <button className="button button--ghost" type="button" onClick={resetForm} disabled={busy}>Cancel</button>}
              <button className="button" type="submit" disabled={busy || !available}>{busy ? 'Saving…' : editingId === null ? 'Save locally' : 'Save replacement'}</button>
            </div>
          </form>
          {!available && <p className="panel-hint">Connect the local Python backend to manage persistent memory.</p>}
        </section>

        <section className="panel memory-list-panel" aria-live="polite">
          <div className="panel-heading">
            <div><p className="eyebrow">SAVED LOCALLY</p><h2>{memories.length} {memories.length === 1 ? 'memory' : 'memories'}</h2></div>
            <span className="subtle-badge">PRIVATE</span>
          </div>
          {memories.length ? (
            <ul className="memory-list">
              {memories.map((memory) => (
                <li key={memory.id}>
                  <div className="memory-item__heading"><span>{displayKind(memory.kind)}</span><time dateTime={memory.createdAt}>{new Date(memory.createdAt).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</time></div>
                  <p>{memory.content}</p>
                  <div className="memory-item__actions">
                    <button type="button" onClick={() => edit(memory)} disabled={busy}>Edit</button>
                    <button className="memory-delete" type="button" onClick={() => requestDelete(memory.id)} disabled={busy}>{pendingDeleteId === memory.id ? 'Confirm delete' : 'Delete'}</button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="memory-empty"><span>◌</span><p>No consented memories yet. Saved preferences and project notes will appear here.</p></div>
          )}
        </section>
      </div>
    </section>
  )
}
