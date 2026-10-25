/**
 * 极简 i18n — 不引入第三方库。
 * 语言偏好存 localStorage，全局 signal 驱动重渲染。
 */
import { useState, useEffect } from 'react'

export type Lang = 'zh' | 'en'

const STORAGE_KEY = 'rm_lang'

function getInitialLang(): Lang {
  return (localStorage.getItem(STORAGE_KEY) as Lang) ?? 'zh'
}

// 全局当前语言（模块级单例）
let _lang: Lang = typeof window !== 'undefined' ? getInitialLang() : 'zh'
const _listeners = new Set<() => void>()

export function getLang(): Lang { return _lang }

export function setLang(lang: Lang) {
  _lang = lang
  localStorage.setItem(STORAGE_KEY, lang)
  _listeners.forEach(fn => fn())
}

export function toggleLang() {
  setLang(_lang === 'zh' ? 'en' : 'zh')
}

// ── 主题控制 ──────────────────────────────────────────────────────────────
const THEME_KEY = 'rm_theme'
export type Theme = 'dark' | 'light'

function getInitialTheme(): Theme {
  return (localStorage.getItem(THEME_KEY) as Theme) ?? 'dark'
}

let _theme: Theme = typeof window !== 'undefined' ? getInitialTheme() : 'dark'
const _themeListeners = new Set<() => void>()

function applyTheme(theme: Theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light')
  } else {
    document.documentElement.removeAttribute('data-theme')
  }
}

export function setTheme(theme: Theme) {
  _theme = theme
  localStorage.setItem(THEME_KEY, theme)
  applyTheme(theme)
  _themeListeners.forEach(fn => fn())
}

export function toggleTheme() {
  setTheme(_theme === 'dark' ? 'light' : 'dark')
}

export function useTheme(): [Theme, () => void] {
  const [theme, setLocalTheme] = useState<Theme>(_theme)
  useEffect(() => {
    applyTheme(_theme) // 页面加载时应用
    const handler = () => setLocalTheme(_theme)
    _themeListeners.add(handler)
    return () => { _themeListeners.delete(handler) }
  }, [])
  return [theme, toggleTheme]
}

/** React hook，订阅语言变化 */
export function useLang(): [Lang, () => void] {
  const [lang, setLocalLang] = useState<Lang>(_lang)
  useEffect(() => {
    const handler = () => setLocalLang(_lang)
    _listeners.add(handler)
    return () => { _listeners.delete(handler) }
  }, [])
  return [lang, toggleLang]
}

// ── 文案字典 ──────────────────────────────────────────────────────────────

