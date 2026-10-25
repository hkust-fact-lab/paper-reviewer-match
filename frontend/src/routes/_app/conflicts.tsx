import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw, Check, X } from 'lucide-react'
import { PageHeader } from '~/components/layout/page-header'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card } from '~/components/ui/card'
import { EmptyState } from '~/components/layout/empty-state'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'
import { toast } from '~/components/ui/toast'

export const Route = createFileRoute('/_app/conflicts')({
  component: ConflictsPage,
})

interface Conflict {
  id: number
  paper_id: number
  reviewer_id: number
  paper_title: string
  reviewer_name: string
  source: string
  detail: string | null
  status: string
  created_at: string
}

function ConflictsPage() {
  const [lang] = useLang()
  const [conflicts, setConflicts] = useState<Conflict[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'pending' | 'confirmed'>('all')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    const data = await api.get<Conflict[]>('/conflicts').catch(() => [])
    setConflicts(data)
    setLoading(false)
  }

  async function confirm(id: number) {
    await api.patch(`/conflicts/${id}/confirm`, {})
    toast.success(lang === 'zh' ? '已确认冲突' : 'Conflict confirmed')
    load()
  }

  async function reject(id: number) {
    await api.patch(`/conflicts/${id}/reject`, {})
    toast.success(lang === 'zh' ? '已驳回' : 'Rejected')
    load()
  }

  const srcLabel = (s: string) => ({
    institution:   t('srcInstitution', lang),
    coauthor:      t('srcCoauthor', lang),
    self_reported: t('srcSelfReport', lang),
    manual:        t('srcManual', lang),
  }[s] ?? s)

  const filtered = filter === 'all' ? conflicts : conflicts.filter(c => c.status === filter)

  return (
    <div className="anim-fade-up">
      <PageHeader
        title={t('conflictsTitle', lang)}
        description={`${conflicts.length} ${lang === 'zh' ? '条记录' : 'records'}`}
      />

      {/* Filter tabs */}
      <div className="flex gap-1 mb-4">
        {(['all', 'pending', 'confirmed'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-medium transition-colors ${filter === f ? 'bg-primary text-white' : 'text-muted-foreground hover:bg-surface-subtle'}`}>
            {f === 'all' ? t('filterAll', lang) : f === 'pending' ? t('filterPending', lang) : t('filterConfirmed', lang)}
            <span className="ml-1.5 opacity-70">
              {f === 'all' ? conflicts.length : conflicts.filter(c => c.status === f).length}
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <Card className="p-8 flex items-center justify-center">
          <RefreshCw className="size-5 animate-spin text-muted-foreground" />
        </Card>
      ) : filtered.length === 0 ? (
        <Card>
          <EmptyState
            icon={<AlertTriangle className="size-5" />}
            title={t('noConflicts', lang)}
            description={t('noConflictsDesc', lang)}
          />
        </Card>
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                {[t('papersTitle', lang), 'Reviewer', lang === 'zh' ? '来源' : 'Source', lang === 'zh' ? '状态' : 'Status', lang === 'zh' ? '操作' : 'Actions'].map(h => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {filtered.map(c => (
                <tr key={c.id} className="hover:bg-surface-subtle transition-colors">
                  <td className="px-5 py-3 max-w-xs">
                    <p className="text-foreground line-clamp-1">{c.paper_title}</p>
                  </td>
                  <td className="px-5 py-3 text-foreground">{c.reviewer_name}</td>
                  <td className="px-5 py-3">
                    <Badge variant="default">{srcLabel(c.source)}</Badge>
                    {c.detail && <p className="text-xs text-muted-foreground mt-0.5">{c.detail}</p>}
                  </td>
                  <td className="px-5 py-3">
                    {c.status === 'pending'   && <Badge variant="warning">{t('coiPending', lang)}</Badge>}
                    {c.status === 'confirmed' && <Badge variant="danger">{t('coiConfirmed', lang)}</Badge>}
                    {c.status === 'rejected'  && <Badge variant="default">{t('coiRejected', lang)}</Badge>}
                  </td>
                  <td className="px-5 py-3">
                    {c.status === 'pending' && (
                      <div className="flex gap-1.5">
                        <Button size="sm" variant="outline" onClick={() => confirm(c.id)}>
                          <Check className="size-3.5" /> {t('confirm', lang)}
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => reject(c.id)}>
                          <X className="size-3.5" /> {t('reject', lang)}
                        </Button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
