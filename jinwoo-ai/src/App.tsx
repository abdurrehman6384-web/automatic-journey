import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ArmyHQ } from './components/ArmyHQ'
import { AuditTrail } from './components/AuditTrail'
import { ChatPanel } from './components/ChatPanel'
import { ControlReviewPanel } from './components/ControlReviewPanel'
import { FrameworkPanel } from './components/FrameworkPanel'
import { MemoryVault } from './components/MemoryVault'
import { MissionPanel } from './components/MissionPanel'
import { ProviderPanel } from './components/ProviderPanel'
import { ResearchPanel } from './components/ResearchPanel'
import { SecurityScanPanel } from './components/SecurityScanPanel'
import { WorkspacePanel } from './components/WorkspacePanel'
import { commanders, buildArmyStats, defaultFrameworks, defaultProviders } from './data/army'
import { buildMission, isBlockedPrompt } from './lib/mission'
import type { AuditEvent, ChatMessage, Commander, ControlReview, FrameworkDryRun, FrameworkStatus, MemoryItem, MemoryKind, Mission, ProviderStatus, ResearchPlan, SecurityScanPlan, WorkspaceAnalysis, WorkspaceEntry, WorkspaceStatus } from './types/army'

const starterPrompts = [
  'Analyze my project structure and suggest a clean architecture.',
  'Create a research plan for local AI models on my laptop.',
  'Write a safe release checklist for this desktop application.',
]

interface ApiFrameworkStatus {
  id: string
  label: string
  runtime: FrameworkStatus['runtime']
  category: FrameworkStatus['category']
  integration_batch: number
  owner_commander: string
  license: string
  source_url?: string
  state: FrameworkStatus['state']
  implementation_status: FrameworkStatus['implementationStatus']
  execution_enabled: boolean
  capabilities?: string[]
  activation_boundary?: FrameworkStatus['activationBoundary']
  detail: string
}

interface ApiFrameworkDryRun {
  framework_id: string
  framework_label: string
  policy_outcome: FrameworkDryRun['policyOutcome']
  requested_agents: number
  bounded_runtime_workers: number
  external_runtime_invoked: boolean
  requires_approval: boolean
  summary: string
  next_steps: string[]
}

interface ApiControlReviewCheck {
  id: string
  label: string
  passed: boolean
  detail: string
}

interface ApiControlReview {
  reviewed_at: string
  all_passed: boolean
  external_runtime_invoked: boolean
  summary: string
  checks: ApiControlReviewCheck[]
}

interface ApiSecurityScanPlan {
  scanner_id: SecurityScanPlan['scannerId']
  scanner_label: string
  workspace_configured: boolean
  license_review_required: boolean
  external_scan_started: boolean
  requires_approval_for_scan: boolean
  safeguards: string[]
  next_steps: string[]
}

interface ApiResearchTarget {
  url: string
  hostname: string
}

interface ApiResearchPlan {
  framework_id: ResearchPlan['frameworkId']
  topic: string
  targets: ApiResearchTarget[]
  external_fetch_started: boolean
  requires_approval_for_fetch: boolean
  safeguards: string[]
  next_steps: string[]
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

interface ApiWorkspaceStatus {
  configured: boolean
  root_label?: string
  read_only: boolean
  detail: string
}

interface ApiWorkspaceEntry {
  name: string
  relative_path: string
  kind: WorkspaceEntry['kind']
  size_bytes?: number
}

interface ApiWorkspaceAnalysis {
  relative_path: string
  language: string
  size_bytes: number
  line_count: number
  todo_count: number
  fixme_count: number
  import_count: number
  symbol_count: number
  sha256: string
  truncated: boolean
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

const frameworkDryRunFromApi = (result: ApiFrameworkDryRun): FrameworkDryRun => ({
  frameworkId: result.framework_id,
  frameworkLabel: result.framework_label,
  policyOutcome: result.policy_outcome,
  requestedAgents: result.requested_agents,
  boundedRuntimeWorkers: result.bounded_runtime_workers,
  externalRuntimeInvoked: result.external_runtime_invoked,
  requiresApproval: result.requires_approval,
  summary: result.summary,
  nextSteps: result.next_steps,
})

const workspaceStatusFromApi = (workspace: ApiWorkspaceStatus): WorkspaceStatus => ({
  configured: workspace.configured,
  rootLabel: workspace.root_label,
  readOnly: workspace.read_only,
  detail: workspace.detail,
})

const workspaceEntryFromApi = (entry: ApiWorkspaceEntry): WorkspaceEntry => ({
  name: entry.name,
  relativePath: entry.relative_path,
  kind: entry.kind,
  sizeBytes: entry.size_bytes,
})

const workspaceAnalysisFromApi = (analysis: ApiWorkspaceAnalysis): WorkspaceAnalysis => ({
  relativePath: analysis.relative_path,
  language: analysis.language,
  sizeBytes: analysis.size_bytes,
  lineCount: analysis.line_count,
  todoCount: analysis.todo_count,
  fixmeCount: analysis.fixme_count,
  importCount: analysis.import_count,
  symbolCount: analysis.symbol_count,
  sha256: analysis.sha256,
  truncated: analysis.truncated,
})

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
  category: framework.category,
  integrationBatch: framework.integration_batch,
  ownerCommander: framework.owner_commander,
  license: framework.license,
  sourceUrl: framework.source_url,
  state: framework.state,
  implementationStatus: framework.implementation_status,
  executionEnabled: framework.execution_enabled,
  capabilities: framework.capabilities,
  activationBoundary: framework.activation_boundary,
  detail: framework.detail,
})

