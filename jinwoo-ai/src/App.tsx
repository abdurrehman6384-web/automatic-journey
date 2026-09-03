import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ArmyExplorer } from './components/ArmyExplorer'
import { ArmyHQ } from './components/ArmyHQ'
import { AuditTrail } from './components/AuditTrail'
import { ChatPanel } from './components/ChatPanel'
import { ControlReviewPanel } from './components/ControlReviewPanel'
import { FrameworkPanel } from './components/FrameworkPanel'
import { InteractionLab } from './components/InteractionLab'
import { MemoryVault } from './components/MemoryVault'
import { NativeSkillLibraryPanel } from './components/NativeSkillLibraryPanel'
import type { NativeSkillDetail, NativeSkillLibraryData, NativeSkillPlan, NativeSkillSummary } from './components/NativeSkillLibraryPanel'
import { MissionPanel } from './components/MissionPanel'
import { ProviderPanel } from './components/ProviderPanel'
import { ResearchPanel } from './components/ResearchPanel'
import { SecurityScanPanel } from './components/SecurityScanPanel'
import { ShadowArmyCore } from './components/ShadowArmyCore'
import { SkillIntakePanel } from './components/SkillIntakePanel'
import { UpgradeReviewPanel } from './components/UpgradeReviewPanel'
import { WorkspacePanel } from './components/WorkspacePanel'
import { commanders, buildArmyStats, defaultFrameworks, defaultProviders } from './data/army'
import { buildMission, isBlockedPrompt } from './lib/mission'
import type { AuditEvent, ChatMessage, Commander, ControlReview, CoordinationPattern, FrameworkDryRun, FrameworkStatus, MemoryItem, MemoryKind, Mission, ProviderStatus, ResearchPlan, SecurityScanPlan, ShadowArmyOverview, ShadowArmyPlan, WorkspaceAnalysis, WorkspaceEntry, WorkspaceSearch, WorkspaceStatus } from './types/army'

const starterPrompts = [
  'Analyze my project structure and suggest a clean architecture.',
  'Create a research plan for local AI models on my laptop.',
  'Write a safe release checklist for this desktop application.',
]

type ViewId = 'hq' | 'missions' | 'army' | 'core' | 'chat' | 'workspace' | 'research' | 'security' | 'memory' | 'interaction' | 'skills' | 'registry' | 'control' | 'settings'

type NavigationItem = {
  id: ViewId
  label: string
  icon: string
}

const viewMeta: Record<ViewId, { eyebrow: string; title: string; description: string }> = {
  hq: { eyebrow: 'SHADOW ARMY // COMMAND CONSOLE', title: 'Army HQ', description: 'Visible, local-first command coordination.' },
  missions: { eyebrow: 'MISSION CONTROL // APPROVAL FIRST', title: 'Mission workbench', description: 'Plan, verify and approve meaningful actions.' },
  army: { eyebrow: 'SHADOW ARMY // VISIBLE HIERARCHY', title: 'Army explorer', description: 'Inspect logical roles without spawning a hidden army.' },
  core: { eyebrow: 'SHADOW ARMY // NATIVE MULTI-AGENT CORE', title: 'Army core', description: 'Map hierarchy, patterns and approval edges without starting a swarm.' },
  chat: { eyebrow: 'LOCAL AI // CONSENT AWARE', title: 'Command channel', description: 'Talk locally by default; cloud use is explicit.' },
  workspace: { eyebrow: 'IGRIS // READ-ONLY GUARD', title: 'Workspace Guard', description: 'Confined source diagnostics inside a selected folder.' },
  research: { eyebrow: 'TANK // NO-FETCH GATE', title: 'Research Gate', description: 'Validate a public-source plan without opening a URL.' },
  security: { eyebrow: 'GREED // DEFENSIVE ONLY', title: 'Security Gate', description: 'Prepare an authorised no-scan boundary review.' },
  memory: { eyebrow: 'LOCAL MEMORY // CONSENT FIRST', title: 'Memory Vault', description: 'Inspect and control locally stored memories.' },
  interaction: { eyebrow: 'BATCH 06 // SAFETY-LOCKED', title: 'Interaction Lab', description: 'Review gesture and hardware concepts without capture or control.' },
  skills: { eyebrow: 'BATCH 13 // CLEAN-ROOM PORTABLE SKILLS', title: 'Native skill command', description: 'Discover, select, pause and revise local planning-only skill plans.' },
  registry: { eyebrow: 'ADAPTERS & SKILL CATALOGUES // EXPLICIT BOUNDARIES', title: 'Framework & skill registry', description: 'Review source and capability contracts before any runtime can exist.' },
  control: { eyebrow: 'JINWOO NATIVE // ZERO SIDE EFFECT', title: 'Control & audit', description: 'Verify locks, capacity and local audit availability.' },
  settings: { eyebrow: 'LOCAL-FIRST // CONFIGURATION', title: 'Command settings', description: 'Provider visibility and delivery constraints.' },
}

