import { createFileRoute, Link } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { FileText, GitMerge, AlertTriangle, Users, RefreshCw } from 'lucide-react'
import { Card, CardContent } from '~/components/ui/card'
import { PageHeader } from '~/components/layout/page-header'
import { Button } from '~/components/ui/button'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'

export const Route = createFileRoute('/_app/conference')({
  component: ConferencePage,
})

interface Stats {
  papers: number
  assigned: number
  reviewers: number
  pending_conflicts: number
  analyzing: number
  has_matches: boolean
}

function ConferencePage() {
  const [lang] = useLang()
  const [stats, setStats] = useState<Stats | null>(null)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    loadStats()
    const interval = setInterval(loadStats, 5000)
    return () => clearInterval(interval)
  }, [])

  async function loadStats() {
    try {
      const [papers, reviewers, assignments, conflicts] = await Promise.all([
        api.get<any[]>('/papers'),
        api.get<any[]>('/reviewers'),
        api.get<any[]>('/assignment'),
        api.get<any[]>('/conflicts'),
      ])
      const analyzedIds = papers.filter((p: any) => p.analysis_status === 'analyzed').map((p: any) => p.id)
      // 检查是否有匹配分数（取第一篇已分析论文查询）
      let has_matches = false
      if (analyzedIds.length > 0) {
        const matches = await api.get<any[]>(`/matches/paper/${analyzedIds[0]}`).catch(() => [])
        has_matches = matches.length > 0
      }
      setStats({
        papers: papers.length,
        assigned: new Set(assignments.map((a: any) => a.paper_id)).size,
        reviewers: reviewers.length,
        pending_conflicts: conflicts.filter((c: any) => c.status === 'pending').length,
        analyzing: papers.filter((p: any) => p.analysis_status === 'analyzing').length,
        has_matches,
      })
    } catch {}
  }

  async function handleRun() {
    setRunning(true)
    await api.post('/assignment/run', {}).catch(() => {})
    setTimeout(() => { setRunning(false); loadStats() }, 2000)
  }

  const steps = [
    { n: 1, label: t('step1', lang), desc: t('step1d', lang), done: (stats?.papers ?? 0) > 0, to: '/papers' as const },
    { n: 2, label: t('step2', lang), desc: t('step2d', lang), done: (stats?.reviewers ?? 0) > 0, to: '/reviewers' as const },
    { n: 3, label: t('step3', lang), desc: t('step3d', lang), done: stats?.has_matches ?? false, to: '/papers' as const },
    { n: 4, label: t('step4', lang), desc: t('step4d', lang), done: (stats?.assigned ?? 0) > 0, to: '/assignment' as const },
  ]

  return (
    <div className="anim-fade-up">
      <PageHeader
        title={t('confTitle', lang)}
        description={t('confSub', lang)}
        action={
          <Button onClick={handleRun} disabled={running}>
            {running ? <RefreshCw className="size-4 animate-spin" /> : <GitMerge className="size-4" />}
            {t('confRunBtn', lang)}
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4 mb-6">
        {[
          { label: t('statPapers', lang),    value: stats?.papers,           sub: stats?.analyzing ? `${stats.analyzing} ${lang === 'zh' ? '篇分析中' : 'analyzing'}` : '',  icon: FileText,       to: '/papers' },
          { label: t('statAssigned', lang),   value: stats?.assigned,         sub: `/ ${stats?.papers ?? 0}`,                                                                  icon: GitMerge,       to: '/assignment' },
          { label: t('statReviewers', lang),  value: stats?.reviewers,        sub: '',                                                                                          icon: Users,          to: '/reviewers' },
          { label: t('statCoi', lang),        value: stats?.pending_conflicts, sub: '',                                                                                         icon: AlertTriangle,  to: '/conflicts' },
        ].map(({ label, value, sub, icon: Icon, to }) => (
          <Link key={to} to={to}>
            <Card className="hover-lift cursor-pointer">
              <CardContent className="pt-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="mt-1 text-2xl font-semibold text-foreground">
                      {stats ? (value ?? 0) : <RefreshCw className="size-4 animate-spin text-muted-foreground mt-1.5 inline-block" />}
                    </p>
                    {sub && <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>}
                  </div>
                  <div className="size-9 rounded-[var(--radius-sm)] bg-surface-subtle flex items-center justify-center">
                    <Icon className="size-4 text-muted-foreground" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <Card>
        <CardContent className="pt-5 pb-5">
          <h2 className="text-sm font-semibold text-foreground mb-4">{t('stepTitle', lang)}</h2>
          <ol className="space-y-3">
            {steps.map(({ n, label, desc, done, to }) => (
              <li key={n}>
                <Link to={to} className="flex items-start gap-3 group">
                  <div className={`size-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 mt-0.5 transition-colors ${done ? 'bg-success text-white' : 'bg-surface-subtle text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary'}`}>
                    {done ? '✓' : n}
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${done ? 'text-muted-foreground line-through' : 'text-foreground'}`}>{label}</p>
                    <p className="text-xs text-muted-foreground">{desc}</p>
                  </div>
                </Link>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>
    </div>
  )
}
