import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Upload, FileText, RefreshCw, ChevronRight } from 'lucide-react'
import { PageHeader } from '~/components/layout/page-header'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card } from '~/components/ui/card'
import { EmptyState } from '~/components/layout/empty-state'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'

export const Route = createFileRoute('/_app/papers')({
  component: PapersPage,
})

interface Paper {
  id: number
  hotcrp_id: string | null
  title: string
  authors: { name: string }[] | null
  topics: string[] | null
  analysis_status: string
}

function PapersPage() {
  const [lang] = useLang()
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    const data = await api.get<Paper[]>('/papers').catch(() => null)
    if (data) setPapers(data)
    else setError(lang === 'zh' ? '加载失败，请刷新重试' : 'Failed to load. Please refresh.')
    setLoading(false)
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files
    if (!files?.length) return
    setUploading(true)
    const form = new FormData()
    for (const f of files) form.append('files', f)
    await fetch('/api/papers/upload', { method: 'POST', body: form })
    await load()
    setUploading(false)
    e.target.value = ''
  }

  const statusMap = (status: string): { label: string; variant: 'default' | 'warning' | 'success' | 'danger' | 'primary' } => {
    const map: Record<string, { label: string; variant: 'default' | 'warning' | 'success' | 'danger' | 'primary' }> = {
      pending:   { label: t('statusPending', lang),   variant: 'default' },
      analyzing: { label: t('statusAnalyzing', lang), variant: 'warning' },
      analyzed:  { label: t('statusAnalyzed', lang),  variant: 'success' },
      assigned:  { label: t('statusAssigned', lang),  variant: 'primary' },
      error:     { label: t('statusError', lang),     variant: 'danger' },
    }
    return map[status] ?? { label: status, variant: 'default' }
  }

  return (
    <div className="anim-fade-up">
      <PageHeader
        title={t('papersTitle', lang)}
        description={`${papers.length} ${lang === 'zh' ? '篇' : 'papers'}`}
        action={
          <label className="cursor-pointer inline-flex h-9 items-center gap-1.5 rounded-[10px] bg-primary px-4 text-sm font-medium text-white shadow-sm hover:opacity-90 transition-opacity select-none">
            <input type="file" accept=".pdf" multiple className="sr-only" onChange={handleUpload} />
            {uploading ? <RefreshCw className="size-4 animate-spin" /> : <Upload className="size-4" />}
            {uploading ? t('uploading', lang) : t('importPapers', lang)}
          </label>
        }
      />

      {error && <p className="text-sm text-danger mb-4">{error}</p>}

      {loading ? (
        <Card className="p-8 flex items-center justify-center">
          <RefreshCw className="size-5 animate-spin text-muted-foreground" />
        </Card>
      ) : papers.length === 0 ? (
        <Card>
          <EmptyState
            icon={<FileText className="size-5" />}
            title={t('noPapers', lang)}
            description={t('noPapersDesc', lang)}
          />
        </Card>
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                {[t('colId', lang), t('colTitle', lang), t('colTopics', lang), t('colStatus', lang), ''].map(h => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {papers.map((p, i) => {
                const { label, variant } = statusMap(p.analysis_status)
                return (
                  <tr key={p.id} className="hover:bg-surface-subtle transition-colors anim-fade-up" style={{ animationDelay: `${i * 25}ms` }}>
                    <td className="px-5 py-3 text-xs text-muted-foreground font-mono">{p.hotcrp_id ?? `#${p.id}`}</td>
                    <td className="px-5 py-3">
                      <div className="font-medium text-foreground line-clamp-1">{p.title}</div>
                      {p.authors && (
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {p.authors.slice(0, 3).map(a => a.name).join(', ')}
                          {p.authors.length > 3 && ' …'}
                        </div>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(p.topics ?? []).slice(0, 2).map(topic => <Badge key={topic}>{topic}</Badge>)}
                      </div>
                    </td>
                    <td className="px-5 py-3"><Badge variant={variant}>{label}</Badge></td>
                    <td className="px-5 py-3 text-right">
                      <Link to="/papers/$id" params={{ id: String(p.id) }}>
                        <Button variant="ghost" size="icon-sm"><ChevronRight className="size-4" /></Button>
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
