import { Link, useRouterState } from '@tanstack/react-router'
import {
  AlertTriangle, FileText, LayoutDashboard,
  LogOut, Menu, Users, X, GitMerge,
} from 'lucide-react'
import { type ReactNode, useEffect, useState } from 'react'
import { Button } from '~/components/ui/button'
import { cn } from '~/lib/utils'
import type { CurrentUser } from '~/lib/auth'
import { useLang, useTheme, t } from '~/lib/i18n'

export function AppShell({ user, children }: { user: CurrentUser; children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [lang, toggleLang] = useLang()
  const [theme, toggleTheme] = useTheme()
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  useEffect(() => setOpen(false), [pathname])

  const nav = [
    { to: '/conference', icon: LayoutDashboard, label: t('navDashboard', lang) },
    { to: '/papers',     icon: FileText,         label: t('navPapers', lang) },
    { to: '/reviewers',  icon: Users,            label: t('navReviewers', lang) },
    { to: '/assignment', icon: GitMerge,         label: t('navAssignment', lang) },
    { to: '/conflicts',  icon: AlertTriangle,    label: t('navConflicts', lang) },
  ]

  return (
    <div className="min-h-dvh lg:grid" style={{ gridTemplateColumns: '220px 1fr' }}>
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex flex-col border-r border-[var(--border)] bg-surface w-[220px]',
          'transition-transform duration-[var(--duration-normal)] ease-[var(--ease-smooth)]',
          'lg:sticky lg:top-0 lg:h-dvh lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Logo */}
        <div className="flex h-14 items-center justify-between px-4 border-b border-[var(--border)]">
          <Link to="/conference" className="flex items-center gap-2">
            <div className="size-6 rounded-[6px] bg-primary flex items-center justify-center">
              <span className="text-[10px] font-bold text-white">R</span>
            </div>
            <span className="text-sm font-semibold text-foreground">ReviewMatch</span>
          </Link>
          <Button variant="ghost" size="icon-sm" className="lg:hidden" onClick={() => setOpen(false)}>
            <X />
          </Button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-3" aria-label="主导航">
          <ul className="flex flex-col gap-0.5">
            {nav.map((item) => (
              <li key={item.to}>
                <Link
                  to={item.to}
                  activeOptions={{ exact: item.to === '/conference', includeSearch: false }}
                  className="flex h-9 items-center gap-2.5 rounded-[var(--radius-sm)] px-2.5 text-sm text-[var(--text-secondary)] hover:bg-surface-subtle hover:text-foreground transition-colors duration-[var(--duration-fast)] [&.active]:bg-surface-selected [&.active]:text-primary [&.active]:font-medium"
                >
                  <item.icon className="size-4 shrink-0" />
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* Bottom: lang toggle + user */}
        <div className="border-t border-[var(--border)] px-3 py-3 space-y-2">
          {/* Controls row */}
          <div className="flex gap-1.5">
            <button
              onClick={toggleLang}
              className="flex-1 flex items-center justify-center gap-1 rounded-[var(--radius-sm)] px-2 py-1.5 text-xs text-muted-foreground hover:bg-surface-subtle hover:text-foreground transition-colors border border-[var(--border)]"
            >
              {lang === 'zh' ? '中 → EN' : 'EN → 中'}
            </button>
            <button
              onClick={toggleTheme}
              title={theme === 'dark' ? '切换浅色' : 'Switch to dark'}
              className="flex items-center justify-center rounded-[var(--radius-sm)] px-2.5 py-1.5 text-xs text-muted-foreground hover:bg-surface-subtle hover:text-foreground transition-colors border border-[var(--border)]"
            >
              {theme === 'dark' ? '☀' : '◑'}
            </button>
          </div>

          {/* User */}
          <div className="flex items-center gap-2.5 rounded-[var(--radius-sm)] px-2 py-1.5">
            <div className="size-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <span className="text-xs font-semibold text-primary">{user.name[0]?.toUpperCase()}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-foreground truncate">{user.name}</div>
              <div className="text-xs text-[var(--text-tertiary)] truncate">{user.email}</div>
            </div>
            <button
              title={t('logout', lang)}
              className="text-[var(--text-tertiary)] hover:text-foreground transition-colors"
              onClick={async () => {
                await fetch('/api/auth/logout', { method: 'POST' })
                location.href = '/login'
              }}
            >
              <LogOut className="size-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Backdrop */}
      {open && (
        <div className="fixed inset-0 z-30 bg-black/30 lg:hidden" onClick={() => setOpen(false)} aria-hidden />
      )}

      {/* Main */}
      <div className="flex min-w-0 flex-col">
        <header
          className="sticky top-0 z-20 flex items-center gap-2 border-b border-[var(--border)] px-4 glass"
          style={{ height: '56px' }}
        >
          <Button variant="ghost" size="icon-sm" className="-ml-1 lg:hidden" onClick={() => setOpen(true)}>
            <Menu />
          </Button>
          <div className="flex-1" />
        </header>
        <main className="mx-auto w-full max-w-[1280px] flex-1 px-6 py-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  )
}
