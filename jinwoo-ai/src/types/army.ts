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
  runtime: 'builtin' | 'python' | 'typescript-mcp'
  state: 'canonical' | 'not-installed' | 'detected'
  executionEnabled: boolean
  detail: string
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

export type MemoryKind = 'preference' | 'project' | 'note' | 'reminder'

export interface MemoryItem {
  id: number
  content: string
  kind: MemoryKind
  createdAt: string
}

export interface ArmyStats {
  departments: number
  subDepartments: number
  logicalAgents: number
  workerSlots: number
  activeWorkers: number
}
