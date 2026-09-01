import { commanders, workerRoles } from '../data/army'
import type { Commander, Mission } from '../types/army'

const routes: Array<{ commanderId: string; terms: string[] }> = [
  { commanderId: 'igris', terms: ['code', 'bug', 'react', 'next', 'python', 'api', 'build', 'test', 'database', 'app'] },
  { commanderId: 'tank', terms: ['research', 'search', 'report', 'data', 'market', 'compare', 'analysis'] },
  { commanderId: 'greed', terms: ['security', 'secret', 'privacy', 'vulnerability', 'password', 'encrypt'] },
  { commanderId: 'tusk', terms: ['ui', 'design', 'animation', 'image', 'video', 'feature', 'creative'] },
  { commanderId: 'iron', terms: ['business', 'marketing', 'campaign', 'mvp', 'brand', 'sales'] },
  { commanderId: 'jima', terms: ['document', 'docs', 'write', 'proposal', 'summary', 'changelog'] },
  { commanderId: 'shadow', terms: ['quality', 'qa', 'verify', 'validate', 'regression'] },
  { commanderId: 'fang', terms: ['integrate', 'integration', 'connect', 'webhook', 'service'] },
  { commanderId: 'kaisel', terms: ['upgrade', 'dependency', 'repository', 'repo', 'improve'] },
  { commanderId: 'nox', terms: ['schedule', 'monitor', 'operation', 'resource', 'daily'] },
]

const approvalTerms = ['delete', 'remove', 'overwrite', 'write file', 'run ', 'terminal', 'install', 'uninstall', 'send ', 'publish', 'upload', 'payment', 'mouse', 'keyboard']
const blockedTerms = ['bypass password', 'bypass pin', 'steal password', 'steal credential', 'keylogger', 'hidden recording', 'spyware', 'disable antivirus']

export const isBlockedPrompt = (prompt: string) => {
  const normalized = prompt.toLowerCase()
  return blockedTerms.some((term) => normalized.includes(term))
}

export const selectCommander = (prompt: string): Commander => {
  const normalized = prompt.toLowerCase()
  const route = routes.find(({ terms }) => terms.some((term) => normalized.includes(term)))
  return commanders.find((commander) => commander.id === route?.commanderId) ?? commanders[1]
}

export const buildMission = (prompt: string): Mission => {
  const commander = selectCommander(prompt)
  const normalized = prompt.toLowerCase()
  const requiresApproval = approvalTerms.some((term) => normalized.includes(term))
  const risk = requiresApproval ? 'high' : commander.defaultSafety === 'sandboxed' ? 'medium' : 'low'

  return {
    id: `mission-${Date.now()}`,
    prompt,
    commanderId: commander.id,
    commander: commander.name,
    status: requiresApproval ? 'awaiting_approval' : 'planned',
    risk,
    requiresApproval,
    createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    workers: workerRoles,
    steps: [
      `${commander.name} receives the mission and defines its boundary.`,
      'Planner creates a visible, constrained execution plan.',
      requiresApproval ? 'Await explicit approval before any impactful action.' : 'Executor prepares a safe draft or read-only result.',
      'Verifier checks quality, evidence and policy before final delivery.',
    ],
  }
}
