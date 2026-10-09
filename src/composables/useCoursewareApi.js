/**
 * 课件生成 API 封装
 * 后端地址统一由 src/config/api.js 提供（可用 VITE_API_ORIGIN 覆盖）
 */

import { API_BASE } from "../config/api.js";

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
 * @param {string} [params.sparkTemplateId] - 讯飞模板 ID，为空用后端默认
 * @param {boolean} [params.isCardNote] - 讯飞：是否生成演讲备注
 * @param {boolean} [params.isFigure] - 讯飞：是否自动配图
 * @param {string} [params.duration] - 课时长度
 * @param {string} [params.studentProfile] - 学生学情
 * @param {string} [params.interactionDesign] - 互动设计（课件）
 * @param {string} [params.lessonFocus] - 环节侧重（教案）
 * @param {string} [params.usageScene] - 使用场景
 * @param {string} [params.assessment] - 评估标准
 * @param {string} [params.target] - 教学目标 / 考查点（练习、试卷）
 * @param {string} [params.questionTypes] - 题型构成（练习）
 * @param {string} [params.scenario] - 使用场景（练习，兼容旧字段）
 * @param {number} [params.count] - 题量（练习）
 * @param {number} [params.totalScore] - 总分（试卷）
 * @param {number} [params.choiceCount] - 选择题数量（试卷）
 * @param {number} [params.fillCount] - 填空题数量（试卷）
 * @param {number} [params.essayCount] - 解答题数量（试卷）
 * @param {boolean} [params.generateAB] - 是否生成 A/B 卷（试卷）
 * @returns {Promise<{taskId: string, status: string}>}
 */
export async function submitCoursewareTask(params) {
  const formData = new FormData();
  formData.append("type", params.type);
  formData.append("subject", params.subject);
  formData.append("topic", params.topic);
  if (params.grade) formData.append("grade", params.grade);
  if (params.style) formData.append("style", params.style);
  if (params.outline) formData.append("outline", params.outline);
  if (params.requirements) formData.append("requirements", params.requirements);
  if (params.difficulty) formData.append("difficulty", params.difficulty);

  // 教学要素（各模块共用的教学决策信息）
  if (params.duration) formData.append("duration", params.duration);
  if (params.studentProfile)
    formData.append("studentProfile", params.studentProfile);
  if (params.interactionDesign)
    formData.append("interactionDesign", params.interactionDesign);
  if (params.lessonFocus) formData.append("lessonFocus", params.lessonFocus);
  if (params.usageScene) formData.append("usageScene", params.usageScene);
  if (params.assessment) formData.append("assessment", params.assessment);
  if (params.target) formData.append("target", params.target);
  if (params.questionTypes)
    formData.append("questionTypes", params.questionTypes);

  // 练习：使用场景与题量
  if (params.scenario) formData.append("scenario", params.scenario);
  if (
    params.count !== undefined &&
    params.count !== null &&
    params.count !== ""
  )
    formData.append("count", String(params.count));

  // 试卷：卷面配置
  if (
    params.totalScore !== undefined &&
    params.totalScore !== null &&
    params.totalScore !== ""
  )
    formData.append("totalScore", String(params.totalScore));
  if (
    params.choiceCount !== undefined &&
    params.choiceCount !== null &&
    params.choiceCount !== ""
  )
    formData.append("choiceCount", String(params.choiceCount));
  if (
    params.fillCount !== undefined &&
    params.fillCount !== null &&
    params.fillCount !== ""
  )
    formData.append("fillCount", String(params.fillCount));
  if (
    params.essayCount !== undefined &&
    params.essayCount !== null &&
    params.essayCount !== ""
  )
    formData.append("essayCount", String(params.essayCount));
  if (params.generateAB !== undefined && params.generateAB !== null)
    formData.append("generateAB", String(params.generateAB));

  // 讯飞智文 PPT 参数
  if (params.sparkTemplateId)
    formData.append("sparkTemplateId", params.sparkTemplateId);
  if (params.isCardNote !== undefined)
    formData.append("isCardNote", String(params.isCardNote));
  if (params.isFigure !== undefined)
    formData.append("isFigure", String(params.isFigure));

  // 如果有参考文件，附加上传
  if (params.files?.length) {
    for (const file of params.files) {
      formData.append("files", file);
    }
  }

  const res = await fetch(`${API_BASE}/create`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`提交失败: ${res.status}`);
  return res.json();
}

