import type { ArmyStats, Commander, FrameworkStatus, ProviderStatus, SubDepartment, WorkerRole } from '../types/army'

const SUB_DEPARTMENTS_PER_COMMANDER = 3
const AGENTS_PER_SUB_DEPARTMENT = 10

const workerRoles: WorkerRole[] = [
  { id: 'planner', name: 'Planner', responsibility: 'Breaks work into visible, constrained steps.' },
  { id: 'executor', name: 'Executor', responsibility: 'Creates a result or proposes an approved action.' },
  { id: 'verifier', name: 'Verifier', responsibility: 'Checks evidence, quality and the safety policy.' },
]

type TeamSeed = readonly [name: string, focus: string]
type CommanderSeed = Omit<Commander, 'subDepartments'> & { teams: readonly TeamSeed[] }

const subDepartments = (commanderId: string, teams: readonly TeamSeed[]): SubDepartment[] =>
  teams.map(([name, focus], index) => ({ id: `${commanderId}-${index + 1}`, name, focus }))

const seeds: CommanderSeed[] = [
  {
    id: 'jinwoo', number: 1, name: 'Jinwoo', title: 'Shadow Monarch', department: 'Supreme Command', icon: '♛', color: '#f1d8ff', glow: 'rgba(173, 67, 255, .58)',
    description: 'Turns your request into a safe mission, explains progress and gives the final answer.', defaultSafety: 'no-direct-tools', status: 'ready', activeMission: 'Army coordination',
    teams: [['Mission Control', 'Mission boundaries, priority and final outcome'], ['Final Decision', 'Policy-aware final decisions'], ['User Interface Layer', 'Clear communication and mission visibility']],
  },
  {
    id: 'bellion', number: 2, name: 'Bellion', title: 'Grand Marshal', department: 'Controller', icon: '✦', color: '#d4e3ff', glow: 'rgba(87, 145, 255, .45)',
    description: 'Routes missions, protects the queue and keeps every department in formation.', defaultSafety: 'no-direct-tools', status: 'working', activeMission: 'Synchronising command flow',
    teams: [['Routing and Queue', 'Task intake, capacity and prioritisation'], ['Commander Coordination', 'Explicit hand-offs between departments'], ['Mission Monitoring', 'Progress, failure and recovery state']],
  },
  {
    id: 'igris', number: 3, name: 'Igris', title: 'Blood-Red Commander', department: 'Development', icon: '⚔', color: '#ffbac5', glow: 'rgba(255, 61, 90, .46)',
    description: 'Architecture, code reviews, fixes, test plans and approved patches.', defaultSafety: 'approval-required', status: 'ready',
    teams: [['Core Engine', 'Architecture, files, APIs and data contracts'], ['Intelligence Layer', 'Models, prompts, routing and evaluation'], ['Delivery and Safety', 'Tests, patches, performance and release quality']],
  },
  {
    id: 'beru', number: 4, name: 'Beru', title: 'Ant King', department: 'Managers', icon: '◈', color: '#ffe1a8', glow: 'rgba(251, 180, 65, .46)',
    description: 'Coordinates work, handles dependencies and keeps updates from getting lost.', defaultSafety: 'no-direct-tools', status: 'ready',
    teams: [['Task Distribution', 'Assigns the right agent template'], ['Workflow Management', 'Dependencies, owners and checkpoints'], ['Update and Maintenance', 'Change follow-up and issue triage']],
  },
  {
    id: 'tusk', number: 5, name: 'Tusk', title: 'High Orc Warlock', department: 'Features', icon: '✺', color: '#dda8ff', glow: 'rgba(193, 75, 255, .42)',
    description: 'UI concepts, animations, creative briefs, content drafts and feature proposals.', defaultSafety: 'approval-required', status: 'ready',
    teams: [['Creative Production', 'Original visual and content concepts'], ['Editing and Tools', 'Approved media editing workflows'], ['Agent Factory', 'New agent-template proposals']],
  },
  {
    id: 'iron', number: 6, name: 'Iron', title: 'Shield Bearer', department: 'Business', icon: '⬡', color: '#b6f3e1', glow: 'rgba(43, 221, 180, .42)',
    description: 'Business plans, MVP scopes, marketing drafts and growth experiments.', defaultSafety: 'approval-required', status: 'ready',
    teams: [['Business Planning', 'Business cases and pricing models'], ['Marketing and Growth', 'Campaign drafts and audience research'], ['MVP and Expansion', 'Scope, validation and roadmap proposals']],
  },
  {
    id: 'tank', number: 7, name: 'Tank', title: 'Ice Bear', department: 'Researchers', icon: '◉', color: '#a9d8ff', glow: 'rgba(56, 166, 255, .46)',
    description: 'Public-web research, approved APIs, data organisation and cited reports.', defaultSafety: 'read-only', status: 'working', activeMission: 'Scanning public sources',
    teams: [['Public Research', 'Authorised public sources and citations'], ['Data Extraction', 'Allowed APIs and user-provided documents'], ['Report Generation', 'Structured evidence-based reports']],
  },
  {
    id: 'kaisel', number: 8, name: 'Kaisel', title: 'Shadow Dragon', department: 'Upgrading', icon: '⌁', color: '#d6b2ff', glow: 'rgba(140, 76, 255, .42)',
    description: 'Finds upgrade candidates and prepares tested, reversible upgrade proposals.', defaultSafety: 'sandboxed', status: 'ready',
    teams: [['Tool Discovery', 'Candidate tool and dependency research'], ['Safe Integration', 'Sandbox, licence and compatibility checks'], ['Version Management', 'Upgrade, release and rollback plans']],
  },
  {
    id: 'jima', number: 9, name: 'Jima', title: 'Shadow Scribe', department: 'Scribes', icon: '✎', color: '#f6e7ca', glow: 'rgba(224, 190, 122, .35)',
    description: 'Writes mission reports, documentation, changelogs and knowledge-base entries.', defaultSafety: 'approval-required', status: 'ready',
    teams: [['Documentation', 'Technical and user-facing docs'], ['Knowledge Base', 'Approved, searchable project knowledge'], ['Report Writing', 'Mission outcomes and exportable reports']],
  },
  {
    id: 'greed', number: 10, name: 'Greed', title: 'Shadow Guardian', department: 'Security', icon: '◐', color: '#ffaec5', glow: 'rgba(255, 75, 134, .42)',
    description: 'Defensive privacy checks, secret hygiene and authorised security posture reports.', defaultSafety: 'sandboxed', status: 'guarded',
    teams: [['Privacy Guard', 'Local data boundary and privacy reviews'], ['Secret Scanner', 'Workspace secret-hygiene checks'], ['Policy Enforcer', 'Tool risk and approval verification']],
  },
  {
    id: 'shadow', number: 11, name: 'Shadow', title: 'Error Hunter', department: 'Quality Assurance', icon: '✓', color: '#bcf7cd', glow: 'rgba(72, 214, 113, .38)',
    description: 'Runs tests, catches regressions and checks mission acceptance criteria.', defaultSafety: 'read-only', status: 'ready',
    teams: [['Testing', 'Unit, integration and UI checks'], ['Bug Hunting', 'Failure reproduction and diagnosis'], ['Regression', 'Release confidence and change verification']],
  },
  {
    id: 'fang', number: 12, name: 'Fang', title: 'Link Phantom', department: 'Integration', icon: '⌘', color: '#b8c7ff', glow: 'rgba(114, 129, 255, .42)',
    description: 'Connects approved APIs, services and modules through explicit contracts.', defaultSafety: 'approval-required', status: 'ready',
    teams: [['API Linking', 'Provider schemas and health checks'], ['Service Connection', 'Local service boundaries and retries'], ['Module Integration', 'Typed interfaces and compatibility tests']],
  },
  {
    id: 'blades', number: 13, name: 'Blades', title: 'Mind Forger', department: 'Training', icon: '◒', color: '#eed0ff', glow: 'rgba(205, 107, 255, .38)',
    description: 'Creates evaluation sets, prompt experiments and model performance reports.', defaultSafety: 'sandboxed', status: 'ready',
    teams: [['Model Evaluation', 'Benchmarks and comparison reports'], ['Prompt Engineering', 'Versioned prompt experiments'], ['Agent Training', 'Approved local learning experiments']],
  },
  {
    id: 'nox', number: 14, name: 'Nox', title: 'Night Executor', department: 'Operations', icon: '◌', color: '#ccd5e8', glow: 'rgba(158, 180, 226, .35)',
    description: 'Manages opt-in schedules, local resources, task health and graceful recovery.', defaultSafety: 'approval-required', status: 'offline',
    teams: [['Scheduling', 'Explicit user-approved timing'], ['Resource Management', 'CPU, memory and queue controls'], ['Health Monitoring', 'Run health, alerts and recovery']],
  },
  {
    id: 'ashborn', number: 15, name: 'Ashborn', title: 'Future Specter', department: 'Innovation', icon: '✧', color: '#f2c2ff', glow: 'rgba(241, 106, 255, .45)',
    description: 'Explores new ideas in a sandbox and returns evidence-based prototypes.', defaultSafety: 'sandboxed', status: 'ready',
    teams: [['Experimentation', 'Safe proof-of-concept experiments'], ['Future Research', 'Emerging technology tracking'], ['Prototype Development', 'Sandboxed, reversible prototypes']],
  },
]

