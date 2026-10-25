import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { BookOpen, RefreshCw } from 'lucide-react'
import { PageHeader } from '~/components/layout/page-header'
import { Card } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { EmptyState } from '~/components/layout/empty-state'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'

export const Route = createFileRoute('/_app/my/papers')({
  component: MyPapersPage,
})

interface Assignment {
  paper_id: number
  paper_title: string
  reviewer_name: string
  status: string
}

function MyPapersPage() {
  const [lang] = useLang()
  const [papers, setPapers] = useState<Assignment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/auth/me/reviewer-id').then(r => r.json()),
      api.get<Assignment[]>('/assignment'),
    ]).then(([{ reviewer_id }, all]) => {
      const mine = reviewer_id
        ? (all as any[]).filter(a => a.reviewer_id === reviewer_id)
        : []
      setPapers(mine)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return (
    <div className="anim-fade-up">
      <PageHeader
        title={t('navMyPapers', lang)}
        description={`${papers.length} ${lang === 'zh' ? '篇' : 'papers'}`}
      />
      {loading ? (
        <Card className="p-8 flex items-center justify-center">
          <RefreshCw className="size-5 animate-spin text-muted-foreground" />
        </Card>
      ) : papers.length === 0 ? (
        <Card>
          <EmptyState
            icon={<BookOpen className="size-5" />}
            title={lang === 'zh' ? '暂未分配论文' : 'No papers assigned'}
            description={lang === 'zh' ? '分配完成后，你负责审阅的论文将显示在这里' : 'Papers assigned to you will appear here after assignment is complete.'}
          />
        </Card>
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                {[t('colTitle', lang), t('colStatus', lang)].map(h => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {papers.map(p => (
                <tr key={p.paper_id} className="hover:bg-surface-subtle transition-colors">
                  <td className="px-5 py-3 text-foreground">{p.paper_title}</td>
                  <td className="px-5 py-3">
                    <Badge variant={p.status === 'confirmed' ? 'success' : 'default'}>
                      {p.status === 'confirmed'
                        ? (lang === 'zh' ? '已确认' : 'Confirmed')
                        : (lang === 'zh' ? '待审阅' : 'Pending')}
                    </Badge>
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
