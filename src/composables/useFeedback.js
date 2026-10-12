import { computed, ref } from 'vue'
import { storageKey } from '../config/storage.js'

const STORAGE_KEY = storageKey('reflect-feedback')

// 反馈类型 —— 与「提交新反馈」表单的下拉选项一一对应。
export const FEEDBACK_TYPE_LABELS = {
  courseware: '课件优化',
  'lesson-plan': '教案改进',
  activity: '教学活动设计',
  'ai-quality': 'AI 生成质量',
  platform: '平台功能建议',
  other: '其他',
}

// 反馈状态 —— data-status 沿用 .rh-status 的既有配色（橙 / 蓝 / 绿）。
export const FEEDBACK_STATUS_LABELS = {
  pending: '待处理',
  iterating: '处理中',
  resolved: '已采纳',
}

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persist(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  } catch {
    /* 隐私模式 / 配额写满：内存里的这份仍然可用 */
  }
}

// 模块级单例：表单提交与「全部反馈记录」弹窗共享同一份列表。
// 之前提交只弹 toast、不写任何数据，右侧「历史反馈记录」读的又是生成任务历史，
// 所以提交后列表永远不变 —— 这里单独开一份 storage，与生成任务彻底解耦。
const items = ref(load())

function uid() {
  return `fb_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
}

export function useFeedback() {
  // 按提交时间倒序；提交后 computed 自动失效，列表即时刷新
  const feedbackList = computed(() =>
    [...items.value].sort((a, b) => b.createdAt - a.createdAt),
  )

  function addFeedback({ type, title, content, contact = '', fileName = '' }) {
    const record = {
      id: uid(),
      type,
      title: String(title || '').trim(),
      content: String(content || '').trim(),
      contact: String(contact || '').trim(),
      fileName: fileName || '',
      status: 'pending',
      createdAt: Date.now(),
    }
    items.value = [record, ...items.value]
    persist(items.value)
    return record
  }

  function removeFeedback(id) {
    items.value = items.value.filter((item) => item.id !== id)
    persist(items.value)
  }

  return {
    feedbackList,
    addFeedback,
    removeFeedback,
    FEEDBACK_TYPE_LABELS,
    FEEDBACK_STATUS_LABELS,
  }
}
