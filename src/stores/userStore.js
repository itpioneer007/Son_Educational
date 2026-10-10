import { reactive } from "vue";
import { storageKey } from "../config/storage.js";

const STORAGE_KEY = storageKey("user-profile");

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return { name: "测试用户", avatar: null };
}

function save(data) {
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

  function updateProfile(data) {
    Object.assign(state, data);
    save({ name: state.name, avatar: state.avatar });
  }

  return { state, getAvatar, getName, updateProfile };
}
