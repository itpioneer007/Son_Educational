import { storageKey } from '../config/storage.js'

const STORAGE_KEY = storageKey('features-history')

const SEED_HISTORY = [
  {
    id: 'h1',
    type: 'ppt',
    title: '牛顿第二定律 · PPT课件',
    subject: '高中物理',
    status: 'completed',
    createdAt: Date.now() - 86400000 * 1,
    pages: 18,
  },
  {
    id: 'h2',
    type: 'doc',
    title: '牛顿第二定律 · 教案',
    subject: '高中物理',
    status: 'completed',
    createdAt: Date.now() - 86400000 * 2,
    pages: 6,
  },
  {
    id: 'h3',
    type: 'interactive',
    title: '力的分解 · 教学题生成',
    subject: '高中物理',
    status: 'draft',
    createdAt: Date.now() - 86400000 * 3,
    pages: 4,
  },
  {
    id: 'h4',
    type: 'ppt',
    title: '鸦片战争 · 导入课件',
    subject: '初中历史',
    status: 'iterating',
    createdAt: Date.now() - 86400000 * 5,
    pages: 12,
  },
]

const TYPE_LABELS = {
  ppt: '课件生成',
  doc: '教案生成',
  interactive: '教学题生成',
}

const STATUS_LABELS = {
  completed: '已完成',
  draft: '待完善',
  iterating: '优化中',
  failed: '失败',
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    /* ignore */
  }
  return structuredClone(SEED_HISTORY)
}

function saveHistory(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

function uid() {
  return `h_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
}

export function useFeatures() {
  function getHistory() {
    return [...loadHistory()].sort((a, b) => b.createdAt - a.createdAt)
  }

  function getStats() {
    const list = loadHistory()
    return {
      total: list.length,
      completed: list.filter((h) => h.status === 'completed').length,
      iterating: list.filter((h) => h.status === 'iterating').length,
      ppt: list.filter((h) => h.type === 'ppt').length,
      doc: list.filter((h) => h.type === 'doc').length,
      interactive: list.filter((h) => h.type === 'interactive').length,
    }
  }

  function addRecord({ type, title, subject, status = 'draft', pages = 0, taskId }) {
    const record = {
      id: uid(),
      type,
      title,
      subject: subject || '未分类',
      status,
      createdAt: Date.now(),
      pages,
      taskId: taskId || null,
    }
    const list = loadHistory()
    list.unshift(record)
    saveHistory(list)
    return record
  }

  function updateRecord(id, patch) {
    const list = loadHistory()
    const index = list.findIndex((item) => item.id === id)
    if (index < 0) return null

    list[index] = {
      ...list[index],
      ...patch,
    }
    saveHistory(list)
    return list[index]
  }

  function deleteRecord(id) {
    saveHistory(loadHistory().filter((h) => h.id !== id))
  }

  return {
    getHistory,
    getStats,
    addRecord,
    updateRecord,
    deleteRecord,
    TYPE_LABELS,
    STATUS_LABELS,
  }
}

export function formatFeatureTime(ts) {
  const diff = Date.now() - ts
  const day = 86400000
  if (diff < day) return '今天'
  if (diff < day * 2) return '昨天'
  if (diff < day * 7) return `${Math.floor(diff / day)} 天前`
  return new Date(ts).toLocaleDateString('zh-CN')
}

export function getTypeIcon(type) {
  // 使用SVG图标，更美观且有设计感
  const icons = {
    ppt: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/>
      <path d="M8 9v6M8 9l2.5 3M8 15l2.5-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="15" cy="10" r="1.5" fill="currentColor"/>
      <circle cx="15" cy="14" r="1.5" fill="currentColor"/>
    </svg>`,
    doc: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
      <path d="M14 2v6h6M8 13h8M8 17h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M14 2l6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>`,
    interactive: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="6" width="16" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/>
      <path d="M8 10h2M8 14h2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      <circle cx="15" cy="12" r="2" stroke="currentColor" stroke-width="1.5"/>
      <path d="M17 12l2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>`,
  }
  return icons[type] || icons.ppt
}
