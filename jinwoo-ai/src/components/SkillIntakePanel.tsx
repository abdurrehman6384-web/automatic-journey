import type { FrameworkStatus } from '../types/army'
import { skillCatalog } from '../data/skillCatalog'

interface SkillIntakePanelProps {
  frameworks: FrameworkStatus[]
}

const groups = ['Core catalogues', 'Provider and modality lanes', 'Large-scale collection lanes', 'Specialist method lanes'] as const

const statusLabel = (framework: FrameworkStatus | undefined) => {
  if (!framework) return 'exact source pending'
  if (framework.implementationStatus === 'reference-only') return 'reference only'
  return framework.implementationStatus.replaceAll('-', ' ')
}

export function SkillIntakePanel({ frameworks }: SkillIntakePanelProps) {
  const frameworkById = new Map(frameworks.map((framework) => [framework.id, framework]))

  return (
    <section className="skill-intake panel" aria-labelledby="skill-intake-title">
      <header className="skill-intake__heading">
        <div>
          <p className="eyebrow">BATCH 11 · REQUESTED SKILL-SOURCE REVIEW QUEUE</p>
          <h2 id="skill-intake-title">Shadow Army skill catalogue</h2>
          <p>Rank reflects the requested review order, not trust or activation priority. Reported counts are source claims or labels—not active agents. Jinwoo remains fixed at 15 commanders, 45 divisions and 450 logical agents.</p>
        </div>
        <div className="skill-intake__locks" aria-label="Skill safety locks">
          <span>No skill payload loaded</span>
          <span>No auto activation</span>
          <span>Policy stays canonical</span>
        </div>
      </header>

      <p className="skill-intake__notice">A catalogue record never turns a repository, profile, prompt or instruction file into a native capability. Every source remains disabled until its exact licence, subtree, provenance, privacy, dependency and approval review passes.</p>

      {groups.map((group) => {
        const entries = skillCatalog.filter((entry) => entry.group === group)
        return (
          <section className="skill-intake__group" key={group} aria-labelledby={`skill-group-${group.replaceAll(' ', '-').toLowerCase()}`}>
            <h3 id={`skill-group-${group.replaceAll(' ', '-').toLowerCase()}`}>{group}</h3>
            <div className="skill-intake__grid">
              {entries.map((entry) => {
                const framework = frameworkById.get(entry.frameworkId)
                const sourceUrl = framework?.sourceUrl ?? entry.sourceUrl
                return (
                  <article className="skill-source-card" key={entry.frameworkId}>
                    <div className="skill-source-card__topline">
                      <span className="skill-source-card__rank">Rank {String(entry.rank).padStart(2, '0')}</span>
                      <span className={`framework-state framework-state--${framework?.implementationStatus ?? 'queued'}`}>{statusLabel(framework)}</span>
                    </div>
                    <h4>{entry.repository}</h4>
                    <p className="skill-source-card__scope"><b>Reported scope</b>{entry.reportedScope}</p>
                    <div className="skill-source-card__categories" aria-label={`${entry.repository} categories`}>
                      {entry.categories.map((category) => <span key={category}>{category}</span>)}
                    </div>
                    <p className="skill-source-card__note">{entry.note}</p>
                    <div className="skill-source-card__footer">
                      {sourceUrl
                        ? <a href={sourceUrl} target="_blank" rel="noreferrer">Review source <span aria-hidden="true">↗</span></a>
                        : <span>Exact source link required</span>}
                      <span>{framework?.ownerCommander ?? 'Owner pending'}</span>
                    </div>
                  </article>
                )
              })}
            </div>
          </section>
        )
      })}
    </section>
  )
}
