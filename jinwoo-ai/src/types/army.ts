export type SafetyLevel = 'read-only' | 'approval-required' | 'sandboxed' | 'no-direct-tools'

export type DepartmentStatus = 'ready' | 'working' | 'offline' | 'guarded'

export interface WorkerRole {
  id: 'planner' | 'executor' | 'verifier'
  name: string
  responsibility: string
}

export interface SubDepartment {
  id: string
  name: string
  focus: string
}

export interface Commander {
  id: string
  number: number
  name: string
  title: string
  department: string
  icon: string
  color: string
  glow: string
  description: string
  defaultSafety: SafetyLevel
  status: DepartmentStatus
  activeMission?: string
  subDepartments: SubDepartment[]
}

export interface Mission {
  id: string
  prompt: string
  commanderId: string
  commander: string
  status: 'planned' | 'awaiting_approval' | 'running' | 'complete' | 'cancelled'
  risk: 'low' | 'medium' | 'high'
  requiresApproval: boolean
  createdAt: string
  steps: string[]
  workers: WorkerRole[]
  result?: string
}

export interface ProviderStatus {
  id: string
  label: string
  mode: 'local' | 'cloud' | 'memory'
  state: 'ready' | 'unconfigured' | 'offline' | 'checking'
  detail: string
}

export interface FrameworkStatus {
  id: string
  label: string
  runtime: 'builtin' | 'python' | 'typescript-mcp' | 'typescript-service' | 'container-sidecar' | 'go-cli' | 'go-service' | 'rust-cli' | 'desktop-client' | 'mobile-client' | 'skill-catalog'
  category: 'orchestration' | 'workflow' | 'coding' | 'research' | 'web-collection' | 'memory' | 'automation' | 'security' | 'governance' | 'computer-use' | 'reference' | 'media'
  integrationBatch: number
  ownerCommander: string
  license: string
  sourceUrl?: string
  state: 'canonical' | 'not-installed' | 'detected' | 'reference-only'
  implementationStatus: 'active' | 'contract-ready' | 'license-review-required' | 'source-review-required' | 'reference-only' | 'archived-upstream' | 'queued'
  executionEnabled: boolean
  capabilities?: string[]
  activationBoundary?: 'read-only' | 'approval-required' | 'sandboxed' | 'reference-only'
  detail: string
}

export interface FrameworkDryRun {
  frameworkId: string
  frameworkLabel: string
  policyOutcome: 'safe-plan' | 'approval-required' | 'blocked'
  requestedAgents: number
  boundedRuntimeWorkers: number
  externalRuntimeInvoked: boolean
  requiresApproval: boolean
  summary: string
  nextSteps: string[]
}

export interface ControlReviewCheck {
  id: string
  label: string
  passed: boolean
  detail: string
}

export interface ControlReview {
  reviewedAt: string
  allPassed: boolean
  externalRuntimeInvoked: boolean
  summary: string
  checks: ControlReviewCheck[]
}

export interface SecurityScanPlan {
  scannerId: 'trufflehog' | 'gitleaks'
  scannerLabel: string
  workspaceConfigured: boolean
  licenseReviewRequired: boolean
  externalScanStarted: boolean
  requiresApprovalForScan: boolean
  safeguards: string[]
  nextSteps: string[]
}

export interface ResearchTarget {
  url: string
  hostname: string
}

export interface ResearchPlan {
  frameworkId: 'firecrawl' | 'firecrawl-web-agent' | 'crawl4ai'
  topic: string
  targets: ResearchTarget[]
  externalFetchStarted: boolean
  requiresApprovalForFetch: boolean
  safeguards: string[]
  nextSteps: string[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  provider?: string
  localOnly?: boolean
}

export interface AuditEvent {
  id: number
  eventType: string
  missionId?: string
  actor: string
  detail: string
  createdAt: string
}

export interface WorkspaceStatus {
  configured: boolean
  rootLabel?: string
  readOnly: boolean
  detail: string
}

export interface WorkspaceEntry {
  name: string
  relativePath: string
  kind: 'file' | 'directory'
  sizeBytes?: number
}

export interface WorkspaceAnalysis {
  relativePath: string
  language: string
  sizeBytes: number
  lineCount: number
  todoCount: number
  fixmeCount: number
  importCount: number
  symbolCount: number
  sha256: string
  truncated: boolean
}

export type MemoryKind = 'preference' | 'project' | 'note' | 'reminder'

export interface MemoryItem {
  id: number
  content: string
  kind: MemoryKind
  createdAt: string
}

export type CoordinationPattern = 'hierarchical' | 'commander-council' | 'dependency-graph' | 'bounded-swarm'

export interface ShadowArmyFramework {
  id: string
  label: string
  category: string
  patternRole: string
  implementationStatus: string
  executionEnabled: boolean
}

export interface ShadowArmyAgent {
  id: string
  name: string
  commanderId: string
  divisionId: string
  division: string
  specialty: string
  logical: boolean
  runtimeStarted: boolean
}

export interface ShadowArmyStage {
  id: string
  label: string
  owner: string
  phase: 'intake' | 'route' | 'scope' | 'plan' | 'draft' | 'verify' | 'deliver'
  detail: string
  requiresApproval: boolean
}

export interface ShadowArmyPlan {
  id: string
  prompt: string
  coordination: CoordinationPattern
  commanderId: string
  commander: string
  divisionId: string
  division: string
  requestedLogicalAgents: number
  logicalAgentsReserved: number
  displayedLogicalAgents: number
  runtimeWorkerCap: number
  runtimeWorkersStarted: number
  risk: Mission['risk']
  requiresApproval: boolean
  externalRuntimeInvoked: boolean
  patternSummary: string
  agents: ShadowArmyAgent[]
  stages: ShadowArmyStage[]
  frameworks: ShadowArmyFramework[]
  guardrails: string[]
  createdAt: string
}

export interface ShadowArmyOverview {
  commanders: number
  divisions: number
  logicalAgents: number
  workerSlots: number
  activeRuntimeWorkers: number
  runtimeCapPerMission: number
  allExternalRuntimesDisabled: boolean
  hierarchy: string[]
  supportedPatterns: CoordinationPattern[]
}

export interface ArmyStats {
  departments: number
  subDepartments: number
  logicalAgents: number
  workerSlots: number
  activeWorkers: number
}
