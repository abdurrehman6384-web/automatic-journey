import { useState } from 'react'
import type { FormEvent } from 'react'
import type { ChatMessage, ProviderStatus } from '../types/army'

interface ChatPanelProps {
  messages: ChatMessage[]
  providers: ProviderStatus[]
  busy: boolean
  onSend: (message: string, preferredProvider: string | undefined, allowCloud: boolean) => Promise<boolean>
}

export function ChatPanel({ messages, providers, busy, onSend }: ChatPanelProps) {
  const [message, setMessage] = useState('')
  const [preferredProvider, setPreferredProvider] = useState('')
  const [allowCloud, setAllowCloud] = useState(false)
  const [formError, setFormError] = useState('')

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const clean = message.trim()
    if (!clean) {
      setFormError('Write a message for Jinwoo first.')
      return
    }
    setFormError('')
    if (await onSend(clean, preferredProvider || undefined, allowCloud)) setMessage('')
  }

  return (
    <section className="chat-panel panel" aria-labelledby="chat-title">
      <div className="panel-heading">
        <div><p className="eyebrow">LOCAL AI CHAT</p><h2 id="chat-title">Speak with Jinwoo</h2></div>
        <span className="subtle-badge">APPROVAL-FIRST</span>
      </div>
      <p className="chat-panel__hint">Ask for an explanation, draft, or plan. Use the command bar when you want to create a visible Army mission.</p>
      <div className="chat-thread" aria-live="polite">
        {messages.map((chat) => (
          <article className={`chat-message chat-message--${chat.role}`} key={chat.id}>
            <span className="chat-message__avatar">{chat.role === 'assistant' ? '♛' : 'YOU'}</span>
            <div>
              <p>{chat.content}</p>
              {chat.role === 'assistant' && chat.provider && <small>{chat.provider}{chat.localOnly ? ' · local / demo route' : ' · cloud-approved route'}</small>}
            </div>
          </article>
        ))}
        {busy && <article className="chat-message chat-message--assistant"><span className="chat-message__avatar">♛</span><div><p className="chat-typing">Jinwoo is preparing a response<span>.</span><span>.</span><span>.</span></p></div></article>}
      </div>
      <form className="chat-form" onSubmit={submit}>
        <label htmlFor="chat-message">Your message</label>
        <textarea id="chat-message" value={message} onChange={(event) => setMessage(event.target.value)} maxLength={8000} placeholder="Ask Jinwoo to explain, draft or plan something safely…" />
        <div className="chat-form__routing">
          <label htmlFor="chat-provider">Route</label>
          <select id="chat-provider" value={preferredProvider} onChange={(event) => setPreferredProvider(event.target.value)}>
            <option value="">Auto — local first</option>
            {providers.filter((provider) => provider.mode !== 'memory').map((provider) => (
              <option key={provider.id} value={provider.id} disabled={provider.state !== 'ready'}>{provider.label} — {provider.state === 'ready' ? provider.mode : 'not configured'}</option>
            ))}
          </select>
          <label className="consent-check"><input type="checkbox" checked={allowCloud} onChange={(event) => setAllowCloud(event.target.checked)} /><span>I explicitly approve cloud processing for this message if a cloud route is used.</span></label>
        </div>
        {formError && <p className="form-error" role="alert">{formError}</p>}
        <div className="chat-form__actions"><span>Credentials, OTPs and blocked security requests are rejected.</span><button className="button" type="submit" disabled={busy}>{busy ? 'Thinking…' : 'Send to Jinwoo'} <b>↗</b></button></div>
      </form>
    </section>
  )
}
