export interface UpgradeReviewEntry {
  sequence: number
  frameworkId: string
  repository: string
  revision: string
  licenceSignal: string
  upgradeTarget: string
  categories: string[]
  sourceUrl: string
  note: string
}

// Batch 12 is a bounded, metadata-only discovery pass. A revision records the
// public default-branch ref observed during review; it is not source approval,
// dependency approval, a licence conclusion or an activation instruction.
export const batchTwelveUpgradeReview: UpgradeReviewEntry[] = [
  {
    sequence: 1,
    frameworkId: 'markitdown-upgrade-intake',
    repository: 'microsoft/markitdown',
    revision: '20d06b6c8508f86bfae3252a979a661a14306287',
    licenceSignal: 'GitHub metadata: MIT',
    upgradeTarget: 'Selected-workspace document intake boundary',
    categories: ['Document boundary', 'Format planning', 'Retention'],
    sourceUrl: 'https://github.com/microsoft/markitdown',
    note: 'No converter, parser, OCR route, document read or output retention is enabled.',
  },
  {
    sequence: 2,
    frameworkId: 'graphrag-upgrade-intake',
    repository: 'microsoft/graphrag',
    revision: 'f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704',
    licenceSignal: 'GitHub metadata: MIT',
    upgradeTarget: 'Local knowledge-map and retrieval boundary',
    categories: ['Knowledge map', 'Retrieval boundary', 'Data minimisation'],
    sourceUrl: 'https://github.com/microsoft/graphrag',
    note: 'No corpus, graph, index, embedding, model or provider route is created.',
  },
  {
    sequence: 3,
    frameworkId: 'litellm-upgrade-intake',
    repository: 'BerriAI/litellm',
    revision: '22cc97fe0a27367d19fdb03a16dbfd497f4360e8',
    licenceSignal: 'GitHub metadata: NOASSERTION',
    upgradeTarget: 'Provider-routing boundary comparison',
    categories: ['Provider consent', 'Routing policy', 'Credentials'],
    sourceUrl: 'https://github.com/BerriAI/litellm',
    note: 'Reference only: no gateway, API key, fallback, proxy, provider request or telemetry is enabled.',
  },
  {
    sequence: 4,
    frameworkId: 'opa-upgrade-intake',
    repository: 'open-policy-agent/opa',
    revision: '25a1d928d6ff43000c428ccfc1970d54afb5494b',
    licenceSignal: 'GitHub metadata: Apache-2.0',
    upgradeTarget: 'Policy-rule and approval-model comparison',
    categories: ['Policy rules', 'Decision audit', 'Approvals'],
    sourceUrl: 'https://github.com/open-policy-agent/opa',
    note: 'No policy engine or bundle runs, and Jinwoo remains the canonical controller.',
  },
  {
    sequence: 5,
    frameworkId: 'lancedb-upgrade-intake',
    repository: 'lancedb/lancedb',
    revision: '2779b75d0d0252a324bc39ab73c9132d3b212484',
    licenceSignal: 'GitHub metadata: Apache-2.0',
    upgradeTarget: 'Opt-in local retrieval and retention design',
    categories: ['Local retrieval', 'Retention', 'Memory boundary'],
    sourceUrl: 'https://github.com/lancedb/lancedb',
    note: 'No database, index, embedding, source file or Memory Vault record is created.',
  },
  {
    sequence: 6,
    frameworkId: 'promptfoo-upgrade-intake',
    repository: 'promptfoo/promptfoo',
    revision: '48a71cd0163b01ba8efb2954eb0165dd810a6c6e',
    licenceSignal: 'GitHub metadata: MIT',
    upgradeTarget: 'Defensive local evaluation-plan design',
    categories: ['Evaluation plan', 'Defensive testing', 'Evidence'],
    sourceUrl: 'https://github.com/promptfoo/promptfoo',
    note: 'No evaluator, provider request, third-party target, adversarial payload or report is run.',
  },
  {
    sequence: 7,
    frameworkId: 'ruff-upgrade-intake',
    repository: 'astral-sh/ruff',
    revision: '849bc61d7aea53bf7ded094973b176eb607fe3e5',
    licenceSignal: 'GitHub metadata: MIT',
    upgradeTarget: 'Local lint and format review planning',
    categories: ['Lint policy', 'Formatting impact', 'Quality gate'],
    sourceUrl: 'https://github.com/astral-sh/ruff',
    note: 'No binary is installed; no workspace code is scanned, rewritten or formatted.',
  },
  {
    sequence: 8,
    frameworkId: 'syft-upgrade-intake',
    repository: 'anchore/syft',
    revision: '77031752faf6810edf6d57c8ba798408796ea283',
    licenceSignal: 'GitHub metadata: Apache-2.0',
    upgradeTarget: 'Approved SBOM preflight design',
    categories: ['SBOM boundary', 'Supply chain', 'Artifact retention'],
    sourceUrl: 'https://github.com/anchore/syft',
    note: 'No filesystem, container, image or package database is inspected, and no SBOM is generated.',
  },
  {
    sequence: 9,
    frameworkId: 'trivy-upgrade-intake',
    repository: 'aquasecurity/trivy',
    revision: 'dcfb99218f072d1f54576af3c0b4f6fc8fe843f3',
    licenceSignal: 'GitHub metadata: Apache-2.0',
    upgradeTarget: 'Authorised vulnerability scan-plan design',
    categories: ['Scope consent', 'Finding redaction', 'No-scan plan'],
    sourceUrl: 'https://github.com/aquasecurity/trivy',
    note: 'No scanner, vulnerability database, cloud account, target, finding or remediation is used.',
  },
  {
    sequence: 10,
    frameworkId: 'opentelemetry-upgrade-intake',
    repository: 'open-telemetry/opentelemetry-python',
    revision: 'eeeaa8f925c2b4430db3c08ef9912249138d7c00',
    licenceSignal: 'GitHub metadata: Apache-2.0',
    upgradeTarget: 'Local-only observability and audit boundary',
    categories: ['Observability', 'Telemetry minimisation', 'Audit boundary'],
    sourceUrl: 'https://github.com/open-telemetry/opentelemetry-python',
    note: 'No SDK, instrumentation, collector, exporter, trace, metric, log or telemetry destination is enabled.',
  },
]
