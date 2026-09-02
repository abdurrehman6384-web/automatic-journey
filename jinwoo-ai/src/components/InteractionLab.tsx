import { CommandOrb } from './CommandOrb'
import type { FrameworkStatus } from '../types/army'

interface InteractionLabProps {
  frameworks: FrameworkStatus[]
  onOpenRegistry: () => void
}

const labelForStatus = (status: FrameworkStatus['implementationStatus']) => status.replaceAll('-', ' ')

export function InteractionLab({ frameworks, onOpenRegistry }: InteractionLabProps) {
  const barehands = frameworks.find((framework) => framework.id === 'barehands')
  const orb = frameworks.find((framework) => framework.id === 'ultron-orb-ui')
  const physical = frameworks.find((framework) => framework.id === 'physical-cutter-safety-intake')
  const jarvis = frameworks.find((framework) => framework.id === 'jarvis-one-click-setup')
  const pcGesture = frameworks.find((framework) => framework.id === 'pc-hand-gesture-control')

  return (
    <section className="interaction-lab" aria-labelledby="interaction-lab-title">
      <header className="interaction-lab__hero panel">
        <div>
          <p className="eyebrow">BATCH 06 + 10 · CAMERA, DESKTOP &amp; HARDWARE SAFETY BOUNDARY</p>
          <h1 id="interaction-lab-title">Interaction lab</h1>
          <p>Gesture, assistant-setup, orb and physical-device ideas are visible for review only. Camera capture, hand tracking, setup scripts, local services, desktop input and physical hardware control are all locked by default.</p>
          <div className="interaction-lab__hero-flags">
            <span>Camera off</span>
            <span>Pointer locked</span>
            <span>No setup script</span>
            <span>No physical action</span>
          </div>
        </div>
        <CommandOrb state="guarded" />
      </header>

      <div className="interaction-lab__grid">
        <article className="interaction-card interaction-card--gesture">
          <div className="interaction-card__icon" aria-hidden="true">⌁</div>
          <p className="eyebrow">WEBCAM / GESTURES</p>
          <h2>Hand-tracking safety intake</h2>
          <p>Gesture interactions can be designed later as an opt-in accessibility layer. Both reviewed gesture sources remain source-gated: no browser camera permission, vision runtime, hand model or pointer event is present in this build.</p>
          <div className="interaction-card__status">
            <span>Camera: locked</span>
            <span>Barehands: {barehands ? labelForStatus(barehands.implementationStatus) : 'source review required'}</span>
            <span>PC gesture: {pcGesture ? labelForStatus(pcGesture.implementationStatus) : 'source review required'}</span>
          </div>
          <ul>
            <li>Explicit in-app camera consent and visible indicator</li>
            <li>Local processing, capture minimisation and retention review</li>
            <li>Per-action approval, emergency stop and no autonomous pointer</li>
          </ul>
        </article>

        <article className="interaction-card interaction-card--desktop">
          <div className="interaction-card__icon" aria-hidden="true">▣</div>
          <p className="eyebrow">DESKTOP ASSISTANT SETUP</p>
          <h2>One-click setup intake</h2>
          <p>The reviewed Jarvis source is a source-review record, not a setup path. No installer, batch file, provider, voice/audio, browser, external-tool session, file opener or desktop action is copied or started.</p>
          <div className="interaction-card__status">
            <span>Setup: locked</span>
            <span>{jarvis ? labelForStatus(jarvis.implementationStatus) : 'source review required'}</span>
          </div>
          <ul>
            <li>Verify a compatible licence for every selected source subtree</li>
            <li>Keep secrets in local secure storage, never setup scripts</li>
            <li>Show exact install/action previews before future approval</li>
          </ul>
        </article>

        <article className="interaction-card interaction-card--orb">
          <div className="interaction-card__orb"><CommandOrb compact /></div>
          <p className="eyebrow">ORIGINAL VISUAL SYSTEM</p>
          <h2>Orb command readout</h2>
          <p>The visual orb in Jinwoo is an original CSS interface element for mission state. It is not an upstream implementation and does not include a camera, 3D scene or Android control.</p>
          <div className="interaction-card__status">
            <span>Visual only</span>
            <span>{orb ? labelForStatus(orb.implementationStatus) : 'contract ready'}</span>
          </div>
          <ul>
            <li>Ready, active and guarded mission states</li>
            <li>Original visual language, no third-party assets</li>
            <li>No autonomous phone or desktop action</li>
          </ul>
        </article>

        <article className="interaction-card interaction-card--hardware">
          <div className="interaction-card__icon" aria-hidden="true">⛉</div>
          <p className="eyebrow">PHYSICAL CUTTER / ROBOTICS</p>
          <h2>Safety intake only</h2>
          <p>No cutter, robotic arm, motor, blade, laser, serial port, USB device, Bluetooth device or industrial controller can be connected from Jinwoo.</p>
          <div className="interaction-card__status">
            <span>Hardware: disconnected</span>
            <span>{physical ? labelForStatus(physical.implementationStatus) : 'source review required'}</span>
          </div>
          <ul>
            <li>Machine/manual and legal-use review first</li>
            <li>Physical guard, emergency stop and operator plan</li>
            <li>Independent safety sign-off before any future proposal</li>
          </ul>
        </article>
      </div>

      <aside className="interaction-lab__boundary panel">
        <div>
          <p className="eyebrow">NON-NEGOTIABLE SAFETY CHECKPOINT</p>
          <h2>Nothing moves without a separate safety phase.</h2>
          <p>Batch 06 and Batch 10 record interaction ideas and source-review evidence, not a camera controller, installer or hardware driver. Each possible route needs a narrow source and privacy review, explicit user consent, visible action preview, audit record and disable path.</p>
        </div>
        <button className="button button--ghost" type="button" onClick={onOpenRegistry}>Review framework contracts <span>↗</span></button>
      </aside>
    </section>
  )
}