const navigationGroups: Array<{ label: string; items: NavigationItem[] }> = [
  {
    label: 'COMMAND',
    items: [
      { id: 'hq', label: 'Army HQ', icon: '⌘' },
      { id: 'missions', label: 'Mission desk', icon: '◈' },
      { id: 'army', label: 'Army explorer', icon: '◫' },
      { id: 'core', label: 'Army core', icon: '⌬' },
      { id: 'chat', label: 'Command channel', icon: '✦' },
    ],
  },
  {
    label: 'GUARDRAILS',
    items: [
      { id: 'workspace', label: 'Workspace Guard', icon: '▣' },
      { id: 'research', label: 'Research Gate', icon: '◍' },
      { id: 'security', label: 'Security Gate', icon: '◐' },
      { id: 'memory', label: 'Memory Vault', icon: '◌' },
    ],
  },
  {
    label: 'SYSTEM',
    items: [
      { id: 'interaction', label: 'Interaction Lab', icon: '⌁' },
      { id: 'skills', label: 'Native skills', icon: '◈' },
      { id: 'registry', label: 'Frameworks & skills', icon: '✧' },
      { id: 'control', label: 'Control & audit', icon: '✓' },
      { id: 'settings', label: 'Settings', icon: '⚙' },
    ],
  },
]

