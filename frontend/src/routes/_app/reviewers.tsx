import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Upload, Users, RefreshCw, ChevronRight, AlertCircle } from 'lucide-react'
import { PageHeader } from '~/components/layout/page-header'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card } from '~/components/ui/card'
import { EmptyState } from '~/components/layout/empty-state'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'

export const Route = createFileRoute('/_app/reviewers')({
  component: ReviewersPage,
})

interface Reviewer {
  id: number
  name: string
  email: string
  institution: string | null
  expertise_topics: string[] | null
  fetch_status: string
  publications: unknown[] | null
}

function ReviewersPage() {
  const [lang] = useLang()
  const [reviewers, setReviewers] = useState<Reviewer[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    const data = await api.get<Reviewer[]>('/reviewers').catch(() => null)
    if (data) setReviewers(data)
    else setError(lang === 'zh' ? '加载失败' : 'Failed to load')
    setLoading(false)
  }

  async function handleCsvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    await fetch('/api/reviewers/upload-csv', { method: 'POST', body: form })
    await load()
    setUploading(false)
    e.target.value = ''
  }

  const fetchLabel = (s: string) => ({
    pending:            t('fetchPending', lang),
    fetching:           t('fetchFetching', lang),
    done:               t('fetchDone', lang),
    needs_confirmation: t('fetchNeedsConf', lang),
    no_data:            t('fetchNoData', lang),
    error:              t('fetchError', lang),
  }[s] ?? s)

  const fetchVariant = (s: string): 'default' | 'warning' | 'success' | 'danger' =>
    s === 'done' ? 'success' : s === 'needs_confirmation' || s === 'fetching' ? 'warning' : s === 'error' ? 'danger' : 'default'

  const needsConf = reviewers.filter(r => r.fetch_status === 'needs_confirmation')

  return (
    <div className="anim-fade-up">
      <PageHeader
        title={t('reviewersTitle', lang)}
        description={`${reviewers.length} ${lang === 'zh' ? '位' : ''}`}
        action={
          <label className="cursor-pointer inline-flex h-9 items-center gap-1.5 rounded-[10px] bg-primary px-4 text-sm font-medium text-white shadow-sm hover:opacity-90 transition-opacity select-none">
            <input type="file" accept=".csv" className="sr-only" onChange={handleCsvUpload} />
            {uploading ? <RefreshCw className="size-4 animate-spin" /> : <Upload className="size-4" />}
            {uploading ? t('importingPC', lang) : t('importPC', lang)}
          </label>
        }
      />

      {error && <p className="text-sm text-danger mb-4">{error}</p>}

      {needsConf.length > 0 && (
        <div className="mb-4 rounded-[var(--radius)] bg-warning-surface border border-[var(--border)] px-4 py-3 flex items-center gap-3">
          <AlertCircle className="size-4 text-warning shrink-0" />
          <span className="text-sm text-foreground">
            {needsConf.length} {t('needsConfWarn', lang)}
          </span>
        </div>
      )}

      {loading ? (
        <Card className="p-8 flex items-center justify-center">
          <RefreshCw className="size-5 animate-spin text-muted-foreground" />
        </Card>
      ) : reviewers.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Users className="size-5" />}
            title={t('noReviewers', lang)}
            description={t('noReviewersDesc', lang)}
          />
        </Card>
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                {[t('colName', lang), t('colInstitution', lang), t('colExpertise', lang), t('colPaperCount', lang), t('colFetchStatus', lang), ''].map(h => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {reviewers.map((r, i) => (
                <tr key={r.id} className="hover:bg-surface-subtle transition-colors anim-fade-up" style={{ animationDelay: `${i * 20}ms` }}>
                  <td className="px-5 py-3">
                    <div className="font-medium text-foreground">{r.name}</div>
                    <div className="text-xs text-muted-foreground">{r.email}</div>
                  </td>
                  <td className="px-5 py-3 text-sm text-muted-foreground">{r.institution ?? '—'}</td>
                  <td className="px-5 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(r.expertise_topics ?? []).slice(0, 2).map(topic => <Badge key={topic}>{topic}</Badge>)}
                      {!r.expertise_topics?.length && <span className="text-xs text-[var(--text-tertiary)]">—</span>}
                    </div>
                  </td>
                  <td className="px-5 py-3 text-sm text-muted-foreground">{r.publications?.length ?? '—'}</td>
                  <td className="px-5 py-3"><Badge variant={fetchVariant(r.fetch_status)}>{fetchLabel(r.fetch_status)}</Badge></td>
                  <td className="px-5 py-3 text-right">
                    <Link to="/reviewers/$id" params={{ id: String(r.id) }}>
                      <Button variant="ghost" size="icon-sm"><ChevronRight className="size-4" /></Button>
                    </Link>
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
