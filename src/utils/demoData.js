// 演示数据工具
// ---------------------------------------------------------------------------
// 比赛演示环境没有真实后端数据源，页面上的浏览量、热度、评分等只能由前端生成。
// 直接用 Math.random() 有两个问题：① 每次重渲染数值都会跳，一眼看出是假数据；
// ② 无法表现"随时间增长"的活性。
// 这里改用「确定性伪随机 + 时间锚点」：同一个输入永远得到同一个结果，
// 但会随自然日推进而缓慢增长，看起来就像真的有人在用。
// ---------------------------------------------------------------------------

/** 32 位字符串哈希（FNV-1a），把任意 id 稳定地映射成种子 */
export function hashSeed(str) {
  let h = 2166136261;
  const s = String(str ?? "");
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** mulberry32：小巧的确定性伪随机发生器，返回 [0, 1) */
export function seededRandom(seed) {
  let a = (Number(seed) || 0) >>> 0;
  return function next() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 稳定整数：同一 seed 永远得到 [min, max] 内的同一个值 */
export function seededInt(seed, min, max) {
  if (max <= min) return min;
  const rand = seededRandom(hashSeed(seed));
  return Math.floor(min + rand() * (max - min + 1));
}

/**
 * 缓慢增长的计数：同一自然日内恒定，每过一天增加 perDay 上下浮动一点。
 * 结果形如 base、base+1、base+3 …… 像真实的累计阅读量 / 下载量。
 *
 * @param {string} seed    稳定种子（同一 seed 每次结果一致）
 * @param {number} base    起始值
 * @param {number} perDay  每天大致增量
 * @param {number} daysAgo 从「多少天前」开始累计（默认 30 天）
 */
export function growingCount(seed, base, perDay, daysAgo = 30) {
  const elapsed = Math.max(0, Math.round(Number(daysAgo) || 0));
  const rand = seededRandom(hashSeed(`${seed}:growth`));
  let value = base;
  for (let i = 0; i < elapsed; i += 1) {
    value += perDay * (0.6 + rand() * 0.8);
  }
  return Math.round(value);
}

/** 本地日期键：2026-10-10 */
export function dateKey(date = new Date()) {
  const d = new Date(date);
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

/** 简短日期：10.10 */
export function shortDate(date = new Date()) {
  const d = new Date(date);
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${m}.${day}`;
}

/** 把大数字格式化成 1.2w / 3562 这种更"像真实平台"的写法 */
export function formatCount(value) {
  const n = Number(value) || 0;
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(Math.round(n));
}