interface ApiFrameworkStatus {
  id: string
  label: string
  runtime: FrameworkStatus['runtime']
  category: FrameworkStatus['category']
  integration_batch: number
  owner_commander: string
  license: string
  source_url?: string | null
  review_commit?: string | null
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

interface ApiWorkspaceSearch {
  query: string
  relative_path: string
  results: ApiWorkspaceEntry[]
  scanned_directories: number
  truncated: boolean
}


interface ApiShadowArmyFramework {
  id: string
  label: string
  category: string
  pattern_role: string
  implementation_status: string
  execution_enabled: boolean
}

interface ApiShadowArmyAgent {
  id: string
  name: string
  commander_id: string
  division_id: string
  division: string
  specialty: string
  logical: boolean
  runtime_started: boolean
}

interface ApiShadowArmyStage {
  id: string
  label: string
  owner: string
  phase: 'intake' | 'route' | 'scope' | 'plan' | 'draft' | 'verify' | 'deliver'
  detail: string
  requires_approval: boolean
}

interface ApiShadowArmyOverview {
  commanders: number
  divisions: number
  logical_agents: number
  worker_slots: number
  active_runtime_workers: number
  runtime_cap_per_mission: number
  all_external_runtimes_disabled: boolean
  hierarchy: string[]
  supported_patterns: CoordinationPattern[]
}

interface ApiShadowArmyPlan {
  id: string
  prompt: string
  coordination: CoordinationPattern
  commander_id: string
  commander: string
  division_id: string
  division: string
  requested_logical_agents: number
  logical_agents_reserved: number
  displayed_logical_agents: number
  runtime_worker_cap: number
  runtime_workers_started: number
  risk: ShadowArmyPlan['risk']
  requires_approval: boolean
  external_runtime_invoked: boolean
  pattern_summary: string
  agents: ApiShadowArmyAgent[]
  stages: ApiShadowArmyStage[]
  frameworks: ApiShadowArmyFramework[]
  guardrails: string[]
  created_at: string
}

interface ApiSkillActivationResponse {
  skill: NativeSkillSummary
  changed: boolean
  detail: string
  external_runtime_invoked: boolean
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


const shadowArmyOverviewFromApi = (overview: ApiShadowArmyOverview): ShadowArmyOverview => ({
  commanders: overview.commanders,
  divisions: overview.divisions,
  logicalAgents: overview.logical_agents,
  workerSlots: overview.worker_slots,
  activeRuntimeWorkers: overview.active_runtime_workers,
  runtimeCapPerMission: overview.runtime_cap_per_mission,
  allExternalRuntimesDisabled: overview.all_external_runtimes_disabled,
  hierarchy: overview.hierarchy,
  supportedPatterns: overview.supported_patterns,
})

const shadowArmyPlanFromApi = (plan: ApiShadowArmyPlan): ShadowArmyPlan => ({
  id: plan.id,
  prompt: plan.prompt,
  coordination: plan.coordination,
  commanderId: plan.commander_id,
  commander: plan.commander,
  divisionId: plan.division_id,
  division: plan.division,
  requestedLogicalAgents: plan.requested_logical_agents,
  logicalAgentsReserved: plan.logical_agents_reserved,
  displayedLogicalAgents: plan.displayed_logical_agents,
  runtimeWorkerCap: plan.runtime_worker_cap,
  runtimeWorkersStarted: plan.runtime_workers_started,
  risk: plan.risk,
  requiresApproval: plan.requires_approval,
  externalRuntimeInvoked: plan.external_runtime_invoked,
  patternSummary: plan.pattern_summary,
  agents: plan.agents.map((agent) => ({
    id: agent.id,
    name: agent.name,
    commanderId: agent.commander_id,
    divisionId: agent.division_id,
    division: agent.division,
    specialty: agent.specialty,
    logical: agent.logical,
    runtimeStarted: agent.runtime_started,
  })),
  stages: plan.stages.map((stage) => ({
    id: stage.id,
    label: stage.label,
    owner: stage.owner,
    phase: stage.phase,
    detail: stage.detail,
    requiresApproval: stage.requires_approval,
  })),
  frameworks: plan.frameworks.map((framework) => ({
    id: framework.id,
    label: framework.label,
    category: framework.category,
    patternRole: framework.pattern_role,
    implementationStatus: framework.implementation_status,
    executionEnabled: framework.execution_enabled,
  })),
  guardrails: plan.guardrails,
  createdAt: plan.created_at,
})

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

const workspaceSearchFromApi = (search: ApiWorkspaceSearch): WorkspaceSearch => ({
  query: search.query,
  relativePath: search.relative_path,
  results: search.results.map(workspaceEntryFromApi),
  scannedDirectories: search.scanned_directories,
  truncated: search.truncated,
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
  sourceUrl: framework.source_url ?? undefined,
  reviewCommit: framework.review_commit ?? undefined,
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
  // Surface the latest owner-prioritised native core first; Army HQ remains one tap away.
  const [activeView, setActiveView] = useState<ViewId>('core')
  const [navigationOpen, setNavigationOpen] = useState(false)
  const [now, setNow] = useState(() => new Date())
  const [selectedCommander, setSelectedCommander] = useState<Commander>(commanders[0])
  const [mission, setMission] = useState<Mission | null>(null)
  const [prompt, setPrompt] = useState('')
  const [providers, setProviders] = useState<ProviderStatus[]>(defaultProviders)
  const [frameworks, setFrameworks] = useState<FrameworkStatus[]>(defaultFrameworks)
  const [frameworkDryRun, setFrameworkDryRun] = useState<FrameworkDryRun | null>(null)
  const [frameworkBusy, setFrameworkBusy] = useState(false)
  const [shadowOverview, setShadowOverview] = useState<ShadowArmyOverview | null>(null)
  const [shadowPlan, setShadowPlan] = useState<ShadowArmyPlan | null>(null)
  const [shadowBusy, setShadowBusy] = useState(false)
  const [nativeSkillLibrary, setNativeSkillLibrary] = useState<NativeSkillLibraryData | null>(null)
  const [nativeSkillPlans, setNativeSkillPlans] = useState<NativeSkillPlan[]>([])
  const [nativeSkillDetail, setNativeSkillDetail] = useState<NativeSkillDetail | null>(null)
  const [nativeSkillBusy, setNativeSkillBusy] = useState(false)
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
  const [workspaceSearch, setWorkspaceSearch] = useState<WorkspaceSearch | null>(null)
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

  const loadNativeSkillLibrary = async (announce = false): Promise<void> => {
    setNativeSkillBusy(true)
    try {
      const [libraryResponse, plansResponse] = await Promise.all([
        fetch('/api/skills'),
        fetch('/api/skill-orchestrator/plans'),
      ])
      const libraryPayload = await libraryResponse.json() as NativeSkillLibraryData | { detail?: string }
      const plansPayload = await plansResponse.json() as NativeSkillPlan[] | { detail?: string }
      if (!libraryResponse.ok || !('skills' in libraryPayload) || !Array.isArray(libraryPayload.skills)) {
        if (announce) setNotice(errorDetail(libraryPayload, 'The native skill library could not be refreshed.'))
        return
      }
      setNativeSkillLibrary(libraryPayload)
      if (plansResponse.ok && Array.isArray(plansPayload)) setNativeSkillPlans(plansPayload)
      if (announce) setNotice(`${libraryPayload.skills.length} Jinwoo-owned planning skills refreshed locally. No external runtime was invoked.`)
    } catch {
      if (announce) setNotice('The native skill library is unavailable because the local backend is offline.')
    } finally {
      setNativeSkillBusy(false)
    }
  }

  const inspectNativeSkill = async (skillId: string): Promise<void> => {
    setNativeSkillBusy(true)
    try {
      const response = await fetch(`/api/skills/${encodeURIComponent(skillId)}`)
      const payload = await response.json() as NativeSkillDetail | { detail?: string }
      if (!response.ok || !('instructions' in payload)) {
        setNotice(errorDetail(payload, 'That native SKILL.md could not be opened.'))
        return
      }
      setNativeSkillDetail(payload)
      setNotice(`Opened the local ${payload.skill_path} instruction. No upstream source or runtime was opened.`)
    } catch {
      setNotice('The native skill instruction is unavailable because the local backend is offline.')
    } finally {
      setNativeSkillBusy(false)
    }
  }

  const setNativeSkillAvailability = async (skillId: string, enabled: boolean): Promise<boolean> => {
    setNativeSkillBusy(true)
    try {
      const response = await fetch(`/api/skills/${encodeURIComponent(skillId)}/activation`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      })
      const payload = await response.json() as ApiSkillActivationResponse | { detail?: string }
      if (!response.ok || !('skill' in payload)) {
        setNotice(errorDetail(payload, 'Native skill availability could not be changed.'))
        return false
      }
      setNativeSkillLibrary((current) => current ? {
        ...current,
        skills: current.skills.map((skill) => skill.id === skillId ? payload.skill : skill),
      } : current)
      setNativeSkillDetail((current) => current?.id === skillId ? { ...current, ...payload.skill } : current)
      void loadAudit()
      setNotice(payload.detail)
      return true
    } catch {
      setNotice('Native skill availability is unavailable because the local backend is offline.')
      return false
    } finally {
      setNativeSkillBusy(false)
    }
  }

  const createNativeSkillPlan = async (objective: string, skillIds: string[], controllerInstruction?: string): Promise<boolean> => {
    setNativeSkillBusy(true)
    try {
      const response = await fetch('/api/skill-orchestrator/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objective, skill_ids: skillIds, controller_instruction: controllerInstruction }),
      })
      const payload = await response.json() as NativeSkillPlan | { detail?: string }
      if (!response.ok || !('id' in payload)) {
        setNotice(errorDetail(payload, 'The Master Orchestrator could not prepare that native skill plan.'))
        return false
      }
      setNativeSkillPlans((current) => [payload, ...current.filter((plan) => plan.id !== payload.id)])
      void loadAudit()
      setNotice(`Jinwoo prepared a ${payload.policy_outcome} skill plan with ${payload.selected_skill_ids.length} native skills. No worker was started.`)
      return true
    } catch {
      setNotice('The Master Orchestrator is unavailable because the local backend is offline.')
      return false
    } finally {
      setNativeSkillBusy(false)
    }
  }