const controlReviewFromApi = (review: ApiControlReview): ControlReview => ({
  reviewedAt: review.reviewed_at,
  allPassed: review.all_passed,
  externalRuntimeInvoked: review.external_runtime_invoked,
  summary: review.summary,
  checks: review.checks,
})

const securityScanPlanFromApi = (plan: ApiSecurityScanPlan): SecurityScanPlan => ({
  scannerId: plan.scanner_id,
  scannerLabel: plan.scanner_label,
  workspaceConfigured: plan.workspace_configured,
  licenseReviewRequired: plan.license_review_required,
  externalScanStarted: plan.external_scan_started,
  requiresApprovalForScan: plan.requires_approval_for_scan,
  safeguards: plan.safeguards,
  nextSteps: plan.next_steps,
})

const researchPlanFromApi = (plan: ApiResearchPlan): ResearchPlan => ({
  frameworkId: plan.framework_id,
  topic: plan.topic,
  targets: plan.targets,
  externalFetchStarted: plan.external_fetch_started,
  requiresApprovalForFetch: plan.requires_approval_for_fetch,
  safeguards: plan.safeguards,
  nextSteps: plan.next_steps,
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
  if (typeof payload !== 'object' || payload === null || !('detail' in payload)) return fallback
  const detail = payload.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const firstMessage = detail.find((item): item is { msg: string } => (
      typeof item === 'object' && item !== null && 'msg' in item && typeof item.msg === 'string'
    ))
    if (firstMessage) return firstMessage.msg
  }
  return fallback
}

