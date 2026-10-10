// 本地存储键统一前缀 —— 品牌「知启灵枢」（zhi qi ling shu）
// 所有 localStorage key 都从这里取，避免散落各处的旧品牌前缀残留。
export const STORAGE_PREFIX = "zqls";

export function storageKey(name) {
  return `${STORAGE_PREFIX}-${name}`;
}