/**
 * 按修改意见重新生成（沿用原任务参数 + 累积修改意见）
 * @param {string} taskId - 原任务 ID（复用同一任务，下载地址不变）
 * @param {string} instruction - 用户提出的修改意见
 * @returns {Promise<{taskId: string, status: string, revisions: string[]}>}
 */
export async function refineCoursewareTask(taskId, instruction) {
  const res = await fetch(`${API_BASE}/${taskId}/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instruction }),
  });
  if (!res.ok) {
    let detail = `修改失败: ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch {
      // 响应体不是 JSON 时沿用状态码提示
    }
    throw new Error(detail);
  }
  return res.json();
}

/**
 * 导出最终内容：把用户已确认的正文渲染为可下载文件（docx / html / pptx）
 * @param {string} taskId
 * @returns {Promise<{taskId: string, status: string}>}
 */
export async function exportCoursewareTask(taskId) {
  const res = await fetch(`${API_BASE}/${taskId}/export`, { method: "POST" });
  if (!res.ok) {
    let detail = `导出失败: ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch {
      // 响应体不是 JSON 时沿用状态码提示
    }
    throw new Error(detail);
  }
  return res.json();
}

/**
 * 建立 SSE 连接，实时监听生成进度与正文增量
 * @param {string} taskId
 * @param {Object} callbacks
 * @param {(text: string) => void} [callbacks.onDelta] - 正文增量（流式追加到消息）
 * @param {(data: {status, progress, stage, filename}) => void} [callbacks.onProgress]
 * @param {(data: {status, filename}) => void} [callbacks.onDone] - status 为 ready/completed 时回调
 * @param {(err: Error) => void} [callbacks.onError]
 * @returns {EventSource}
 */
export function subscribeProgress(taskId, callbacks) {
  const source = new EventSource(`${API_BASE}/${taskId}/stream`);

  // 正文增量：边生成边渲染，避免长时间等待无反馈
  source.addEventListener("delta", (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.text) callbacks.onDelta?.(data.text);
    } catch {
      // 单条增量解析失败不中断整体流
    }
  });

  source.addEventListener("progress", (e) => {
    try {
      const data = JSON.parse(e.data);
      callbacks.onProgress?.(data);

      if (data.status === "ready" || data.status === "completed") {
        callbacks.onDone?.(data);
        source.close();
      }
      if (data.status === "failed") {
        callbacks.onError?.(new Error(data.error || "处理失败"));
        source.close();
      }
    } catch (err) {
      callbacks.onError?.(err);
      source.close();
    }
  });

  source.addEventListener("error", () => {
    // EventSource 自动重连，超过重试次数会触发此事件
    callbacks.onError?.(new Error("SSE 连接断开"));
    source.close();
  });

  return source;
}

/**
 * 下载生成的文件
 * @param {string} taskId
 * @param {string} filename
 */
export function downloadFile(taskId, filename) {
  const a = document.createElement("a");
  a.href = `${API_BASE}/${taskId}/download`;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/**
 * 获取历史记录
 * @returns {Promise<Array>}
 */
export async function getCoursewareHistory() {
  const res = await fetch(`${API_BASE}/list`);
  if (!res.ok) throw new Error(`获取历史失败: ${res.status}`);
  return res.json();
}

/**
 * 删除任务
 * @param {string} taskId
 */
export async function deleteCoursewareTask(taskId) {
  const res = await fetch(`${API_BASE}/${taskId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`删除失败: ${res.status}`);
  return res.json();
}
