import { reactive } from "vue";
import { storageKey } from "../config/storage.js";

const STORAGE_KEY = storageKey("user-profile");

// 个人中心里所有可编辑字段的默认值。
// 注意：这里必须与 ProfileView 的表单字段保持一一对应，
// 否则 persist() 会漏写字段、刷新后表现为「保存了但没保存」。
const DEFAULTS = {
  name: "测试用户",
  avatar: null,
  email: "",
  birthday: "",
  qq: "",
  wechat: "",
  motto: "",
};

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    // 与默认值合并：兼容只有 { name, avatar } 的历史存档
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return { ...DEFAULTS };
}

function persist() {
  const data = {};
  for (const key of Object.keys(DEFAULTS)) data[key] = state[key];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

const state = reactive(load());

export function useUserStore() {
  function getAvatar() {
    return state.avatar || null;
  }

  function getName() {
    return state.name || "";
  }

  function getEmail() {
    return state.email || "";
  }

  /**
   * 更新个人资料并落盘。
   * 只接受 DEFAULTS 里声明过的字段，避免把 UI 态写进存储。
   */
  function updateProfile(data = {}) {
    for (const key of Object.keys(DEFAULTS)) {
      if (data[key] !== undefined) state[key] = data[key];
    }
    persist();
  }

  /** 清空个人资料，恢复默认值 */
  function resetProfile() {
    Object.assign(state, DEFAULTS);
    persist();
  }

  return { state, getAvatar, getName, getEmail, updateProfile, resetProfile };
}