if (seeds.length !== 15 || seeds.some(({ teams }) => teams.length !== SUB_DEPARTMENTS_PER_COMMANDER)) {
  throw new Error('The Shadow Army must define 15 commanders with exactly three sub-departments each.')
}

export const commanders: Commander[] = seeds.map(({ teams, ...commander }) => ({
  ...commander,
  subDepartments: subDepartments(commander.id, teams),
}))

export const defaultProviders: ProviderStatus[] = [
  { id: 'ollama', label: 'Ollama', mode: 'local', state: 'ready', detail: 'Local-first route · demo ready' },
  { id: 'lm-studio', label: 'LM Studio', mode: 'local', state: 'unconfigured', detail: 'Optional local endpoint' },
  { id: 'claude', label: 'Claude', mode: 'cloud', state: 'unconfigured', detail: 'Secure key required' },
  { id: 'glm', label: 'GLM / Z.ai', mode: 'cloud', state: 'unconfigured', detail: 'Secure key required' },
  { id: 'hugging-face', label: 'Hugging Face', mode: 'cloud', state: 'unconfigured', detail: 'Inference / embeddings optional' },
  { id: 'mem0', label: 'Mem0', mode: 'memory', state: 'offline', detail: 'Optional memory sync · local fallback active' },
]

export const defaultFrameworks: FrameworkStatus[] = [
  {
    id: 'jinwoo-native',
    label: 'Jinwoo Native Engine',
    runtime: 'builtin',
    category: 'orchestration',
    integrationBatch: 0,
    ownerCommander: 'Jinwoo',
    license: 'Original project code',
    implementationStatus: 'active',
    state: 'canonical',
    executionEnabled: true,
    detail: 'Canonical mission engine; policy, approval, workspace and audit remain in command.',
  },
  {
    id: 'swarms',
    label: 'Swarms',
    runtime: 'python',
    category: 'orchestration',
    integrationBatch: 1,
    ownerCommander: 'Bellion',
    license: 'Apache-2.0',
    sourceUrl: 'https://github.com/kyegomez/swarms',
    implementationStatus: 'contract-ready',
    state: 'not-installed',
    executionEnabled: false,
    detail: 'Bounded hierarchical-worker adapter contract; upstream runtime remains disabled.',
  },
  {
    id: 'agency-swarm',
    label: 'Agency-Swarm',
    runtime: 'python',
    category: 'orchestration',
    integrationBatch: 1,
    ownerCommander: 'Beru',
    license: 'MIT',
    sourceUrl: 'https://github.com/VRSEN/agency-swarm',
    implementationStatus: 'contract-ready',
    state: 'not-installed',
    executionEnabled: false,
    detail: 'Policy-gated organisation-handoff adapter contract; upstream runtime remains disabled.',
  },
  {
    id: 'ruflo',
    label: 'Ruflo',
    runtime: 'typescript-mcp',
    category: 'orchestration',
    integrationBatch: 1,
    ownerCommander: 'Igris',
    license: 'MIT',
    sourceUrl: 'https://github.com/ruvnet/ruflo',
    implementationStatus: 'contract-ready',
    state: 'not-installed',
    executionEnabled: false,
    detail: 'Local TypeScript/MCP bridge contract; upstream runtime remains disabled.',
  },
  {
    id: 'langgraph',
    label: 'LangGraph',
    runtime: 'python',
    category: 'workflow',
    integrationBatch: 1,
    ownerCommander: 'Jinwoo',
    license: 'MIT',
    sourceUrl: 'https://github.com/langchain-ai/langgraph',
    implementationStatus: 'contract-ready',
    state: 'not-installed',
    executionEnabled: false,
    detail: 'Checkpointed state-workflow adapter contract; upstream runtime remains disabled.',
  },
  {
    id: 'crewai',
    label: 'CrewAI',
    runtime: 'python',
    category: 'orchestration',
    integrationBatch: 1,
    ownerCommander: 'Beru',
    license: 'MIT',
    sourceUrl: 'https://github.com/crewAIInc/crewAI',
    implementationStatus: 'contract-ready',
    state: 'not-installed',
    executionEnabled: false,
    detail: 'Bounded role-crew adapter contract; upstream runtime remains disabled.',
  },
]

export const buildArmyStats = (activeWorkers = 3): ArmyStats => ({
  departments: commanders.length,
  subDepartments: commanders.length * SUB_DEPARTMENTS_PER_COMMANDER,
  logicalAgents: commanders.length * SUB_DEPARTMENTS_PER_COMMANDER * AGENTS_PER_SUB_DEPARTMENT,
  workerSlots: commanders.length * SUB_DEPARTMENTS_PER_COMMANDER * AGENTS_PER_SUB_DEPARTMENT * workerRoles.length,
  activeWorkers,
})

export { workerRoles }
