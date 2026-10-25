import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { useLang, useTheme, t } from '~/lib/i18n'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

function LoginPage() {
  const navigate = useNavigate()
  const [lang, toggleLang] = useLang()
  const [theme, toggleTheme] = useTheme()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) { setError(t('loginError', lang)); return }
      await navigate({ to: '/conference' })
    } catch {
      setError(t('loginError', lang))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-dvh flex items-center justify-center bg-background px-4">
      {/* Lang toggle */}
      <div className="fixed top-4 right-4 flex gap-1.5">
        <button onClick={toggleLang}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded border border-[var(--border)]">
          {lang === 'zh' ? 'EN' : '中文'}
        </button>
        <button onClick={toggleTheme}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded border border-[var(--border)]">
          {theme === 'dark' ? '☀' : '◑'}
        </button>
      </div>

      <div className="w-full max-w-sm anim-spring-in">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="size-12 rounded-[var(--radius)] bg-primary flex items-center justify-center shadow-md">
            <span className="text-xl font-bold text-white">R</span>
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold text-foreground">{t('appName', lang)}</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">{t('appSub', lang)}</p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="rounded-[var(--radius-lg)] bg-surface shadow-[var(--shadow-lg)] p-6 space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">{t('loginUsername', lang)}</label>
            <Input value={username} onChange={e => setUsername(e.target.value)}
              placeholder="admin" autoComplete="username" autoFocus required />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">{t('loginPassword', lang)}</label>
            <Input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••" autoComplete="current-password" required />
          </div>
          {error && <p className="text-xs text-danger">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? t('loginLoading', lang) : t('loginSubmit', lang)}
          </Button>
          <p className="text-center text-xs text-[var(--text-tertiary)]">{t('loginNoAccount', lang)}</p>
        </form>
      </div>
    </div>
  )
}