  const applyNativeSkillDirective = async (
    planId: string,
    action: 'pause' | 'resume' | 'terminate' | 'rewrite-instructions',
    controllerInstruction?: string,
  ): Promise<boolean> => {
    setNativeSkillBusy(true)
    try {
      const response = await fetch(`/api/skill-orchestrator/plans/${encodeURIComponent(planId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, controller_instruction: controllerInstruction }),
      })
      const payload = await response.json() as NativeSkillPlan | { detail?: string }
      if (!response.ok || !('id' in payload)) {
        setNotice(errorDetail(payload, 'The Master Orchestrator could not apply that local plan directive.'))
        return false
      }
      setNativeSkillPlans((current) => [payload, ...current.filter((plan) => plan.id !== payload.id)])
      void loadAudit()
      setNotice(`Jinwoo ${action.replaceAll('-', ' ')} for a local skill plan. No skill or external runtime was executed.`)
      return true
    } catch {
      setNotice('The Master Orchestrator directive is unavailable because the local backend is offline.')
      return false
    } finally {
      setNativeSkillBusy(false)
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


  const createShadowArmyPlan = async (
    message: string,
    requestedLogicalAgents: number,
    coordination: CoordinationPattern,
  ): Promise<boolean> => {
    const clean = message.trim()
    if (isBlockedPrompt(clean)) {
      setNotice('This request crosses a security or privacy boundary, so Jinwoo did not create an Army topology.')
      return false
    }

    setShadowBusy(true)
    try {
      const response = await fetch('/api/shadow-army/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: clean,
          requested_logical_agents: requestedLogicalAgents,
          coordination,
        }),
      })
      const payload = await response.json() as ApiShadowArmyPlan | { detail?: string }
      if (!response.ok || !('id' in payload)) {
        setNotice(errorDetail(payload, 'Bellion could not prepare that bounded Army topology.'))
        return false
      }
      const nextPlan = shadowArmyPlanFromApi(payload)
      setShadowPlan(nextPlan)
      const commander = commanders.find((item) => item.id === nextPlan.commanderId)
      if (commander) setSelectedCommander(commander)
      void loadAudit()
      setNotice(`${nextPlan.commander} prepared a ${nextPlan.coordination.replaceAll('-', ' ')} topology. No external agent runtime was invoked.`)
      return true
    } catch {
      setNotice('The Shadow Army core is unavailable because the local backend is offline.')
      return false
    } finally {
      setShadowBusy(false)
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
        setWorkspaceSearch(null)
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

  const searchWorkspace = async (query: string, relativePath: string) => {
    setWorkspaceBusy(true)
    try {
      const response = await fetch('/api/workspace/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, relative_path: relativePath, max_results: 50 }),
      })
      const payload = await response.json() as ApiWorkspaceSearch | { detail?: string }
      if (!response.ok || !('results' in payload)) {
        setNotice(errorDetail(payload, 'Igris could not complete that filename search.'))
        return
      }
      setWorkspaceSearch(workspaceSearchFromApi(payload))
      setNotice('Igris completed a bounded filename-only search. No file content was read and the search term was not added to audit logs.')
    } catch {
      setNotice('Workspace search is unavailable because the local backend is offline.')
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
      setWorkspaceSearch(null)
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
      setWorkspaceSearch(null)
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
    const timer = window.setInterval(() => setNow(new Date()), 30_000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    void loadMemories()
    void loadAudit()
    void loadWorkspace()
  }, [])

  useEffect(() => {
    let mounted = true
    void loadNativeSkillLibrary()
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
    fetch('/api/shadow-army/overview')
      .then(async (response) => response.ok ? response.json() : Promise.reject(new Error('Shadow Army core unavailable')))
      .then((payload: ApiShadowArmyOverview) => {
        if (mounted && payload && Array.isArray(payload.supported_patterns)) {
          setShadowOverview(shadowArmyOverviewFromApi(payload))
        }
      })
      .catch(() => {
        // ShadowArmyCore provides a deterministic, no-runtime fallback for standalone UI previews.
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

  const navigate = (view: ViewId) => {
    setActiveView(view)
    setNavigationOpen(false)
  }

  return (
    <div className={`app-shell ${navigationOpen ? 'app-shell--nav-open' : ''}`}>
      {navigationOpen && <button className="mobile-nav-backdrop" type="button" aria-label="Close navigation" onClick={() => setNavigationOpen(false)} />}
      <aside className="sidebar" id="primary-navigation">
        <div className="sidebar__header">
          <div className="brand">
            <span className="brand-mark">♛</span>
            <span><b>JINWOO</b><small>SHADOW ARMY</small></span>
          </div>
          <button className="sidebar__close" type="button" onClick={() => setNavigationOpen(false)} aria-label="Close navigation">×</button>
        </div>
        <nav className="sidebar-nav" aria-label="Primary navigation">
          {navigationGroups.map((group) => (
            <div className="nav-group" key={group.label}>
              <p>{group.label}</p>
              {group.items.map((item) => (
                <button
                  className={activeView === item.id ? 'nav-item nav-item--active' : 'nav-item'}
                  type="button"
                  onClick={() => navigate(item.id)}
                  aria-current={activeView === item.id ? 'page' : undefined}
                  key={item.id}
                >
                  <span>{item.icon}</span>{item.label}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-status">
          <span className="signal-dot" />
          <div><b>LOCAL MODE</b><small>Private by default · approval gated</small></div>
        </div>
        <p className="sidebar-foot">External tools, cameras, device control and workspace writes stay disabled until separately reviewed.</p>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="topbar__title">
            <button className="menu-toggle" type="button" aria-controls="primary-navigation" aria-expanded={navigationOpen} onClick={() => setNavigationOpen(true)} aria-label="Open navigation">☰</button>
            <div>
              <p className="eyebrow">{viewMeta[activeView].eyebrow}</p>
              <strong>{viewMeta[activeView].title}</strong>
              <small>{viewMeta[activeView].description}</small>
            </div>
          </div>
          <div className="topbar-actions">
            <time className="command-clock" dateTime={now.toISOString()}>{now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
            <span className="mode-indicator"><i /> LOCAL-FIRST</span>
            <button type="button" className="avatar-button" aria-label="Open command settings" onClick={() => navigate('settings')}>J</button>
          </div>
        </header>

        <section className="command-bar panel" aria-label="Mission command bar">
          <div className="command-bar__icon">✦</div>
          <form onSubmit={submitPrompt}>
            <label htmlFor="command">Give the army an order</label>
            <input id="command" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Example: analyze my project and make a safe fix plan" />
          </form>
          <span className="command-bar__safety">Plan first</span>
          <button className="button command-bar__button" type="button" onClick={() => { void dispatchMission(prompt) }}>Deploy <span>↗</span></button>
        </section>

        <div className="notice" role="status" aria-live="polite"><span className="status-dot status-dot--ready" /><span>{notice}</span><small>No external runtime invoked by this interface.</small></div>

        <section className="view-transition" aria-label={`${viewMeta[activeView].title} content`}>
          {activeView === 'hq' && (
            <ArmyHQ
              stats={stats}
              selectedCommander={selectedCommander}
              mission={mission}
              onSelectCommander={selectCommander}
              onOpenMission={() => navigate('missions')}
              onOpenArmy={() => navigate('army')}
              onOpenInteraction={() => navigate('interaction')}
            />
          )}

          {activeView === 'missions' && (
            <div className="mission-layout">
              <MissionPanel mission={mission} selectedCommander={selectedCommander} onApprove={() => { void transitionMission('approve') }} onCancel={() => { void transitionMission('cancel') }} />
              <aside className="side-stack">
                <section className="panel mission-safety-card">
                  <p className="eyebrow">MISSION SAFETY</p>
                  <h2>Visible work only</h2>
                  <p>Planner, Executor and Verifier roles are capped at three proposed workers. Approval never silently starts an optional framework, shell, browser or device tool.</p>
                  <button className="button button--ghost" type="button" onClick={() => navigate('control')}>Open control review</button>
                </section>
                <ProviderPanel providers={providers} />
                <AuditTrail events={auditEvents} missionId={mission?.id} />
                <section className="panel quick-panel"><p className="eyebrow">QUICK MISSIONS</p><h2>Try a safe request</h2>{starterPrompts.map((item) => <button type="button" onClick={() => { void dispatchMission(item) }} key={item}>{item}<span>↗</span></button>)}</section>
              </aside>
            </div>
          )}

          {activeView === 'army' && <ArmyExplorer selectedCommander={selectedCommander} onSelectCommander={selectCommander} />}

          {activeView === 'core' && <ShadowArmyCore overview={shadowOverview} plan={shadowPlan} busy={shadowBusy} onPlan={createShadowArmyPlan} />}

          {activeView === 'chat' && <ChatPanel messages={chatMessages} providers={providers} busy={chatBusy} onSend={sendChat} />}

          {activeView === 'workspace' && (
            <div className="guardrail-layout">
              <WorkspacePanel status={workspaceStatus} entries={workspaceEntries} analysis={workspaceAnalysis} search={workspaceSearch} busy={workspaceBusy} onSelect={selectWorkspace} onClear={clearWorkspace} onBrowse={browseWorkspace} onSearch={searchWorkspace} onAnalyze={analyzeWorkspaceFile} />
              <aside className="side-stack">
                <section className="panel boundary-card">
                  <p className="eyebrow">WORKSPACE BOUNDARY</p>
                  <h2>Igris reads, never writes.</h2>
                  <p>Selecting a folder enables bounded diagnostics only. Patch, terminal, Git, test and dependency actions remain separate future approvals.</p>
                  <div className="boundary-card__list"><span>Path escape protected</span><span>Regular files only</span><span>No automatic changes</span></div>
                </section>
                <AuditTrail events={auditEvents} />
              </aside>
            </div>
          )}

          {activeView === 'research' && <ResearchPanel plan={researchPlan} busy={researchBusy} onPlan={createResearchPlan} />}

          {activeView === 'security' && (
            <div className="security-layout">
              <SecurityScanPanel workspace={workspaceStatus} plan={securityScanPlan} busy={securityScanBusy} onPlan={createSecurityScanPlan} />
              <aside className="side-stack">
                <section className="panel boundary-card boundary-card--guarded">
                  <p className="eyebrow">DEFENSIVE POSTURE ONLY</p>
                  <h2>No scan means no scan.</h2>
                  <p>This gate makes a bounded review plan. It does not enumerate targets, read files, scan Git history, validate credentials or contact any system.</p>
                  <div className="boundary-card__list"><span>Authorisation required</span><span>Findings stay masked</span><span>No network verification</span></div>
                </section>
                <AuditTrail events={auditEvents} />
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

          {activeView === 'interaction' && <InteractionLab frameworks={frameworks} onOpenRegistry={() => navigate('registry')} />}

          {activeView === 'skills' && (
            <NativeSkillLibraryPanel
              library={nativeSkillLibrary}
              plans={nativeSkillPlans}
              detail={nativeSkillDetail}
              busy={nativeSkillBusy}
              onRefresh={() => loadNativeSkillLibrary(true)}
              onInspect={inspectNativeSkill}
              onSetAvailability={setNativeSkillAvailability}
              onCreatePlan={createNativeSkillPlan}
              onDirective={applyNativeSkillDirective}
            />
          )}

          {activeView === 'registry' && (
            <>
              <SkillIntakePanel frameworks={frameworks} />
              <UpgradeReviewPanel frameworks={frameworks} />
              <div className="registry-layout">
                <FrameworkPanel frameworks={frameworks} dryRun={frameworkDryRun} busy={frameworkBusy} onDryRun={runFrameworkDryRun} />
                <aside className="side-stack">
                  <section className="panel registry-summary">
                    <p className="eyebrow">REGISTRY SUMMARY</p>
                    <h2>{frameworks.length} controlled lanes</h2>
                    <p>Presence in this list is not installation, permission or activation. Every external route remains under Jinwoo policy, approval, workspace and audit controls.</p>
                    <div className="registry-summary__counts">
                      <span><b>{frameworks.filter((framework) => framework.implementationStatus === 'contract-ready').length}</b> contract ready</span>
                      <span><b>{frameworks.filter((framework) => framework.implementationStatus === 'license-review-required').length}</b> licence gates</span>
                      <span><b>{frameworks.filter((framework) => framework.implementationStatus === 'source-review-required').length}</b> source intake</span>
                    </div>
                  </section>
                  <section className="panel boundary-card">
                    <p className="eyebrow">ACTIVATION STANDARD</p>
                    <h2>One lane at a time.</h2>
                    <p>A future adapter needs a pinned version, source/licence review, typed contract, consent, workspace confinement, audit, offline tests and a disable path.</p>
                  </section>
                </aside>
              </div>
            </>
          )}

          {activeView === 'control' && (
            <div className="control-layout">
              <ControlReviewPanel review={controlReview} busy={controlReviewBusy} onRun={runControlReview} />
              <aside className="side-stack">
                <AuditTrail events={auditEvents} />
                <section className="panel boundary-card">
                  <p className="eyebrow">AUDIT PROMISE</p>
                  <h2>Record decisions, not secrets.</h2>
                  <p>The local audit trail retains redacted control metadata. It does not need to expose raw prompts, provider credentials, media, camera data or workspace contents.</p>
                </section>
              </aside>
            </div>
          )}

          {activeView === 'settings' && (
            <div className="settings-hub">
              <section className="panel settings-hub__hero">
                <div>
                  <p className="eyebrow">ROUTING POLICY</p>
                  <h1>Local first, cloud by choice.</h1>
                  <p>Jinwoo keeps the local mission engine, consent, workspace boundary and audit trail in command. Cloud providers remain per-request choices and optional frameworks stay non-executing until individually reviewed.</p>
                </div>
                <div className="settings-hub__actions">
                  <button className="button button--ghost" type="button" onClick={() => navigate('workspace')}>Open Workspace Guard</button>
                  <button className="button button--ghost" type="button" onClick={() => navigate('registry')}>Review registry</button>
                </div>
              </section>
              <div className="settings-hub__grid">
                <ProviderPanel providers={providers} />
                <section className="panel settings-card">
                  <p className="eyebrow">DELIVERY CONSTRAINTS</p>
                  <h2>Safe by architecture.</h2>
                  <p>Providers, adapters and future device lanes are designed to return proposals through the Jinwoo policy. No browser bundle stores cloud keys, and no optional tool can take control merely because it appears in the interface.</p>
                  <div className="settings-list"><span>Python FastAPI mission control</span><span>TypeScript command dashboard</span><span>SQLite consent-based memory</span><span>User-selected workspace confinement</span><span>Explicit cloud and action approval</span><span>External runtimes disabled by default</span></div>
                </section>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
