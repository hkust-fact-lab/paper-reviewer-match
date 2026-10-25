import { createFileRoute, Link } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { ArrowLeft, RefreshCw, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'
import { toast } from '~/components/ui/toast'

export const Route = createFileRoute('/_app/reviewers/$id')({
  component: ReviewerDetailPage,
})

interface Reviewer {
  id: number
  name: string
  email: string
  institution: string | null
  scholar_url: string | null
  scholar_confirmed: boolean
  fetch_status: string
  fetch_error: string | null
  expertise_topics: string[] | null
  publications: { title: string; year: number; venue: string; citedby: number; url: string }[] | null
  load_min: number
  load_max: number
}

function ReviewerDetailPage() {
  const { id } = Route.useParams()
  const [lang] = useLang()
  const [reviewer, setReviewer] = useState<Reviewer | null>(null)
  const [assignments, setAssignments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [refetching, setRefetching] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get<Reviewer>(`/reviewers/${id}`),
      api.get<any[]>('/assignment').then(all => all.filter(a => a.reviewer_id === Number(id))),
    ]).then(([r, a]) => { setReviewer(r); setAssignments(a) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  async function handleRefetch() {
    setRefetching(true)
    try {
      await fetch(`/api/reviewers/${id}/retry-fetch`, { method: 'POST' })
      toast.success(lang === 'zh' ? '已重新入队抓取' : 'Re-queued for fetching')
    } catch {
      toast.error(lang === 'zh' ? '操作失败' : 'Failed')
    }
    setRefetching(false)
  }

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <RefreshCw className="size-5 animate-spin text-muted-foreground" />
    </div>
  )
  if (!reviewer) return <p className="text-sm text-muted-foreground">{t('notFound', lang)}</p>

  const needsConf = reviewer.fetch_status === 'needs_confirmation'
  const candidates: any[] = needsConf
    ? (() => { try { return JSON.parse(reviewer.fetch_error ?? '[]') } catch { return [] } })()
    : []

  const fetchLabel = {
    done:               lang === 'zh' ? '已建档' : 'Done',
    needs_confirmation: lang === 'zh' ? '需确认' : 'Needs Confirmation',
    no_data:            lang === 'zh' ? '无数据' : 'No Data',
    error:              lang === 'zh' ? '抓取失败' : 'Failed',
    fetching:           lang === 'zh' ? '抓取中' : 'Fetching',
    pending:            lang === 'zh' ? '待抓取' : 'Pending',
  }[reviewer.fetch_status] ?? reviewer.fetch_status

  const fetchVariant: 'success' | 'warning' | 'danger' | 'default' =
    reviewer.fetch_status === 'done' ? 'success'
    : reviewer.fetch_status === 'needs_confirmation' || reviewer.fetch_status === 'fetching' ? 'warning'
    : reviewer.fetch_status === 'error' ? 'danger'
    : 'default'

  return (
    <div className="anim-fade-up">
      <Link to="/reviewers" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4">
        <ArrowLeft className="size-3.5" />
        {lang === 'zh' ? '返回列表' : 'Back to list'}
      </Link>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_300px]">
        <div className="space-y-4">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle>{reviewer.name}</CardTitle>
                <Badge variant={fetchVariant}>{fetchLabel}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p className="text-muted-foreground">{reviewer.email}</p>
              {reviewer.institution && <p className="text-muted-foreground">{reviewer.institution}</p>}
              {reviewer.scholar_url && (
                <a href={reviewer.scholar_url} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1 text-primary hover:underline text-xs">
                  Scholar <ExternalLink className="size-3" />
                </a>
              )}
            </CardContent>
          </Card>

          {/* 同名确认 */}
          {needsConf && candidates.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-warning">
                  {lang === 'zh' ? '找到多个同名学者，请确认' : 'Multiple matches found — please confirm'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {candidates.map((c: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-[var(--radius-sm)] border border-[var(--border)] p-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{c.name}</p>
                      <p className="text-xs text-muted-foreground">{c.affiliation || c.institution || '—'}</p>
                      <p className="text-xs text-muted-foreground">{c.paper_count ?? ''}</p>
                    </div>
                    <Button size="sm" variant="outline" onClick={async () => {
                      await fetch(`/api/reviewers/${id}/confirm-scholar?scholar_url=${encodeURIComponent(c.scholar_url)}`, { method: 'PATCH' })
                      toast.success(lang === 'zh' ? '已确认，重新入队抓取' : 'Confirmed, re-queued')
                      location.reload()
                    }}>
                      {lang === 'zh' ? '选择此人' : 'Select'}
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* 专长 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{lang === 'zh' ? '研究专长' : 'Research Expertise'}</CardTitle>
                <Button variant="ghost" size="sm" onClick={handleRefetch} disabled={refetching}>
                  <RefreshCw className={`size-3.5 ${refetching ? 'animate-spin' : ''}`} />
                  {lang === 'zh' ? '重新抓取' : 'Re-fetch'}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {reviewer.expertise_topics?.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {reviewer.expertise_topics.map(topic => <Badge key={topic}>{topic}</Badge>)}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {reviewer.fetch_status === 'no_data'
                    ? (lang === 'zh' ? '未找到 Scholar 数据，可手动填写 Scholar URL 后重新抓取' : 'No Scholar data found. Add a Scholar URL and re-fetch.')
                    : (lang === 'zh' ? '待抓取' : 'Pending')}
                </p>
              )}
            </CardContent>
          </Card>

          {/* 论文 */}
          {reviewer.publications && reviewer.publications.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{lang === 'zh' ? `论文记录（${reviewer.publications.length} 篇）` : `Publications (${reviewer.publications.length})`}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {reviewer.publications.slice(0, 10).map((p, i) => (
                    <div key={i} className="flex items-start justify-between gap-3 py-2 border-b border-[var(--border)] last:border-0">
                      <div className="min-w-0">
                        <p className="text-sm text-foreground line-clamp-1">{p.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {p.venue && <span className="font-medium">{p.venue} · </span>}
                          {p.year || (lang === 'zh' ? '年份未知' : 'Unknown year')}
                          {p.citedby > 0 && ` · ${lang === 'zh' ? '被引' : 'Cited'} ${p.citedby}`}
                        </p>
                      </div>
                      {p.url && (
                        <a href={p.url} target="_blank" rel="noreferrer" className="shrink-0 text-muted-foreground hover:text-primary">
                          <ExternalLink className="size-3.5" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right */}
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>{lang === 'zh' ? '本次分配' : 'This Conference'}</CardTitle></CardHeader>
            <CardContent>
              {assignments.length === 0 ? (
                <p className="text-sm text-muted-foreground">{lang === 'zh' ? '暂未分配' : 'Not assigned yet'}</p>
              ) : (
                <div className="space-y-2">
                  {assignments.map(a => (
                    <div key={a.paper_id} className="text-sm text-foreground line-clamp-2 py-1 border-b border-[var(--border)] last:border-0">
                      {a.paper_title}
                    </div>
                  ))}
                </div>
              )}
              <p className="text-xs text-muted-foreground mt-3">
                {lang === 'zh' ? `上限 ${reviewer.load_max} 篇` : `Max ${reviewer.load_max} papers`}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
