import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { ArrowLeft, RefreshCw, UserPlus, AlertTriangle } from 'lucide-react'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'
import { toast } from '~/components/ui/toast'

export const Route = createFileRoute('/_app/papers/$id')({
  component: PaperDetailPage,
})

interface Paper {
  id: number
  title: string
  abstract: string | null
  authors: { name: string; institution?: string }[] | null
  topics: string[] | null
  methods: string[] | null
  required_expertise: string[] | null
  analysis_status: string
  analysis_error: string | null
}

interface Match {
  reviewer_id: number
  reviewer_name: string
  reviewer_institution: string | null
  total_score: number
  topic_score: number
  method_score: number
  recency_score: number
  rationale: string | null
  has_conflict: boolean
}

function ScoreBar({ value }: { value: number }) {
  return (
    <div className="h-1 w-full rounded-full bg-surface-subtle overflow-hidden">
      <div className="h-full rounded-full bg-primary/40 transition-all duration-500" style={{ width: `${value}%` }} />
    </div>
  )
}

function ReviewerCard({ match, onAssign, lang }: { match: Match; onAssign: (rid: number) => Promise<void>; lang: 'zh' | 'en' }) {
  const [loading, setLoading] = useState(false)
  const score = match.total_score
  const variant = score >= 85 ? 'success' : score >= 65 ? 'default' : 'default'

  async function handleClick() {
    setLoading(true)
    await onAssign(match.reviewer_id)
    setLoading(false)
  }

  return (
    <div className="rounded-[var(--radius)] border border-[var(--border)] bg-surface p-4 hover-lift anim-spring-in">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm text-foreground">{match.reviewer_name}</span>
            {match.has_conflict && <span title="COI"><AlertTriangle className="size-3.5 text-warning shrink-0" /></span>}
          </div>
          {match.reviewer_institution && <div className="text-xs text-muted-foreground mt-0.5">{match.reviewer_institution}</div>}
        </div>
        <Badge variant={variant} className="font-mono text-xs shrink-0">{score}</Badge>
      </div>

      <div className="space-y-1.5 mb-3">
        {([['topic', match.topic_score], ['method', match.method_score], ['recency', match.recency_score]] as [string, number][]).map(([k, v]) => (
          <div key={k} className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-tertiary)] w-12 shrink-0">{k}</span>
            <ScoreBar value={v} />
            <span className="text-xs text-muted-foreground w-6 text-right shrink-0">{v}</span>
          </div>
        ))}
      </div>

      {match.rationale && <p className="text-xs text-muted-foreground mb-3 leading-relaxed">{match.rationale}</p>}

      <Button variant="outline" size="sm" className="w-full" disabled={match.has_conflict || loading} onClick={handleClick}>
        {loading ? <RefreshCw className="size-3.5 animate-spin" /> : <UserPlus className="size-3.5" />}
        {match.has_conflict ? t('hasCoi', lang) : t('addAssign', lang)}
      </Button>
    </div>
  )
}

function PaperDetailPage() {
  const { id } = Route.useParams()
  const [lang] = useLang()
  const [paper, setPaper] = useState<Paper | null>(null)
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null

    async function load() {
      try {
        const [p, m] = await Promise.all([
          api.get<Paper>(`/papers/${id}`),
          api.get<Match[]>(`/matches/paper/${id}`),
        ])
        setPaper(p)
        setMatches(m)
        // 分析完成后停止轮询
        if (p.analysis_status !== 'pending' && p.analysis_status !== 'analyzing') {
          if (interval) { clearInterval(interval); interval = null }
        }
      } catch {}
      setLoading(false)
    }

    load()
    // 分析中时每 3 秒刷新
    interval = setInterval(load, 3000)
    return () => { if (interval) clearInterval(interval) }
  }, [id])

  async function handleAssign(reviewerId: number) {
    try {
      await api.post(`/assignment/${id}/add/${reviewerId}`, {})
      toast.success(lang === 'zh' ? '已加入分配' : 'Assigned successfully')
    } catch {
      toast.error(lang === 'zh' ? '分配失败，可能已存在' : 'Assignment failed')
    }
  }

  if (loading) return <div className="flex items-center justify-center py-24"><RefreshCw className="size-5 animate-spin text-muted-foreground" /></div>
  if (!paper) return <p className="text-sm text-muted-foreground">{t('notFound', lang)}</p>

  const strong = matches.filter(m => m.total_score >= 85)
  const good   = matches.filter(m => m.total_score >= 65 && m.total_score < 85)
  const ok     = matches.filter(m => m.total_score >= 40 && m.total_score < 65)

  return (
    <div className="anim-fade-up">
      <Link to="/papers" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4">
        <ArrowLeft className="size-3.5" /> {t('backToPapers', lang)}
      </Link>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_360px]">
        {/* Left */}
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>{t('paperInfo', lang)}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <h2 className="text-base font-semibold text-foreground leading-snug">{paper.title}</h2>
              {paper.authors && <p className="text-sm text-muted-foreground">{paper.authors.map(a => a.name).join(', ')}</p>}
              {paper.abstract && <p className="text-sm text-foreground/80 leading-relaxed">{paper.abstract}</p>}
              {paper.analysis_error && <p className="text-xs text-danger">{paper.analysis_error}</p>}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>{t('researchTopics', lang)}</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {(paper.topics ?? []).map(topic => <Badge key={topic}>{topic}</Badge>)}
                  {!paper.topics?.length && <span className="text-xs text-muted-foreground">{t('pending', lang)}</span>}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>{t('requiredExp', lang)}</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {(paper.required_expertise ?? []).map(e => <Badge key={e} variant="primary">{e}</Badge>)}
                  {!paper.required_expertise?.length && <span className="text-xs text-muted-foreground">{t('pending', lang)}</span>}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">{t('recReviewers', lang)}</h2>
            <span className="text-xs text-muted-foreground">{matches.length} {t('candidates', lang)}</span>
          </div>

          {matches.length === 0 ? (
            <div className="rounded-[var(--radius)] border border-[var(--border)] p-6 text-center text-sm text-muted-foreground">
              {paper.analysis_status === 'analyzed' ? t('noMatchYet', lang) : t('noMatchPending', lang)}
            </div>
          ) : (
            <div className="space-y-5">
              {strong.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-success mb-2">{t('strongRec', lang)} · {strong.length}</div>
                  <div className="space-y-2">{strong.map(m => <ReviewerCard key={m.reviewer_id} match={m} onAssign={handleAssign} lang={lang} />)}</div>
                </div>
              )}
              {good.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-muted-foreground mb-2">{t('goodRec', lang)} · {good.length}</div>
                  <div className="space-y-2">{good.map(m => <ReviewerCard key={m.reviewer_id} match={m} onAssign={handleAssign} lang={lang} />)}</div>
                </div>
              )}
              {ok.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-[var(--text-tertiary)] mb-2">{t('okRec', lang)} · {ok.length}</div>
                  <div className="space-y-2">{ok.map(m => <ReviewerCard key={m.reviewer_id} match={m} onAssign={handleAssign} lang={lang} />)}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
