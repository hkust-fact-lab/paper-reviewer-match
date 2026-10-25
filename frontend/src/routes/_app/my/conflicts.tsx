import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect, useRef } from 'react'
import { PageHeader } from '~/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Input } from '~/components/ui/input'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { api } from '~/lib/api'
import { useLang } from '~/lib/i18n'
import { toast } from '~/components/ui/toast'

export const Route = createFileRoute('/_app/my/conflicts')({
  component: MyConflictsPage,
})

interface Paper { id: number; title: string; authors: { name: string }[] | null }
interface Conflict { id: number; paper_id: number; paper_title: string; source: string; status: string }

const COI_REASONS = {
  coauthor:     { zh: '合著关系', en: 'Co-authorship' },
  institution:  { zh: '同机构',   en: 'Same institution' },
  manual:       { zh: '导师/学生', en: 'Advisor/Advisee' },
}

function MyConflictsPage() {
  const [lang] = useLang()
  const [search, setSearch] = useState('')
  const [results, setResults] = useState<Paper[]>([])
  const [declared, setDeclared] = useState<Conflict[]>([])
  const [selectedReason, setSelectedReason] = useState<string>('coauthor')
  const [searching, setSearching] = useState(false)
  const [myReviewerId, setMyReviewerId] = useState<number | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    // 加载已申报
    api.get<Conflict[]>('/conflicts').then(all => {
      setDeclared(all.filter(c => c.source === 'self_reported'))
    }).catch(() => {})
    // 获取自己的 reviewer id（通过 email 精确匹配，后端保证唯一）
    fetch('/api/auth/me/reviewer-id')
      .then(r => r.json())
      .then(({ reviewer_id }) => { if (reviewer_id) setMyReviewerId(reviewer_id) })
  }, [])

  useEffect(() => {
    if (!search.trim()) { setResults([]); return }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      const all = await api.get<Paper[]>('/papers').catch(() => [] as Paper[])
      const q = search.toLowerCase()
      setResults(all.filter(p =>
        p.title.toLowerCase().includes(q) ||
        (p.authors ?? []).some(a => a.name.toLowerCase().includes(q))
      ).slice(0, 8))
      setSearching(false)
    }, 400)
  }, [search])

  async function declare(paperId: number) {
    if (!myReviewerId) {
      toast.error(lang === 'zh' ? '未找到你的 reviewer 记录' : 'Your reviewer record not found')
      return
    }
    try {
      await api.post('/conflicts', { paper_id: paperId, reviewer_id: myReviewerId, source: 'self_reported', detail: selectedReason })
      toast.success(lang === 'zh' ? '已申报' : 'Declared successfully')
      const all = await api.get<Conflict[]>('/conflicts')
      setDeclared(all.filter(c => c.source === 'self_reported'))
      setSearch('')
    } catch {
      toast.error(lang === 'zh' ? '申报失败，可能已存在' : 'Declaration failed')
    }
  }

  return (
    <div className="anim-fade-up">
      <PageHeader
        title={lang === 'zh' ? '申报利益冲突' : 'Declare Conflict of Interest'}
        description={lang === 'zh' ? '如与某篇论文有利益冲突，请主动申报' : 'Proactively declare any conflicts of interest with submissions'}
      />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_340px]">
        <Card>
          <CardHeader><CardTitle>{lang === 'zh' ? '搜索论文' : 'Search Papers'}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input
              placeholder={lang === 'zh' ? '输入论文标题或作者名' : 'Search by title or author'}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />

            {/* Reason selector */}
            <div className="flex gap-2 flex-wrap">
              {Object.entries(COI_REASONS).map(([key, labels]) => (
                <button
                  key={key}
                  onClick={() => setSelectedReason(key)}
                  className={`px-2.5 py-1 rounded-[var(--radius-sm)] text-xs font-medium transition-colors ${selectedReason === key ? 'bg-primary text-white' : 'bg-surface-subtle text-muted-foreground hover:bg-surface-selected'}`}
                >
                  {labels[lang]}
                </button>
              ))}
            </div>

            {/* Results */}
            {search && (
              <div className="rounded-[var(--radius-sm)] border border-[var(--border)] divide-y divide-[var(--border)]">
                {searching ? (
                  <p className="px-4 py-3 text-sm text-muted-foreground">{lang === 'zh' ? '搜索中…' : 'Searching…'}</p>
                ) : results.length === 0 ? (
                  <p className="px-4 py-3 text-sm text-muted-foreground">{lang === 'zh' ? '无匹配结果' : 'No results'}</p>
                ) : results.map(p => (
                  <div key={p.id} className="flex items-center justify-between px-4 py-3 hover:bg-surface-subtle transition-colors">
                    <div className="min-w-0 mr-3">
                      <p className="text-sm text-foreground line-clamp-1">{p.title}</p>
                      {p.authors && <p className="text-xs text-muted-foreground">{p.authors.slice(0, 2).map(a => a.name).join(', ')}</p>}
                    </div>
                    <Button size="sm" variant="outline" onClick={() => declare(p.id)}>
                      {lang === 'zh' ? '申报' : 'Declare'}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{lang === 'zh' ? `已申报 (${declared.length})` : `Declared (${declared.length})`}</CardTitle></CardHeader>
          <CardContent>
            {declared.length === 0 ? (
              <p className="text-sm text-muted-foreground">{lang === 'zh' ? '暂无申报记录' : 'No declarations yet'}</p>
            ) : (
              <div className="space-y-2">
                {declared.map(c => (
                  <div key={c.id} className="text-sm py-2 border-b border-[var(--border)] last:border-0">
                    <p className="text-foreground line-clamp-1">{c.paper_title}</p>
                    <Badge variant={c.status === 'confirmed' ? 'danger' : 'warning'} className="mt-1">
                      {c.status === 'confirmed' ? (lang === 'zh' ? '已确认冲突' : 'Confirmed') : (lang === 'zh' ? '待确认' : 'Pending')}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
