import { reactive } from "vue";
import { CHAT_API } from "../config/api.js";

const STORAGE_KEY = "zhike-assistant-sessions";
const ACTIVE_KEY = "zhike-assistant-active";

function uid(prefix = "s") {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return [];
}

function loadActiveId() {
  return localStorage.getItem(ACTIVE_KEY) || null;
}

function saveSessions(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function saveActiveId(id) {
  if (id) localStorage.setItem(ACTIVE_KEY, id);
  else localStorage.removeItem(ACTIVE_KEY);
}

function titleFromMessage(text) {
  const t = text.trim().replace(/\s+/g, " ");
  return t.length > 18 ? `${t.slice(0, 18)}…` : t || "新对话";
}

/**
 * 流式调用后端 Qwen 接口，逐段读取 SSE 返回。
 * @param {Array} messages 多轮对话历史 [{role, content}]
 * @param {object} options { feature }
 * @param {Function} onDelta 每收到一段内容时回调（参数为累积的完整文本）
 * @returns {Promise<string>} 累积的完整回复文本
 */
export async function sendToTongyi(messages, options = {}, onDelta) {
  // 整体超时保护：防止后端/AI 挂起导致 isLoading 永久卡死
  const controller = new AbortController();
  // 生成完整教案/出题草稿可能接近 90 秒，超时设 180s 兜底（仅防真正卡死）
  const TIMEOUT_MS = 180000;
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let res;
  try {
    res = await fetch(CHAT_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
        feature: options.feature || "",
        profile: options.profile || {},
      }),
      signal: controller.signal,
    });
  } catch (e) {
    clearTimeout(timer);
    if (e.name === "AbortError") {
      throw new Error("AI 服务响应超时，请稍后重试");
    }
    throw new Error("无法连接 AI 服务，请确认后端已启动");
  }
  if (!res.ok || !res.body) {
    clearTimeout(timer);
    throw new Error(`AI 服务返回错误（HTTP ${res.status}）`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let full = "";
  let buffer = "";

  while (true) {
    let chunk;
    try {
      chunk = await reader.read();
    } catch (e) {
      clearTimeout(timer);
      if (e.name === "AbortError") {
        throw new Error("AI 服务响应超时，请稍后重试");
      }
      throw e;
    }
    if (chunk.done) break;
    buffer += decoder.decode(chunk.value, { stream: true });

    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const rawEvent = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 2);
      for (const line of rawEvent.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (payload === "[DONE]") continue;
        try {
          const data = JSON.parse(payload);
          if (typeof data.content === "string") {
            full += data.content;
            if (onDelta) onDelta(full);
          } else if (data.error) {
            throw new Error(data.error);
          }
        } catch (err) {
          if (err.message && err.message.includes("AI 服务")) throw err;
          // 忽略无法解析的片段，等待完整事件
        }
      }
    }
  }
  clearTimeout(timer);
  if (!full) throw new Error("AI 服务未返回内容，请稍后重试");
  return full;
}

// 模块级单一响应式状态：组件与逻辑共享同一份 sessions，
// 流式更新与持久化都作用在同一个对象上，切页/刷新都不丢失。
const state = reactive({
  sessions: loadSessions(),
  activeId: loadActiveId(),
});

// 临时会话（定向功能使用，不持久化，切页即丢失）
const ephemeral = reactive({
  session: null,
});

function persistSessions() {
  saveSessions(state.sessions);
}

export function useAssistant() {
  function getSessions() {
    return [...state.sessions].sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return b.updatedAt - a.updatedAt;
    });
  }

  function getActiveSession() {
    // 优先返回临时会话（定向功能）
    if (ephemeral.session) return ephemeral.session;
    return state.sessions.find((s) => s.id === state.activeId) || null;
  }

  function setActive(id) {
    state.activeId = id;
    saveActiveId(id);
  }

  function createSession() {
    const session = {
      id: uid("chat"),
      title: "新对话",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [],
    };
    state.sessions.unshift(session);
    persistSessions();
    setActive(session.id);
    return session;
  }

  function ensureSession() {
    let session = getActiveSession();
    if (!session) {
      session = createSession();
    }
    return session;
  }

  function updateSession(session) {
    const idx = state.sessions.findIndex((s) => s.id === session.id);
    if (idx >= 0) {
      session.updatedAt = Date.now();
      state.sessions[idx] = session;
      persistSessions();
    }
  }

  function deleteSession(id) {
    state.sessions = state.sessions.filter((s) => s.id !== id);
    persistSessions();
    if (state.activeId === id) {
      setActive(state.sessions[0]?.id || null);
    }
  }

  function updateSessionTitle(id, newTitle) {
    const idx = state.sessions.findIndex((s) => s.id === id);
    if (idx >= 0) {
      state.sessions[idx].title = newTitle;
      state.sessions[idx].updatedAt = Date.now();
      persistSessions();
    }
  }

  function pinSession(id) {
    const idx = state.sessions.findIndex((s) => s.id === id);
    if (idx >= 0) {
      state.sessions[idx].isPinned = !state.sessions[idx].isPinned;
      state.sessions[idx].updatedAt = Date.now();
      persistSessions();
    }
  }

  async function sendMessage(content, options = {}) {
    const text = content.trim();
    if (!text) return null;

    // 临时会话（定向功能）：不持久化，切页即丢失
    const isEphemeral = options.ephemeral === true;
    let session;
    if (isEphemeral) {
      if (!ephemeral.session) {
        ephemeral.session = reactive({
          id: uid("tmp"),
          title: titleFromMessage(text),
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: [],
        });
      }
      session = ephemeral.session;
    } else {
      session = ensureSession();
    }

    const userMsg = {
      id: uid("m"),
      role: "user",
      content: text,
      createdAt: Date.now(),
    };
    session.messages.push(userMsg);

    if (session.messages.filter((m) => m.role === "user").length === 1) {
      session.title = titleFromMessage(text);
    }
    if (!isEphemeral) updateSession(session);

    // 先插入空的 AI 占位消息，流式过程中不断填充
    const aiMsg = reactive({
      id: uid("m"),
      role: "assistant",
      content: "",
      createdAt: Date.now(),
    });
    session.messages.push(aiMsg);
    if (!isEphemeral) updateSession(session);

    try {
      const reply = await sendToTongyi(session.messages, options, (full) => {
        aiMsg.content = full;
        if (!isEphemeral) updateSession(session);
        if (typeof options.onDelta === "function") options.onDelta(full);
      });
      aiMsg.content = reply;
      if (!isEphemeral) updateSession(session);
    } catch (err) {
      aiMsg.content = "";
      aiMsg.error = err.message || "AI 服务调用失败";
      if (!isEphemeral) updateSession(session);
    }

    return { session, userMsg, aiMsg };
  }

  function clearEphemeral() {
    ephemeral.session = null;
  }

  function groupSessionsByDate(sessionList) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const groups = { today: [], yesterday: [], earlier: [] };
    for (const s of sessionList) {
      const d = new Date(s.updatedAt);
      d.setHours(0, 0, 0, 0);
      if (d.getTime() === today.getTime()) groups.today.push(s);
      else if (d.getTime() === yesterday.getTime()) groups.yesterday.push(s);
      else groups.earlier.push(s);
    }
    return groups;
  }

  return {
    state,
    getSessions,
    getActiveSession,
    setActive,
    createSession,
    ensureSession,
    deleteSession,
    updateSessionTitle,
    pinSession,
    clearEphemeral,
    sendMessage,
    groupSessionsByDate,
  };
}

export function formatSessionTime(ts) {
  const d = new Date(ts);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  if (isToday) {
    return d.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return d.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}
