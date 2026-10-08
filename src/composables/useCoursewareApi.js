/**
 * 课件生成 API 封装
 * 对接 Python FastAPI 后端 (http://localhost:8000)
 */

const API_BASE = "http://localhost:8000/api/courseware"

/**
 * 提交课件生成任务
 * @param {Object} params - 生成参数
 * @param {'ppt'|'doc'|'quiz'} params.type - 生成类型
 * @param {string} params.subject - 学科
 * @param {string} params.topic - 课题
 * @param {string} [params.grade] - 年级
 * @param {string} [params.style] - 课件风格
 * @param {string} [params.outline] - 大纲要求
 * @param {string} [params.requirements] - 其他要求
 * @param {string} [params.difficulty] - 难度
 * @param {string} [params.template] - 本地 PPT 模版 ID
 * @param {'spark'|'local'} [params.engine] - PPT 生成引擎（讯飞智文 / 本地模板）
 * @param {string} [params.sparkTemplateId] - 讯飞模板 ID，为空用后端默认
 * @param {boolean} [params.isCardNote] - 讯飞：是否生成演讲备注
 * @param {boolean} [params.isFigure] - 讯飞：是否自动配图
 * @returns {Promise<{taskId: string, status: string}>}
 */
export async function submitCoursewareTask(params) {
  const formData = new FormData()
  formData.append("type", params.type)
  formData.append("subject", params.subject)
  formData.append("topic", params.topic)
  if (params.grade) formData.append("grade", params.grade)
  if (params.style) formData.append("style", params.style)
  if (params.outline) formData.append("outline", params.outline)
  if (params.requirements) formData.append("requirements", params.requirements)
  if (params.difficulty) formData.append("difficulty", params.difficulty)
  if (params.template) formData.append("template", params.template)

  // PPT 生成引擎与讯飞参数
  if (params.engine) formData.append("engine", params.engine)
  if (params.sparkTemplateId) formData.append("sparkTemplateId", params.sparkTemplateId)
  if (params.isCardNote !== undefined) formData.append("isCardNote", String(params.isCardNote))
  if (params.isFigure !== undefined) formData.append("isFigure", String(params.isFigure))

  // 如果有参考文件，附加上传
  if (params.files?.length) {
    for (const file of params.files) {
      formData.append("files", file)
    }
  }

  const res = await fetch(`${API_BASE}/create`, {
    method: "POST",
    body: formData,
  })
  if (!res.ok) throw new Error(`提交失败: ${res.status}`)
  return res.json()
}

/**
 * 查询任务状态
 * @param {string} taskId
 * @returns {Promise<Object>}
 */
export async function getTaskStatus(taskId) {
  const res = await fetch(`${API_BASE}/${taskId}`)
  if (!res.ok) throw new Error(`查询失败: ${res.status}`)
  return res.json()
}

/**
 * 建立 SSE 连接，实时监听生成进度
 * @param {string} taskId
 * @param {Object} callbacks
 * @param {(data: {status, progress, stage, filename}) => void} callbacks.onProgress
 * @param {(data: {filename}) => void} callbacks.onComplete
 * @param {(err: Error) => void} callbacks.onError
 * @returns {EventSource}
 */
export function subscribeProgress(taskId, callbacks) {
  const source = new EventSource(`${API_BASE}/${taskId}/stream`)

  source.addEventListener("progress", (e) => {
    try {
      const data = JSON.parse(e.data)
      callbacks.onProgress?.(data)

      if (data.status === "completed") {
        callbacks.onComplete?.(data)
        source.close()
      }
      if (data.status === "failed") {
        callbacks.onError?.(new Error(data.error || "生成失败"))
        source.close()
      }
    } catch (err) {
      callbacks.onError?.(err)
      source.close()
    }
  })

  source.addEventListener("error", () => {
    // EventSource 自动重连，超过重试次数会触发此事件
    callbacks.onError?.(new Error("SSE 连接断开"))
    source.close()
  })

  return source
}

/**
 * 下载生成的文件
 * @param {string} taskId
 * @param {string} filename
 */
export function downloadFile(taskId, filename) {
  const a = document.createElement("a")
  a.href = `${API_BASE}/${taskId}/download`
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

/**
 * 获取历史记录
 * @returns {Promise<Array>}
 */
export async function getCoursewareHistory() {
  const res = await fetch(`${API_BASE}/list`)
  if (!res.ok) throw new Error(`获取历史失败: ${res.status}`)
  return res.json()
}

/**
 * 删除任务
 * @param {string} taskId
 */
export async function deleteCoursewareTask(taskId) {
  const res = await fetch(`${API_BASE}/${taskId}`, { method: "DELETE" })
  if (!res.ok) throw new Error(`删除失败: ${res.status}`)
  return res.json()
}
