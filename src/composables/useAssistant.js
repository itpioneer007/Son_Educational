import { reactive } from "vue";
import { CHAT_API } from "../config/api.js";
import { storageKey } from "../config/storage.js";

const STORAGE_KEY = storageKey("assistant-sessions");
const ACTIVE_KEY = storageKey("assistant-active");

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
 *
 * 超时采用「两段预算」而不是单一总时长：模型首 token 延迟与总时长都可能非常长
 * （实测 Qwen 首 token 可达 125s、单条回答总时长 178s），若用「从请求发起起算的
 * 总时长」做上限，健康的长回答会在写到一半时被中途掐断 —— 用户看到的就是
 * 「明明已经在输出内容，过一会儿突然全没了，还报超时」。
 * 因此改为：
 *   - 首字预算：等待第一个字期间给足 300s（上游排队/冷启可能很慢）；
 *   - 静默预算：首字到达后，只要 60s 内还有新内容就不断续期，
 *     只有真的「卡住不说话」才判定超时。
 * 每次拿到内容都重新计时，健康的慢流永远不会被误杀。
 *
 * @param {Array} messages 多轮对话历史 [{role, content}]
 * @param {object} options { profile, onDelta }
 * @param {Function} onDelta 每收到一段内容时回调（参数为累积的完整文本）
 * @returns {Promise<string>} 累积的完整回复文本
 */
export async function sendToTongyi(messages, options = {}, onDelta) {
  const controller = new AbortController();
  const FIRST_TOKEN_MS = 300000; // 首字预算：5 分钟
  const IDLE_MS = 60000; // 静默预算：首字之后连续 60s 无新内容才算挂死

  let timer = null;
  // 重新计时；每收到一段内容就调用一次，把「总时长上限」变成「静默时长上限」
  const arm = (ms) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => controller.abort(), ms);
  };
  const disarm = () => {
    if (timer) clearTimeout(timer);
    timer = null;
  };
  arm(FIRST_TOKEN_MS);

  // 超时错误带上已产出的部分正文：上层据此保留内容，而不是整段清空
  const timeoutError = (partial) => {
    const e = new Error("AI 服务响应超时，请稍后重试");
    e.partial = partial;
    e.isTimeout = true;
    return e;
  };

  let res;
  try {
    res = await fetch(CHAT_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
        profile: options.profile || {},
      }),
      signal: controller.signal,
    });
  } catch (e) {
    disarm();
    if (e.name === "AbortError") throw timeoutError("");
    throw new Error("无法连接 AI 服务，请确认后端已启动");
  }
  if (!res.ok || !res.body) {
    disarm();
    throw new Error(`AI 服务返回错误（HTTP ${res.status}）`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let full = "";
  let buffer = "";

  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      buffer += decoder.decode(chunk.value, { stream: true });

      let idx;
      let done = false;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        const rawEvent = buffer.slice(0, idx).trim();
        buffer = buffer.slice(idx + 2);
        for (const line of rawEvent.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (payload === "[DONE]") {
            done = true;
            break;
          }
          // 先单独完成 JSON 解析：解析失败只跳过该片段，
          // 不能和后端明确返回的 error 混在一起被忽略。
          let data;
          try {
            data = JSON.parse(payload);
          } catch {
            continue; // 无法解析的片段，等待完整事件
          }
          if (typeof data.content === "string") {
            full += data.content;
            // 首字一到达即从「首字预算」切到「静默预算」，此后每来一段都续期
            arm(IDLE_MS);
            if (onDelta) onDelta(full);
          } else if (data.error) {
            // 后端明确报错：把已产出的部分一起带出去，避免用户丢掉半截回答
            const e = new Error(data.error);
            e.partial = full;
            throw e;
          }
        }
        if (done) break;
      }
      if (done) break;
    }
    disarm();
  } catch (e) {
    disarm();
    if (e.name === "AbortError") throw timeoutError(full);
    // 后端 error / 网络中断：同样保留已产出的内容
    if (e.partial === undefined) e.partial = full;
    throw e;
  }

  if (!full) throw new Error("AI 服务未返回内容，请稍后重试");
  return full;
}

// 模块级单一响应式状态：组件与逻辑共享同一份 sessions，
// 流式更新与持久化都作用在同一个对象上，切页/刷新都不丢失。
const state = reactive({
  sessions: loadSessions(),
  activeId: loadActiveId(),
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

  // 流式期间每个 token 都会调用 updateSession，而 persistSessions 会
  // JSON.stringify 整个会话数组并同步写入 localStorage。
  // 实测单条回答 924 个增量 → 924 次同步写盘，纯属开销且会持续占用主线程。
  // 流式阶段改为节流落盘（保证最终态一定落盘），内存态仍然逐帧更新、不影响渲染。
  let persistTimer = null;
  function schedulePersist() {
    if (persistTimer) return;
    persistTimer = setTimeout(() => {
      persistTimer = null;
      persistSessions();
    }, 500);
  }
  function flushPersist() {
    if (persistTimer) {
      clearTimeout(persistTimer);
      persistTimer = null;
    }
    persistSessions();
  }

  function updateSession(session, opts = {}) {
    const idx = state.sessions.findIndex((s) => s.id === session.id);
    if (idx >= 0) {
      session.updatedAt = Date.now();
      state.sessions[idx] = session;
      if (opts.throttle) schedulePersist();
      else flushPersist();
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

    const session = ensureSession();

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
    updateSession(session);

    // 先插入空的 AI 占位消息，流式过程中不断填充
    const aiMsg = reactive({
      id: uid("m"),
      role: "assistant",
      content: "",
      createdAt: Date.now(),
    });
    session.messages.push(aiMsg);
    updateSession(session);

    // 送给模型的历史要剔除「刚插入、内容还是空的」这条 assistant 占位消息，
    // 否则会把一个空的 assistant turn 也发给模型。
    const history = session.messages
      .filter((m) => !(m.role === "assistant" && !m.content))
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const reply = await sendToTongyi(history, options, (full) => {
        aiMsg.content = full;
        updateSession(session, { throttle: true });
        if (typeof options.onDelta === "function") options.onDelta(full);
      });
      aiMsg.content = reply;
      updateSession(session);
    } catch (err) {
      // 关键：超时/中断都不代表已生成的内容无效。
      // 先前这里无条件 `aiMsg.content = ""`，会把用户已经看到的半截回答整段抹掉，
      // 表现为「明明在输出，突然全没了」。
      // 现在保留已产出部分，仅补充一条中断说明；完全没产出时才算失败。
      const partial = err.partial || aiMsg.content || "";
      if (partial) {
        aiMsg.content = partial;
        aiMsg.interrupted = true;
        aiMsg.error = err.isTimeout
          ? "回答未完成（服务超时），以上为已生成内容"
          : `回答未完成：${err.message || "连接中断"}`;
      } else {
        aiMsg.content = "";
        aiMsg.error = err.message || "AI 服务调用失败";
      }
      updateSession(session);
    }

    return { session, userMsg, aiMsg };
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