function App() {
  const [activeView, setActiveView] = useState<'hq' | 'chat' | 'missions' | 'research' | 'memory' | 'settings'>('hq')
  const [selectedCommander, setSelectedCommander] = useState<Commander>(commanders[0])
  const [mission, setMission] = useState<Mission | null>(null)
  const [prompt, setPrompt] = useState('')
  const [providers, setProviders] = useState<ProviderStatus[]>(defaultProviders)
  const [frameworks, setFrameworks] = useState<FrameworkStatus[]>(defaultFrameworks)
  const [frameworkDryRun, setFrameworkDryRun] = useState<FrameworkDryRun | null>(null)
  const [frameworkBusy, setFrameworkBusy] = useState(false)
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null)
  const [researchBusy, setResearchBusy] = useState(false)
  const [controlReview, setControlReview] = useState<ControlReview | null>(null)
  const [controlReviewBusy, setControlReviewBusy] = useState(false)
  const [securityScanPlan, setSecurityScanPlan] = useState<SecurityScanPlan | null>(null)
  const [securityScanBusy, setSecurityScanBusy] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: 'welcome', role: 'assistant', content: 'I am Jinwoo. Ask for a safe explanation, draft, or plan. Use the command bar above to turn work into a visible Army mission.', provider: 'Jinwoo local interface', localOnly: true },
  ])
  const [chatBusy, setChatBusy] = useState(false)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [workspaceStatus, setWorkspaceStatus] = useState<WorkspaceStatus>({ configured: false, readOnly: true, detail: 'No workspace selected. Igris has no file access until you select a project folder.' })
  const [workspaceEntries, setWorkspaceEntries] = useState<WorkspaceEntry[]>([])
  const [workspaceAnalysis, setWorkspaceAnalysis] = useState<WorkspaceAnalysis | null>(null)
  const [workspaceBusy, setWorkspaceBusy] = useState(false)
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

  const runFrameworkDryRun = async (frameworkId: string, prompt: string, requestedAgents: number): Promise<boolean> => {
    setFrameworkBusy(true)
    try {
      const response = await fetch(`/api/frameworks/${frameworkId}/dry-run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, requested_agents: requestedAgents }),
      })
      const payload = await response.json() as ApiFrameworkDryRun | { detail?: string }
      if (!response.ok || !('framework_id' in payload)) {
        setNotice(errorDetail(payload, 'The framework dry run could not be prepared.'))
        return false
      }
      const result = frameworkDryRunFromApi(payload)
      setFrameworkDryRun(result)
      void loadAudit()
      setNotice(`${result.frameworkLabel} prepared a ${result.policyOutcome} without invoking an upstream runtime.`)
      return true
    } catch {
      setNotice('The framework dry run is unavailable because the local backend is offline.')
      return false
    } finally {
      setFrameworkBusy(false)
    }
  }

  const runControlReview = async (): Promise<boolean> => {
    setControlReviewBusy(true)
    try {
      const response = await fetch('/api/control/review', { method: 'POST' })
      const payload = await response.json() as ApiControlReview | { detail?: string }
      if (!response.ok || !('all_passed' in payload)) {
        setNotice(errorDetail(payload, 'The local control review could not be completed.'))
        return false
      }
      const result = controlReviewFromApi(payload)
      setControlReview(result)
      void loadAudit()
      setNotice(result.allPassed ? 'Native control review passed. No optional runtime was invoked.' : 'Native control review found an item that needs attention. No optional runtime was invoked.')
      return true
    } catch {
      setNotice('The local control review is unavailable because the backend is offline.')
      return false
    } finally {
      setControlReviewBusy(false)
    }
  }

  const createSecurityScanPlan = async (scannerId: SecurityScanPlan['scannerId'], confirmAuthorized: boolean): Promise<boolean> => {
    setSecurityScanBusy(true)
    try {
      const response = await fetch('/api/security/scan-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scanner_id: scannerId, confirm_authorized: confirmAuthorized }),
      })
      const payload = await response.json() as ApiSecurityScanPlan | { detail?: string }
      if (!response.ok || !('scanner_id' in payload)) {
        setNotice(errorDetail(payload, 'Greed could not prepare that no-scan security plan.'))
        return false
      }
      const result = securityScanPlanFromApi(payload)
      setSecurityScanPlan(result)
      void loadAudit()
      setNotice(`Greed prepared a ${result.scannerLabel} boundary without reading a file or starting a scanner.`)
      return true
    } catch {
      setNotice('The security planner is unavailable because the local backend is offline.')
      return false
    } finally {
      setSecurityScanBusy(false)
    }
  }

  const createResearchPlan = async (frameworkId: ResearchPlan['frameworkId'], topic: string, targets: string[], confirmPublicSources: boolean): Promise<boolean> => {
    setResearchBusy(true)
    try {
      const response = await fetch('/api/research/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          framework_id: frameworkId,
          topic,
          targets,
          confirm_public_sources: confirmPublicSources,
        }),
      })
      const payload = await response.json() as ApiResearchPlan | { detail?: string }
      if (!response.ok || !('framework_id' in payload)) {
        setNotice(errorDetail(payload, 'Tank could not create that no-fetch research plan.'))
        return false
      }
      const result = researchPlanFromApi(payload)
      setResearchPlan(result)
      void loadAudit()
      setNotice(`Tank validated ${result.targets.length} public research target${result.targets.length === 1 ? '' : 's'} without opening a URL.`)
      return true
    } catch {
      setNotice('The research planner is unavailable because the local backend is offline.')
      return false
    } finally {
      setResearchBusy(false)
    }
  }

  const loadWorkspace = async (announce = false): Promise<WorkspaceStatus | null> => {
    try {
      const response = await fetch('/api/workspace')
      const payload = await response.json() as ApiWorkspaceStatus | { detail?: string }
      if (!response.ok || !('configured' in payload)) {
        if (announce) setNotice(errorDetail(payload, 'Workspace status is unavailable.'))
        return null
      }
      const nextStatus = workspaceStatusFromApi(payload)
      setWorkspaceStatus(nextStatus)
      if (!nextStatus.configured) {
        setWorkspaceEntries([])
        setWorkspaceAnalysis(null)
        setSecurityScanPlan(null)
      } else {
        void browseWorkspace('.')
      }
      if (announce) setNotice(nextStatus.detail)
      return nextStatus
    } catch {
      if (announce) setNotice('Workspace controls are unavailable. Start the local Python backend to use them.')
      return null
    }
  }

  const browseWorkspace = async (relativePath: string) => {
    setWorkspaceBusy(true)
    try {
      const response = await fetch(`/api/workspace/files?relative_path=${encodeURIComponent(relativePath)}`)
      const payload = await response.json() as ApiWorkspaceEntry[] | { detail?: string }
      if (!response.ok || !Array.isArray(payload)) {
        setNotice(errorDetail(payload, 'Workspace files could not be listed.'))
        return
      }
      setWorkspaceEntries(payload.map(workspaceEntryFromApi))
    } catch {
      setNotice('Workspace files could not be listed because the local backend is unavailable.')
    } finally {
      setWorkspaceBusy(false)
    }
  }

  const selectWorkspace = async (path: string): Promise<boolean> => {
    setWorkspaceBusy(true)
    try {
      const response = await fetch('/api/workspace', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      const payload = await response.json() as ApiWorkspaceStatus | { detail?: string }
      if (!response.ok || !('configured' in payload)) {
        setNotice(errorDetail(payload, 'Workspace could not be selected.'))
        return false
      }
      setWorkspaceStatus(workspaceStatusFromApi(payload))
      setWorkspaceEntries([])
      setWorkspaceAnalysis(null)
      setSecurityScanPlan(null)
      void loadAudit()
      setNotice('Workspace selected. Igris can now run read-only diagnostics inside this folder only.')
      return true
    } catch {
      setNotice('Workspace could not be selected because the local backend is unavailable.')
      return false
    } finally {
      setWorkspaceBusy(false)
    }
  }

  const clearWorkspace = async () => {
    setWorkspaceBusy(true)
    try {
      const response = await fetch('/api/workspace', { method: 'DELETE' })
      if (!response.ok) {
        setNotice('Workspace boundary could not be cleared.')
        return
      }
      setWorkspaceStatus({ configured: false, readOnly: true, detail: 'No workspace selected. Igris has no file access until you select a project folder.' })
      setWorkspaceEntries([])
      setWorkspaceAnalysis(null)
      setSecurityScanPlan(null)
      void loadAudit()
      setNotice('Workspace boundary cleared. Igris no longer has project-file access.')
    } catch {
      setNotice('Workspace boundary could not be cleared because the local backend is unavailable.')
    } finally {
      setWorkspaceBusy(false)
    }
  }

  const analyzeWorkspaceFile = async (relativePath: string) => {
    setWorkspaceBusy(true)
    try {
      const response = await fetch('/api/workspace/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ relative_path: relativePath }),
      })
      const payload = await response.json() as ApiWorkspaceAnalysis | { detail?: string }
      if (!response.ok || !('sha256' in payload)) {
        setNotice(errorDetail(payload, 'Igris could not analyse that file.'))
        return
      }
      setWorkspaceAnalysis(workspaceAnalysisFromApi(payload))
      setNotice('Igris completed a read-only local source diagnostic. No file was changed.')
    } catch {
      setNotice('Igris diagnostics are unavailable because the local backend is unavailable.')
    } finally {
      setWorkspaceBusy(false)
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
    void loadWorkspace()
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
          <button className={activeView === 'research' ? 'nav-item nav-item--active' : 'nav-item'} type="button" onClick={() => setActiveView('research')}><span>◍</span> Research Gate</button>
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
          <div><p className="eyebrow">SHADOW ARMY // COMMAND CONSOLE</p><strong>{activeView === 'hq' ? 'Army HQ' : activeView === 'chat' ? 'Local AI Chat' : activeView === 'missions' ? 'Mission Control' : activeView === 'research' ? 'Tank Research Gate' : activeView === 'memory' ? 'Memory Vault' : 'Command Settings'}</strong></div>
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

        {activeView === 'research' && <ResearchPanel plan={researchPlan} busy={researchBusy} onPlan={createResearchPlan} />}

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
            <div className="settings-main-stack">
              <WorkspacePanel status={workspaceStatus} entries={workspaceEntries} analysis={workspaceAnalysis} busy={workspaceBusy} onSelect={selectWorkspace} onClear={clearWorkspace} onBrowse={browseWorkspace} onAnalyze={analyzeWorkspaceFile} />
              <section className="panel settings-card"><p className="eyebrow">ROUTING POLICY</p><h2>Local first, cloud by choice.</h2><p>Ollama and LM Studio can power local runs. Claude, GLM and Hugging Face adapters remain disabled until their keys are stored outside the browser bundle. Optional framework lanes stay under Jinwoo control.</p><div className="settings-list"><span>Python FastAPI orchestration</span><span>TypeScript command dashboard</span><span>Optional Rust / Go sidecars after profiling</span><span>SQLite + local vector-memory foundation</span><span>Framework adapters remain policy-gated</span></div></section>
              <SecurityScanPanel workspace={workspaceStatus} plan={securityScanPlan} busy={securityScanBusy} onPlan={createSecurityScanPlan} />
              <ControlReviewPanel review={controlReview} busy={controlReviewBusy} onRun={runControlReview} />
            </div>
            <aside className="side-stack"><ProviderPanel providers={providers} /><FrameworkPanel frameworks={frameworks} dryRun={frameworkDryRun} busy={frameworkBusy} onDryRun={runFrameworkDryRun} /></aside>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
