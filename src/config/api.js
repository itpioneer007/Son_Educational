/**
 * 后端服务地址集中配置
 *
 * 全站唯一的后端地址来源。此前地址散落在 useAssistant.js / useCoursewareApi.js /
 * FeaturesView.vue 中硬编码，部署或联调换地址要逐处改源码，容易漏改。
 *
 * 覆盖方式：在项目根目录建 .env.local（已在 .gitignore 的 *.local 规则内）
 *   VITE_API_ORIGIN=http://192.168.1.10:8000
 */

export const API_ORIGIN =
  import.meta.env.VITE_API_ORIGIN || "http://localhost:8000";

/** 课件/教案/练习/试卷 任务接口前缀 */
export const API_BASE = `${API_ORIGIN}/api/courseware`;

/** AI 备课助手对话接口（SSE 流式） */
export const CHAT_API = `${API_ORIGIN}/api/chat`;

/** 讯飞智文模板列表接口 */
export const SPARK_TEMPLATES_API = `${API_ORIGIN}/api/spark/templates`;

/**
 * 把后端返回的相对路径（如 /api/skill/templates/x/preview）拼成完整地址。
 * 已是 http(s) 绝对地址时原样返回。
 * @param {string} path
 * @returns {string}
 */
export function apiUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_ORIGIN}${path}`;
}