export const T = {
  // App
  appName:       { zh: 'ReviewMatch', en: 'ReviewMatch' },
  appSub:        { zh: 'ISCA 2027 审稿人匹配系统', en: 'ISCA 2027 Reviewer Matching' },

  // Nav
  navDashboard:  { zh: '仪表盘', en: 'Dashboard' },
  navPapers:     { zh: '论文', en: 'Papers' },
  navReviewers:  { zh: '审稿人', en: 'Reviewers' },
  navAssignment: { zh: '分配', en: 'Assignment' },
  navConflicts:  { zh: '利益冲突', en: 'Conflicts' },
  navMyPapers:   { zh: '我的论文', en: 'My Papers' },
  navMyCoi:      { zh: '申报 COI', en: 'Declare COI' },
  logout:        { zh: '退出登录', en: 'Sign out' },

  // Login
  loginTitle:    { zh: '登录', en: 'Sign in' },
  loginUsername: { zh: '用户名', en: 'Username' },
  loginPassword: { zh: '密码', en: 'Password' },
  loginSubmit:   { zh: '登录', en: 'Sign in' },
  loginLoading:  { zh: '登录中…', en: 'Signing in…' },
  loginError:    { zh: '用户名或密码错误', en: 'Invalid username or password' },
  loginNoAccount:{ zh: '没有账号？请联系会议负责人', en: 'No account? Contact the program chair.' },

  // Conference
  confTitle:     { zh: 'ISCA 2027', en: 'ISCA 2027' },
  confSub:       { zh: '审稿人匹配与分配', en: 'Reviewer Matching & Assignment' },
  confRunBtn:    { zh: '运行分配', en: 'Run Assignment' },
  statPapers:    { zh: '论文总数', en: 'Total Papers' },
  statAssigned:  { zh: '已分配', en: 'Assigned' },
  statReviewers: { zh: '审稿人', en: 'Reviewers' },
  statCoi:       { zh: '待处理 COI', en: 'Pending COI' },
  stepTitle:     { zh: '开始使用', en: 'Getting Started' },
  step1:         { zh: '导入论文 PDF', en: 'Import Paper PDFs' },
  step1d:        { zh: '上传投稿论文，系统自动提取主题和方法', en: 'Upload submissions; system extracts topics and methods automatically' },
  step2:         { zh: '导入 PC 名单', en: 'Import PC List' },
  step2d:        { zh: '上传 CSV，系统抓取每位成员的研究经历', en: 'Upload CSV; system fetches each member\'s research profile' },
  step3:         { zh: '查看匹配推荐', en: 'Review Match Recommendations' },
  step3d:        { zh: '大模型计算每篇论文与 reviewer 的匹配分数', en: 'LLM computes match scores between papers and reviewers' },
  step4:         { zh: '配置规则并运行分配', en: 'Configure Rules & Run Assignment' },
  step4d:        { zh: '设置每篇篇数、每人上限、COI 规则，一键生成分配方案', en: 'Set per-paper count, per-reviewer limit, COI rules, and generate assignments' },

  // Papers
  papersTitle:   { zh: '论文', en: 'Papers' },
  importPapers:  { zh: '导入论文', en: 'Import Papers' },
  uploading:     { zh: '上传中…', en: 'Uploading…' },
  noPapers:      { zh: '还没有论文', en: 'No papers yet' },
  noPapersDesc:  { zh: '上传论文 PDF，系统将自动提取研究主题、方法和所需专业知识', en: 'Upload paper PDFs; the system will automatically extract topics, methods, and required expertise' },
  colId:         { zh: 'ID', en: 'ID' },
  colTitle:      { zh: '标题', en: 'Title' },
  colTopics:     { zh: '研究方向', en: 'Topics' },
  colStatus:     { zh: '状态', en: 'Status' },
  statusPending:   { zh: '待分析', en: 'Pending' },
  statusAnalyzing: { zh: '分析中', en: 'Analyzing' },
  statusAnalyzed:  { zh: '已分析', en: 'Analyzed' },
  statusAssigned:  { zh: '已分配', en: 'Assigned' },
  statusError:     { zh: '分析失败', en: 'Failed' },

  // Reviewers
  reviewersTitle:  { zh: '审稿人', en: 'Reviewers' },
  importPC:        { zh: '导入 PC 名单', en: 'Import PC List' },
  importingPC:     { zh: '导入中…', en: 'Importing…' },
  noReviewers:     { zh: '还没有 Reviewer', en: 'No reviewers yet' },
  noReviewersDesc: { zh: '上传包含姓名、邮箱、机构的 CSV，系统将自动从 Google Scholar 抓取研究经历', en: 'Upload a CSV with name, email, and institution; the system will fetch research profiles from Google Scholar' },
  colName:         { zh: '姓名', en: 'Name' },
  colInstitution:  { zh: '机构', en: 'Institution' },
  colExpertise:    { zh: '研究方向', en: 'Expertise' },
  colPaperCount:   { zh: '论文数', en: 'Papers' },
  colFetchStatus:  { zh: '画像状态', en: 'Profile Status' },
  fetchDone:       { zh: '已建档', en: 'Done' },
  fetchFetching:   { zh: '抓取中', en: 'Fetching' },
  fetchPending:    { zh: '待抓取', en: 'Pending' },
  fetchNeedsConf:  { zh: '需确认', en: 'Needs Confirmation' },
  fetchNoData:     { zh: '无数据', en: 'No Data' },
  fetchError:      { zh: '抓取失败', en: 'Failed' },
  needsConfWarn:   { zh: '位 reviewer 存在同名情况，需要手动确认 Scholar 主页', en: 'reviewer(s) have ambiguous Scholar profiles — manual confirmation required' },

  // Assignment
  assignTitle:     { zh: '分配', en: 'Assignment' },
  assignSub:       { zh: '配置规则，运行匹配算法，人工调整后导出', en: 'Configure rules, run the matching algorithm, adjust manually, then export' },
  stepConfig:      { zh: '配置规则', en: 'Configure' },
  stepRunning:     { zh: '运行中', en: 'Running' },
  stepResult:      { zh: '调整 & 导出', en: 'Adjust & Export' },
  exportCsv:       { zh: '导出 CSV', en: 'Export CSV' },
  runAlgo:         { zh: '运行分配算法', en: 'Run Assignment Algorithm' },
  saveConfig:      { zh: '保存配置', en: 'Save Config' },
  reconfigBtn:     { zh: '重新配置', en: 'Reconfigure' },
  runningMsg:      { zh: '正在计算最优分配…', en: 'Computing optimal assignment…' },
  runningHint:     { zh: '通常需要 1–3 分钟', en: 'This usually takes 1–3 minutes' },
  sourceAuto:      { zh: '自动', en: 'Auto' },
  sourceManual:    { zh: '手动', en: 'Manual' },
  cfgBasic:        { zh: '基础配额', en: 'Basic Quotas' },
  cfgBasicSub:     { zh: '每篇论文和每位 reviewer 的数量约束', en: 'Count constraints per paper and per reviewer' },
  cfgPerPaper:     { zh: '每篇 reviewer 数', en: 'Reviewers per paper' },
  cfgMaxLoad:      { zh: '每人最多论文数', en: 'Max papers per reviewer' },
  cfgMinLoad:      { zh: '每人最少论文数', en: 'Min papers per reviewer' },
  cfgMinScore:     { zh: '候选最低匹配分', en: 'Min match score' },
  cfgCoi:          { zh: '利益冲突规则', en: 'Conflict of Interest Rules' },
  cfgCoiInst:      { zh: '同机构自动排除', en: 'Exclude same institution automatically' },
  cfgCoiYears:     { zh: '年内算 COI', en: 'years → COI' },
  cfgCoauthor:     { zh: '共同作者', en: 'Co-authors within' },

  // Conflicts
  conflictsTitle:  { zh: '利益冲突', en: 'Conflicts of Interest' },
  filterAll:       { zh: '全部', en: 'All' },
  filterPending:   { zh: '待确认', en: 'Pending' },
  filterConfirmed: { zh: '已确认', en: 'Confirmed' },
  srcInstitution:  { zh: '同机构', en: 'Same Institution' },
  srcCoauthor:     { zh: '共同作者', en: 'Co-author' },
  srcSelfReport:   { zh: '自申报', en: 'Self-reported' },
  srcManual:       { zh: '手动添加', en: 'Manual' },
  coiPending:      { zh: '待确认', en: 'Pending' },
  coiConfirmed:    { zh: '已确认冲突', en: 'Conflict Confirmed' },
  coiRejected:     { zh: '已驳回', en: 'Rejected' },
  confirm:         { zh: '确认', en: 'Confirm' },
  reject:          { zh: '驳回', en: 'Reject' },
  noConflicts:     { zh: '暂无利益冲突记录', en: 'No conflicts of interest' },
  noConflictsDesc: { zh: '导入论文和 PC 名单后，系统将自动检测同机构和共同作者冲突', en: 'After importing papers and the PC list, the system will auto-detect institution and co-author conflicts' },

  // Paper detail
  backToPapers:    { zh: '返回论文列表', en: 'Back to papers' },
  paperInfo:       { zh: '论文信息', en: 'Paper Info' },
  researchTopics:  { zh: '研究方向', en: 'Research Topics' },
  requiredExp:     { zh: '审稿所需专业知识', en: 'Required Expertise' },
  recReviewers:    { zh: '推荐 Reviewer', en: 'Recommended Reviewers' },
  candidates:      { zh: '位候选', en: 'candidates' },
  strongRec:       { zh: '强推荐', en: 'Strong Match' },
  goodRec:         { zh: '合适', en: 'Good Match' },
  okRec:           { zh: '勉强', en: 'Marginal' },
  addAssign:       { zh: '加入分配', en: 'Assign' },
  hasCoi:          { zh: '有利益冲突', en: 'Has COI' },
  pending:         { zh: '待分析', en: 'Pending analysis' },
  noMatchYet:      { zh: '暂无匹配分数，请先运行匹配计算', en: 'No match scores yet — run matching first' },
  noMatchPending:  { zh: '论文分析完成后自动计算匹配分数', en: 'Match scores will be computed after analysis' },

  // General
  loading:         { zh: '加载中…', en: 'Loading…' },
  retry:           { zh: '重试', en: 'Retry' },
  save:            { zh: '保存', en: 'Save' },
  cancel:          { zh: '取消', en: 'Cancel' },
  delete:          { zh: '删除', en: 'Delete' },
  notFound:        { zh: '不存在', en: 'Not found' },
} as const

export type TKey = keyof typeof T

/** 取当前语言的文案 */
export function t(key: TKey, lang: Lang): string {
  return T[key][lang]
}
