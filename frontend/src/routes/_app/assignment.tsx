import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { Play, RefreshCw, Download, Trash2 } from 'lucide-react'
import { PageHeader } from '~/components/layout/page-header'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { api } from '~/lib/api'
import { useLang, t } from '~/lib/i18n'
import { toast } from '~/components/ui/toast'

export const Route = createFileRoute('/_app/assignment')({
  component: AssignmentPage,
})

interface Config {
  reviewers_per_paper: number
  max_papers_per_reviewer: number
  min_papers_per_reviewer: number
  min_score_threshold: number
  coi_same_institution: boolean
  coi_coauthor_years: number
}

interface Assignment {
  id: number
  paper_id: number
  reviewer_id: number
  paper_title: string
  reviewer_name: string
  source: string
  status: string
}

type Step = 'config' | 'running' | 'result'

function AssignmentPage() {
  const [lang] = useLang()
  const [step, setStep]         = useState<Step>('config')
  const [config, setConfig]     = useState<Config | null>(null)
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [saving, setSaving]     = useState(false)
  const [_running, setRunning]  = useState(false)

  useEffect(() => {
    api.get<Config>('/assignment/config').then(setConfig).catch(() => {})
    api.get<Assignment[]>('/assignment').then(data => {
      setAssignments(data)
      if (data.length > 0) setStep('result')
    }).catch(() => {})
  }, [])

  async function saveConfig() {
    if (!config) return
    setSaving(true)
    try {
      await api.patch('/assignment/config', config)
      toast.success(lang === 'zh' ? '配置已保存' : 'Config saved')
    } catch {
      toast.error(lang === 'zh' ? '保存失败' : 'Save failed')
    }
    setSaving(false)
  }

  async function runAssignment() {
    setStep('running')
    setRunning(true)
    try {
      await api.post('/assignment/run', {})
      // 轮询 tasks 表，最多等 5 分钟
      for (let i = 0; i < 100; i++) {
        await new Promise(r => setTimeout(r, 3000))
        const tasks = await api.get<any[]>('/tasks?limit=5').catch(() => [])
        const runTask = (tasks as any[]).find(task => task.type === 'run_assignment')
        if (runTask?.status === 'done') {
          const data = await api.get<Assignment[]>('/assignment').catch(() => [])
          setAssignments(data)
          setStep('result')
          toast.success(lang === 'zh' ? `分配完成，共 ${data.length} 对` : `Assignment done — ${data.length} pairs`)
          return
        }
        if (runTask?.status === 'error') {
          toast.error(runTask.error_message || (lang === 'zh' ? '分配失败' : 'Assignment failed'))
          setStep('config')
          return
        }
      }
      const data = await api.get<Assignment[]>('/assignment').catch(() => [])
      setAssignments(data)
      setStep('result')
    } catch {
      toast.error(lang === 'zh' ? '分配请求失败' : 'Assignment request failed')
      setStep('config')
    } finally {
      setRunning(false)
    }
  }

  async function removeAssignment(paperId: number, reviewerId: number) {
    await api.delete(`/assignment/${paperId}/remove/${reviewerId}`).catch(() => {})
    const data = await api.get<Assignment[]>('/assignment').catch(() => [])
    setAssignments(data)
    toast.success(lang === 'zh' ? '已移除' : 'Removed')
  }

  return (
    <div className="anim-fade-up">
      <PageHeader
        title={t('assignTitle', lang)}
        description={t('assignSub', lang)}
        action={step === 'result' ? (
          <Button onClick={() => window.open('/api/assignment/export', '_blank')}>
            <Download className="size-4" /> {t('exportCsv', lang)}
          </Button>
        ) : undefined}
      />

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6 text-sm">
        {(['config', 'running', 'result'] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`size-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${step === s ? 'bg-primary text-white' : 'bg-surface-subtle text-muted-foreground'}`}>
              {i + 1}
            </div>
            <span className={`text-sm ${step === s ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
              {s === 'config' ? t('stepConfig', lang) : s === 'running' ? t('stepRunning', lang) : t('stepResult', lang)}
            </span>
            {i < 2 && <div className="w-8 h-px bg-[var(--border)]" />}
          </div>
        ))}
      </div>

      {/* Step 1 */}
      {step === 'config' && config && (
        <div className="space-y-4 max-w-xl">
          <Card>
            <CardHeader>
              <CardTitle>{t('cfgBasic', lang)}</CardTitle>
              <CardDescription>{t('cfgBasicSub', lang)}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <label className="space-y-1.5">
                  <span className="text-xs font-medium text-foreground">{t('cfgPerPaper', lang)}</span>
                  <Input type="number" value={config.reviewers_per_paper} min={1}
                    onChange={e => setConfig({ ...config, reviewers_per_paper: +e.target.value })} />
                </label>
                <label className="space-y-1.5">
                  <span className="text-xs font-medium text-foreground">{t('cfgMaxLoad', lang)}</span>
                  <Input type="number" value={config.max_papers_per_reviewer} min={1}
                    onChange={e => setConfig({ ...config, max_papers_per_reviewer: +e.target.value })} />
                </label>
              </div>
              <label className="space-y-1.5 block">
                <span className="text-xs font-medium text-foreground">{t('cfgMinLoad', lang)}</span>
                <Input type="number" value={config.min_papers_per_reviewer} min={0}
                  onChange={e => setConfig({ ...config, min_papers_per_reviewer: +e.target.value })} />
              </label>
              <label className="space-y-1.5 block">
                <span className="text-xs font-medium text-foreground">{t('cfgMinScore', lang)}</span>
                <Input type="number" value={config.min_score_threshold} min={0} max={100}
                  onChange={e => setConfig({ ...config, min_score_threshold: +e.target.value })} />
              </label>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>{t('cfgCoi', lang)}</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <label className="flex items-center gap-3">
                <input type="checkbox" checked={config.coi_same_institution}
                  onChange={e => setConfig({ ...config, coi_same_institution: e.target.checked })}
                  className="size-4 rounded accent-primary" />
                <span className="text-sm text-foreground">{t('cfgCoiInst', lang)}</span>
              </label>
              <div className="flex items-center gap-3">
                <span className="text-sm text-foreground shrink-0">{t('cfgCoauthor', lang)}</span>
                <Input type="number" value={config.coi_coauthor_years} min={1} className="w-20"
                  onChange={e => setConfig({ ...config, coi_coauthor_years: +e.target.value })} />
                <span className="text-muted-foreground shrink-0 text-sm">{t('cfgCoiYears', lang)}</span>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button variant="outline" onClick={saveConfig} disabled={saving}>
              {saving && <RefreshCw className="size-4 animate-spin" />}
              {t('saveConfig', lang)}
            </Button>
            <Button onClick={runAssignment} className="flex-1">
              <Play className="size-4" /> {t('runAlgo', lang)}
            </Button>
          </div>
        </div>
      )}

      {/* Step 2 */}
      {step === 'running' && (
        <Card className="max-w-xl">
          <CardContent className="py-16 flex flex-col items-center gap-4">
            <div className="size-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <p className="text-sm font-medium text-foreground">{t('runningMsg', lang)}</p>
            <p className="text-xs text-muted-foreground">{t('runningHint', lang)}</p>
          </CardContent>
        </Card>
      )}

      {/* Step 3 */}
      {step === 'result' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {assignments.length} {lang === 'zh' ? '对分配' : 'assignment pairs'}
            </p>
            <Button variant="outline" size="sm" onClick={() => setStep('config')}>
              {t('reconfigBtn', lang)}
            </Button>
          </div>
          <Card>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {[t('papersTitle', lang), 'Reviewer', lang === 'zh' ? '来源' : 'Source', ''].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-medium text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {assignments.map(a => (
                  <tr key={a.id} className="hover:bg-surface-subtle transition-colors">
                    <td className="px-5 py-3 max-w-xs"><p className="text-foreground line-clamp-1">{a.paper_title}</p></td>
                    <td className="px-5 py-3 text-foreground">{a.reviewer_name}</td>
                    <td className="px-5 py-3">
                      <Badge variant={a.source === 'manual' ? 'primary' : 'default'}>
                        {a.source === 'manual' ? t('sourceManual', lang) : t('sourceAuto', lang)}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Button variant="ghost" size="icon-sm" onClick={() => removeAssignment(a.paper_id, a.reviewer_id)}>
                        <Trash2 className="size-3.5 text-danger" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}
    </div>
  )
}
