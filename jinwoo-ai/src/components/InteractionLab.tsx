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

  return (
    <section className="interaction-lab" aria-labelledby="interaction-lab-title">
      <header className="interaction-lab__hero panel">
        <div>
          <p className="eyebrow">BATCH 06 · CAMERA &amp; HARDWARE SAFETY BOUNDARY</p>
          <h1 id="interaction-lab-title">Interaction lab</h1>
          <p>Gesture, orb and physical-device ideas are visible for review only. Camera capture, hand tracking, local services and physical hardware control are all locked by default.</p>
          <div className="interaction-lab__hero-flags">
            <span>Camera off</span>
            <span>No device connected</span>
            <span>No physical action</span>
          </div>
        </div>
        <CommandOrb state="guarded" />
      </header>

      <div className="interaction-lab__grid">
        <article className="interaction-card interaction-card--gesture">
          <div className="interaction-card__icon" aria-hidden="true">⌁</div>
          <p className="eyebrow">WEBCAM / GESTURES</p>
          <h2>Hand-tracking concept</h2>
          <p>Pinch, rotate and zoom interactions can be designed later as an opt-in accessibility layer. No browser camera permission or MediaPipe runtime is present in this build.</p>
          <div className="interaction-card__status">
            <span>Camera: locked</span>
            <span>{barehands ? labelForStatus(barehands.implementationStatus) : 'source review required'}</span>
          </div>
          <ul>
            <li>Explicit in-app camera consent</li>
            <li>Camera-off default and visible indicator</li>
            <li>Local processing and emergency stop review</li>
          </ul>
        </article>

        <article className="interaction-card interaction-card--orb">
          <div className="interaction-card__orb"><CommandOrb compact /></div>
          <p className="eyebrow">ORIGINAL VISUAL SYSTEM</p>
          <h2>Orb command readout</h2>
          <p>The visual orb in Jinwoo is an original CSS interface element for mission state. It is not the upstream implementation and does not include a camera, Three.js scene or Android control.</p>
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
          <p>Batch 06 records interaction ideas, not a camera controller or hardware driver. Each possible future route needs a narrow source review, privacy review, explicit user consent, visible action preview, audit record and disable path.</p>
        </div>
        <button className="button button--ghost" type="button" onClick={onOpenRegistry}>Review framework contracts <span>↗</span></button>
      </aside>
    </section>
  )
}
