import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ArmyHQ } from './components/ArmyHQ'
import { AuditTrail } from './components/AuditTrail'
import { ChatPanel } from './components/ChatPanel'
import { FrameworkPanel } from './components/FrameworkPanel'
import { MemoryVault } from './components/MemoryVault'
import { MissionPanel } from './components/MissionPanel'
import { ProviderPanel } from './components/ProviderPanel'
import { commanders, buildArmyStats, defaultFrameworks, defaultProviders } from './data/army'
import { buildMission, isBlockedPrompt } from './lib/mission'
import type { AuditEvent, ChatMessage, Commander, FrameworkStatus, MemoryItem, MemoryKind, Mission, ProviderStatus } from './types/army'

const starterPrompts = [
  'Analyze my project structure and suggest a clean architecture.',
  'Create a research plan for local AI models on my laptop.',
  'Write a safe release checklist for this desktop application.',
]

interface ApiFrameworkStatus {
  id: string
  label: string
  runtime: FrameworkStatus['runtime']
  state: FrameworkStatus['state']
  execution_enabled: boolean
  detail: string
}

interface ApiMemoryItem {
  id: number
  content: string
  kind: MemoryKind
  created_at: string
}

interface ApiChatResponse {
  reply: string
  provider: string
  local_only: boolean
}

interface ApiAuditEvent {
  id: number
  event_type: string
  mission_id?: string
  actor: string
  detail: string
  created_at: string
}

interface ApiMission {
  id: string
  prompt: string
  commander_id: string
  commander: string
  status: Mission['status']
  risk: Mission['risk']
  requires_approval: boolean
  created_at: string
  steps: string[]
  workers: Mission['workers']
  result?: string
}

const auditFromApi = (event: ApiAuditEvent): AuditEvent => ({
  id: event.id,
  eventType: event.event_type,
  missionId: event.mission_id,
  actor: event.actor,
  detail: event.detail,
  createdAt: event.created_at,
})

const memoryFromApi = (memory: ApiMemoryItem): MemoryItem => ({
  id: memory.id,
  content: memory.content,
  kind: memory.kind,
  createdAt: memory.created_at,
})

const frameworkFromApi = (framework: ApiFrameworkStatus): FrameworkStatus => ({
  id: framework.id,
  label: framework.label,
  runtime: framework.runtime,
  state: framework.state,
  executionEnabled: framework.execution_enabled,
  detail: framework.detail,
})

const missionFromApi = (mission: ApiMission): Mission => ({
  id: mission.id,
  prompt: mission.prompt,
  commanderId: mission.commander_id,
  commander: mission.commander,
  status: mission.status,
  risk: mission.risk,
  requiresApproval: mission.requires_approval,
  createdAt: new Date(mission.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  steps: mission.steps,
  workers: mission.workers,
  result: mission.result,
})

const errorDetail = (payload: unknown, fallback: string) => {
  if (typeof payload === 'object' && payload !== null && 'detail' in payload && typeof payload.detail === 'string') {
    return payload.detail
  }
  return fallback
}

function App() {
  const [activeView, setActiveView] = useState<'hq' | 'chat' | 'missions' | 'memory' | 'settings'>('hq')
  const [selectedCommander, setSelectedCommander] = useState<Commander>(commanders[0])
  const [mission, setMission] = useState<Mission | null>(null)
  const [prompt, setPrompt] = useState('')
  const [providers, setProviders] = useState<ProviderStatus[]>(defaultProviders)
  const [frameworks, setFrameworks] = useState<FrameworkStatus[]>(defaultFrameworks)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: 'welcome', role: 'assistant', content: 'I am Jinwoo. Ask for a safe explanation, draft, or plan. Use the command bar above to turn work into a visible Army mission.', provider: 'Jinwoo local interface', localOnly: true },
  ])
  const [chatBusy, setChatBusy] = useState(false)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [memoryAvailable, setMemoryAvailable] = useState(false)
  const [memoryBusy, setMemoryBusy] = useState(false)
  const [notice, setNotice] = useState('Demo command network online. No cloud key is required to explore Army HQ.')

  const stats = useMemo(() => buildArmyStats(mission?.status === 'running' ? 3 : mission ? 1 : 0), [mission])

  const loadAudit = async () => {
    try {
      const response = await fetch('/api/audit')
      const payload = await response.json() as ApiAuditEvent[]
      if (response.ok && Array.isArray(payload)) setAuditEvents(payload.map(auditFromApi))
    } catch {
      // The dashboard remains usable before the local API is available.
    }
  }

  const loadMemories = async (announce = false) => {
    try {
      const response = await fetch('/api/memories')
      const payload = await response.json() as ApiMemoryItem[] | { detail?: string }
      if (!response.ok || !Array.isArray(payload)) {
        setMemoryAvailable(false)
        if (announce) setNotice(errorDetail(payload, 'Memory Vault is unavailable.'))
        return
      }
      setMemories(payload.map(memoryFromApi))
      setMemoryAvailable(true)
      if (announce) setNotice('Memory Vault refreshed from local SQLite.')
    } catch {
      setMemoryAvailable(false)
      if (announce) setNotice('Memory Vault is unavailable. Start the local Python backend to use it.')
    }
  }

  const createMemory = async (content: string, kind: MemoryKind): Promise<boolean> => {
    setMemoryBusy(true)
    try {
      const response = await fetch('/api/memories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, kind, consent: true }),
      })
      const payload = await response.json() as ApiMemoryItem | { detail?: string }
      if (!response.ok || !('id' in payload)) {
        setNotice(errorDetail(payload, 'Memory could not be saved.'))
        return false
      }
      setMemories((current) => [memoryFromApi(payload), ...current])
      setMemoryAvailable(true)
      void loadAudit()
      setNotice('Memory saved locally with your explicit consent.')
      return true
    } catch {
      setMemoryAvailable(false)
      setNotice('Memory could not be saved because the local backend is unavailable.')
      return false
    } finally {
      setMemoryBusy(false)
    }
  }

  const updateMemory = async (memoryId: number, content: string, kind: MemoryKind): Promise<boolean> => {
    setMemoryBusy(true)
    try {
      const response = await fetch(`/api/memories/${memoryId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, kind, consent: true }),
      })
      const payload = await response.json() as ApiMemoryItem | { detail?: string }
      if (!response.ok || !('id' in payload)) {
        setNotice(errorDetail(payload, 'Memory could not be updated.'))
        return false
      }
      const updated = memoryFromApi(payload)
      setMemories((current) => current.map((item) => item.id === updated.id ? updated : item))
      setMemoryAvailable(true)
      void loadAudit()
      setNotice('Memory updated locally with your explicit consent.')
      return true
    } catch {
      setMemoryAvailable(false)
      setNotice('Memory could not be updated because the local backend is unavailable.')
      return false
    } finally {
      setMemoryBusy(false)
    }
  }

  const deleteMemory = async (memoryId: number) => {
    setMemoryBusy(true)
    try {
      const response = await fetch(`/api/memories/${memoryId}`, { method: 'DELETE' })
      if (!response.ok) {
        const payload = await response.json() as { detail?: string }
        setNotice(errorDetail(payload, 'Memory could not be deleted.'))
        return
      }
      setMemories((current) => current.filter((item) => item.id !== memoryId))
      void loadAudit()
      setNotice('Memory deleted from the local vault.')
    } catch {
      setMemoryAvailable(false)
      setNotice('Memory could not be deleted because the local backend is unavailable.')
    } finally {
      setMemoryBusy(false)
    }
  }

  useEffect(() => {
    void loadMemories()
    void loadAudit()
  }, [])

  useEffect(() => {
    let mounted = true
    fetch('/api/providers')
      .then(async (response) => response.ok ? response.json() : Promise.reject(new Error('Backend unavailable')))
      .then((payload: { providers?: ProviderStatus[] }) => {
        if (mounted && payload.providers?.length) {
          setProviders(payload.providers)
          setNotice('Local backend connected. Provider health is being reported by Jinwoo.')
        }
      })
      .catch(() => {
        // The UI deliberately stays useful with its deterministic demo fallback.
      })
    fetch('/api/frameworks')
      .then(async (response) => response.ok ? response.json() : Promise.reject(new Error('Framework registry unavailable')))
      .then((payload: { frameworks?: ApiFrameworkStatus[] }) => {
        if (mounted && payload.frameworks?.length) {
          setFrameworks(payload.frameworks.map(frameworkFromApi))
        }
      })
      .catch(() => {
        // Keep the explicit no-install fallback visible in the standalone dashboard.
      })
    return () => { mounted = false }
  }, [])

  const showMission = (nextMission: Mission, fallback: boolean) => {
    const commander = commanders.find((item) => item.id === nextMission.commanderId) ?? commanders[0]
    setSelectedCommander(commander)
    setMission(nextMission)
    setPrompt('')
    setActiveView('missions')
    const planState = nextMission.requiresApproval ? 'Approval is required before an impactful action.' : 'A safe plan is ready.'
    setNotice(`${commander.name} accepted the mission. ${planState}${fallback ? ' Running in browser demo fallback.' : ''}`)
  }

  const sendChat = async (message: string, preferredProvider: string | undefined, allowCloud: boolean): Promise<boolean> => {
    const clean = message.trim()
    if (!clean) return false
    if (isBlockedPrompt(clean)) {
      setNotice('This request crosses a security or privacy boundary, so Jinwoo did not send it to a provider.')
      return false
    }

    const messageId = `chat-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
    setChatMessages((current) => [...current, { id: messageId, role: 'user', content: clean }])
    setChatBusy(true)
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: clean, preferred_provider: preferredProvider, allow_cloud: allowCloud }),
      })
      const payload = await response.json() as ApiChatResponse | { detail?: string }
      if (!response.ok || !('reply' in payload)) {
        const detail = errorDetail(payload, 'Jinwoo could not complete that chat request.')
        setChatMessages((current) => [...current, { id: `${messageId}-error`, role: 'assistant', content: detail, provider: 'Safety gateway', localOnly: true }])
        setNotice(detail)
        return false
      }
      setChatMessages((current) => [...current, {
        id: `${messageId}-reply`,
        role: 'assistant',
        content: payload.reply,
        provider: payload.provider,
        localOnly: payload.local_only,
      }])
      setNotice(payload.local_only ? 'Jinwoo replied through a local or demo route.' : 'Jinwoo replied through the cloud route you explicitly approved.')
      return true
    } catch {
      const detail = 'Jinwoo chat is unavailable. Start the local Python backend, then try again.'
      setChatMessages((current) => [...current, { id: `${messageId}-offline`, role: 'assistant', content: detail, provider: 'Local interface', localOnly: true }])
      setNotice(detail)
      return false
    } finally {
      setChatBusy(false)
    }
  }

  const dispatchMission = async (message: string) => {
    const clean = message.trim()
    if (!clean) return
    if (isBlockedPrompt(clean)) {
      setNotice('This request crosses a security or privacy boundary, so Jinwoo did not create a mission.')
      return
    }

    try {
      const response = await fetch('/api/missions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: clean }),
      })
      const payload = await response.json() as ApiMission | { detail?: string }
      if (!response.ok) {
        setNotice('detail' in payload ? payload.detail ?? 'Mission rejected by policy.' : 'Mission rejected by policy.')
        return
      }
      showMission(missionFromApi(payload as ApiMission), false)
      void loadAudit()
    } catch {
      // A standalone dashboard remains usable before the Python service is installed.
      showMission(buildMission(clean), true)
    }
  }

  const submitPrompt = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void dispatchMission(prompt)
  }

  const transitionMission = async (action: 'approve' | 'cancel') => {
    if (!mission) return
    try {
      const response = await fetch(`/api/missions/${mission.id}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: action === 'approve' ? JSON.stringify({ approved_by: 'local-user' }) : undefined,
      })
      const payload = await response.json() as ApiMission | { detail?: string }
      if (!response.ok) {
        setNotice('detail' in payload ? payload.detail ?? 'Mission state could not change.' : 'Mission state could not change.')
        return
      }
      const updated = missionFromApi(payload as ApiMission)
      setMission(updated)
      void loadAudit()
      setNotice(action === 'approve' ? 'Mission approval recorded. No unconfigured desktop tool was executed.' : 'Mission rejected. No tool action was executed.')
    } catch {
      setMission(action === 'approve'
        ? { ...mission, status: 'complete', result: 'Approved in local UI demo. No desktop action was executed.' }
        : { ...mission, status: 'cancelled', result: 'Mission rejected by the user. No action was run.' })
      setNotice('Local UI demo recorded the decision. Connect the backend for a persistent audit record.')
    }
  }

  const selectCommander = (commander: Commander) => {
    setSelectedCommander(commander)
    setNotice(`${commander.name} selected — ${commander.defaultSafety.replaceAll('-', ' ')} policy active.`)
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">♛</span><span><b>JINWOO</b><small>SHADOW ARMY</small></span></div>
        <nav aria-label="Primary navigation">
          <button className={activeView === 'hq' ? 'nav-item nav-item--active' : 'nav-item'} type="button" onClick={() => setActiveView('hq')}><span>⌘</span> Army HQ</button>
          <button className={activeView === 'chat' ? 'nav-item nav-item--active' : 'nav-item'} type="button" onClick={() => setActiveView('chat')}><span>✦</span> Chat</button>
          <button className={activeView === 'missions' ? 'nav-item nav-item--active' : 'nav-item'} type="button" onClick={() => setActiveView('missions')}><span>◈</span> Missions</button>
          <button className={activeView === 'memory' ? 'nav-item nav-item--active' : 'nav-item'} type="button" onClick={() => setActiveView('memory')}><span>◌</span> Memory Vault</button>
          <button className={activeView === 'settings' ? 'nav-item nav-item--active' : 'nav-item'} type="button" onClick={() => setActiveView('settings')}><span>⚙</span> Settings</button>
        </nav>
        <div className="sidebar-status">
          <span className="signal-dot" />
          <div><b>LOCAL MODE</b><small>Private by default</small></div>
        </div>
        <p className="sidebar-foot">Every impactful desktop action needs visible approval.</p>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div><p className="eyebrow">SHADOW ARMY // COMMAND CONSOLE</p><strong>{activeView === 'hq' ? 'Army HQ' : activeView === 'chat' ? 'Local AI Chat' : activeView === 'missions' ? 'Mission Control' : activeView === 'memory' ? 'Memory Vault' : 'Command Settings'}</strong></div>
          <div className="topbar-actions"><span className="mode-indicator"><i /> LOCAL-FIRST</span><button type="button" className="avatar-button" aria-label="Open commander profile">J</button></div>
        </header>

        <section className="command-bar panel">
          <div className="command-bar__icon">✦</div>
          <form onSubmit={submitPrompt}>
            <label htmlFor="command">Give the army an order</label>
            <input id="command" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Example: analyze my project and make a safe fix plan" />
          </form>
          <button className="button command-bar__button" type="button" onClick={() => { void dispatchMission(prompt) }}>Deploy <span>↗</span></button>
        </section>

        <p className="notice"><span className="status-dot status-dot--ready" />{notice}</p>

        {activeView === 'hq' && <ArmyHQ stats={stats} selectedCommander={selectedCommander} onSelectCommander={selectCommander} />}

        {activeView === 'chat' && <ChatPanel messages={chatMessages} providers={providers} busy={chatBusy} onSend={sendChat} />}

        {activeView === 'missions' && (
          <div className="mission-layout">
            <MissionPanel mission={mission} selectedCommander={selectedCommander} onApprove={() => { void transitionMission('approve') }} onCancel={() => { void transitionMission('cancel') }} />
            <aside className="side-stack">
              <ProviderPanel providers={providers} />
              <AuditTrail events={auditEvents} missionId={mission?.id} />
              <section className="panel quick-panel"><p className="eyebrow">QUICK MISSIONS</p><h2>Try a safe request</h2>{starterPrompts.map((item) => <button type="button" onClick={() => { void dispatchMission(item) }} key={item}>{item}<span>↗</span></button>)}</section>
            </aside>
          </div>
        )}

        {activeView === 'memory' && (
          <MemoryVault
            memories={memories}
            available={memoryAvailable}
            busy={memoryBusy}
            onCreate={createMemory}
            onUpdate={updateMemory}
            onDelete={deleteMemory}
            onRefresh={() => loadMemories(true)}
          />
        )}

        {activeView === 'settings' && (
          <div className="settings-layout">
            <aside className="side-stack"><ProviderPanel providers={providers} /><FrameworkPanel frameworks={frameworks} /></aside>
            <section className="panel settings-card"><p className="eyebrow">ROUTING POLICY</p><h2>Local first, cloud by choice.</h2><p>Ollama and LM Studio can power local runs. Claude, GLM and Hugging Face adapters remain disabled until their keys are stored outside the browser bundle.</p><div className="settings-list"><span>Python FastAPI orchestration</span><span>TypeScript command dashboard</span><span>Optional Rust / Go sidecars after profiling</span><span>SQLite + local vector-memory foundation</span><span>Framework adapters remain policy-gated</span></div></section>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
