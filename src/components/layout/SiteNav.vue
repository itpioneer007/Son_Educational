<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { navItems, userNavItems } from "../../config/nav.js";
import { storageKey } from "../../config/storage.js";

const USER_KEY = storageKey("user");

const route = useRoute();
const menuOpen = ref(false);
const navSolid = ref(false);
const loginOpen = ref(false);
const userMenuOpen = ref(false);
const user = ref(null);

// 根据登录状态获取导航项
const currentNavItems = computed(() => {
  return user.value ? userNavItems : navItems;
});
const loginError = ref("");
const captchaCode = ref("");
const loginForm = ref({
  account: "admin",
  password: "123456",
  captcha: "",
});

const navIcons = {
  home: [
    "M3.5 9.2 10 4l6.5 5.2V16a1 1 0 0 1-1 1h-3.2v-4.6H7.7V17H4.5a1 1 0 0 1-1-1V9.2z",
  ],
  grid: ["M4 4h5v5H4V4zm7 0h5v5h-5V4zM4 11h5v5H4v-5zm7 0h5v5h-5v-5z"],
  spark: ["M10 3l1.3 4 4 1.3-4 1.4-1.3 4-1.3-4-4-1.4 4-1.3L10 3z"],
  chat: [
    "M4 5.5A2.5 2.5 0 0 1 6.5 3h7A2.5 2.5 0 0 1 16 5.5v4A2.5 2.5 0 0 1 13.5 12H9l-4 3v-3.2A2.5 2.5 0 0 1 4 9.5v-4z",
  ],
  book: [
    "M5 4.5A2.5 2.5 0 0 1 7.5 2H16v14H7.5A2.5 2.5 0 0 0 5 18V4.5zM5 4.5A2.5 2.5 0 0 0 2.5 2H2v14h.5A2.5 2.5 0 0 1 5 18",
  ],
  users: [
    "M7.2 9.2a2.7 2.7 0 1 0 0-5.4 2.7 2.7 0 0 0 0 5.4zM2.8 16.5a4.4 4.4 0 0 1 8.8 0M13.2 8.8a2.2 2.2 0 1 0 0-4.4M12.7 12.4a3.6 3.6 0 0 1 4.5 3.5",
  ],
  info: ["M10 17a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM10 9v4M10 6.7h.01"],
  user: ["M10 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM3 17a7 7 0 1 1 14 0"],
  settings: ["M10.3,2C10.7,2,11,2.3,11,2.7v1c0,0.3,0.2,0.6,0.5,0.7l0.9,0.4c0.3,0.1,0.6,0,0.8-0.2l0.7-0.7c0.2-0.2,0.6-0.2,0.8,0l1.4,1.4c0.2,0.2,0.2,0.6,0,0.8l-0.7,0.7c-0.2,0.2-0.3,0.5-0.2,0.8l0.4,0.9c0.1,0.3,0.4,0.5,0.7,0.5h1c0.4,0,0.7,0.3,0.7,0.7v2c0,0.4-0.3,0.7-0.7,0.7h-1c-0.3,0-0.6,0.2-0.7,0.5l-0.4,0.9c-0.1,0.3,0,0.6,0.2,0.8l0.7,0.7c0.2,0.2,0.2,0.6,0,0.8l-1.4,1.4c-0.2,0.2-0.6,0.2-0.8,0l-0.7-0.7c-0.2-0.2-0.5-0.3-0.8-0.2l-0.9,0.4c-0.3,0.1-0.5,0.4-0.5,0.7v1c0,0.4-0.3,0.7-0.7,0.7h-2c-0.4,0-0.7-0.3-0.7-0.7v-1c0-0.3-0.2-0.6-0.5-0.7l-0.9-0.4c-0.3-0.1-0.6,0-0.8,0.2l-0.7,0.7c-0.2,0.2-0.6,0.2-0.8,0L4.2,16.5c-0.2-0.2-0.2-0.6,0-0.8l0.7-0.7c0.2-0.2,0.3-0.5,0.2-0.8l-0.4-0.9c-0.1-0.3-0.4-0.5-0.7-0.5h-1c-0.4,0-0.7-0.3-0.7-0.7v-2c0-0.4,0.3-0.7,0.7-0.7h1c0.3,0,0.6-0.2,0.7-0.5l0.4-0.9c0.1-0.3,0-0.6-0.2-0.8l-0.7-0.7c-0.2-0.2-0.2-0.6,0-0.8l1.4-1.4c0.2-0.2,0.6-0.2,0.8,0l0.7,0.7c0.2,0.2,0.5,0.3,0.8,0.2l0.9-0.4c0.3-0.1,0.5-0.4,0.5-0.7v-1C9.7,2.3,9.9,2,10.3,2z M10.3,9.7c1,0,1.7,0.8,1.7,1.7s-0.8,1.7-1.7,1.7s-1.7-0.8-1.7-1.7S9.3,9.7,10.3,9.7z"],
};

const captchaDisplay = computed(() => captchaCode.value.split(""));

function onScroll() {
  navSolid.value = window.scrollY > 32;
}

function toggleMenu() {
  menuOpen.value = !menuOpen.value;
}

function closeMenu() {
  menuOpen.value = false;
}

function isActive(to) {
  if (to === "/") return route.path === "/";
  return route.path.startsWith(to);
}

function generateCaptcha() {
  const pool = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  captchaCode.value = Array.from(
    { length: 4 },
    () => pool[Math.floor(Math.random() * pool.length)],
  ).join("");
  loginForm.value.captcha = "";
}

function openLogin() {
  closeMenu();
  userMenuOpen.value = false;
  loginError.value = "";
  generateCaptcha();
  loginOpen.value = true;
}

function closeLogin() {
  loginOpen.value = false;
  loginError.value = "";
}

function submitLogin() {
  const accountOk = loginForm.value.account.trim() === "admin";
  const passwordOk = loginForm.value.password === "123456";
  const captchaOk =
    loginForm.value.captcha.trim().toUpperCase() === captchaCode.value;

  if (!accountOk || !passwordOk) {
    loginError.value = "账号或密码不正确";
    return;
  }

  if (!captchaOk) {
    loginError.value = "验证码不正确";
    generateCaptcha();
    return;
  }

  user.value = { account: "admin" };
  localStorage.setItem(USER_KEY, JSON.stringify(user.value));
  loginOpen.value = false;
  loginError.value = "";
}

function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value;
}

function logout() {
  user.value = null;
  userMenuOpen.value = false;
  localStorage.removeItem(USER_KEY);
}

function loadUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (raw) user.value = JSON.parse(raw);
  } catch {
    user.value = null;
  }
}

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  loadUser();
  generateCaptcha();
});

onUnmounted(() => {
  window.removeEventListener("scroll", onScroll);
});
</script>

<template>
  <header class="nav" :class="{ 'nav--solid': navSolid }">
    <div class="nav__inner">
      <RouterLink to="/" class="brand" @click="closeMenu">
        <span class="brand__mark" aria-hidden="true">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="7" fill="url(#navBrandGrad)" />
            <path
              d="M7 18L11 10H13L17 18H15L14.2 16.2H9.8L9 18H7ZM10.4 14.6H13.6L12 10.8L10.4 14.6Z"
              fill="white"
            />
            <path d="M19 10H21V18H19V10Z" fill="white" opacity="0.7" />
            <defs>
              <linearGradient id="navBrandGrad" x1="0" y1="0" x2="28" y2="28">
                <stop stop-color="#0090ff" />
                <stop offset="1" stop-color="#0057d9" />
              </linearGradient>
            </defs>
          </svg>
        </span>
        <span class="brand__name">知启灵枢</span>
      </RouterLink>

      <nav class="nav__links" :class="{ 'nav__links--open': menuOpen }">
        <RouterLink
          v-for="item in currentNavItems"
          :key="item.to"
          :to="item.to"
          class="nav__link"
          :class="{ 'nav__link--active': isActive(item.to) }"
          @click="closeMenu"
        >
          <svg
            class="nav__link-icon"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
          >
            <path
              v-for="path in navIcons[item.icon]"
              :key="path"
              :d="path"
              stroke="currentColor"
              stroke-width="1.45"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="nav__actions">
        <button v-if="!user" class="co-create-btn" @click="openLogin">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path
              d="M10 4v12M4 10h12"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
            />
          </svg>
          开始共创
        </button>

        <div v-else class="user-area">
          <button class="user-chip" @click="toggleUserMenu">
            <span class="user-avatar" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="8" r="4" fill="#ffffff" />
                <path d="M5 20a7 7 0 0 1 14 0" fill="#ffffff" />
              </svg>
            </span>
            <span>{{ user.account }}</span>
            <svg
              class="user-chip__chevron"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M4 6l4 4 4-4"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>

          <Transition name="user-menu">
            <div v-if="userMenuOpen" class="user-menu">
              <button class="user-menu__item" type="button">
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M4 5h12v10H4V5zm3 3h3M7 11h6M13 8h1"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                身份管理
              </button>
              <button
                class="user-menu__item user-menu__item--danger"
                type="button"
                @click="logout"
              >
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M8 5H5v10h3M11 7l3 3-3 3M14 10H8"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                安全退出
              </button>
            </div>
          </Transition>
        </div>

        <button
          class="nav__toggle"
          :aria-expanded="menuOpen"
          aria-label="打开菜单"
          @click="toggleMenu"
        >
          <span :class="{ open: menuOpen }" />
        </button>
      </div>
    </div>

    <Transition name="login">
      <div v-if="loginOpen" class="login-layer" @click.self="closeLogin">
        <form class="login-card" @submit.prevent="submitLogin">
          <button
            class="login-card__close"
            type="button"
            aria-label="关闭登录弹窗"
            @click="closeLogin"
          >
            <svg viewBox="0 0 20 20" fill="none">
              <path
                d="M6 6l8 8M14 6l-8 8"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
              />
            </svg>
          </button>

          <div class="login-card__head">
            <span class="login-card__avatar" aria-hidden="true">
              <svg viewBox="0 0 28 28" fill="none">
                <circle cx="14" cy="10" r="5" fill="#ffffff" />
                <path d="M5.5 24a8.5 8.5 0 0 1 17 0" fill="#ffffff" />
              </svg>
            </span>
            <div>
              <h2>账号登录</h2>
              <p>登录后进入共创身份</p>
            </div>
          </div>

          <label class="login-field">
            <span>账号</span>
            <input
              v-model="loginForm.account"
              type="text"
              autocomplete="username"
            />
          </label>

          <label class="login-field">
            <span>密码</span>
            <input
              v-model="loginForm.password"
              type="password"
              autocomplete="current-password"
            />
          </label>

          <label class="login-field">
            <span>验证码</span>
            <div class="captcha-row">
              <input
                v-model="loginForm.captcha"
                type="text"
                maxlength="4"
                placeholder="输入验证码"
              />
              <button
                class="captcha-code"
                type="button"
                title="刷新验证码"
                @click="generateCaptcha"
              >
                <span
                  v-for="(char, index) in captchaDisplay"
                  :key="`${char}-${index}`"
                  >{{ char }}</span
                >
              </button>
            </div>
          </label>

          <p v-if="loginError" class="login-error">{{ loginError }}</p>
          <button class="login-submit" type="submit">登录</button>
        </form>
      </div>
    </Transition>
  </header>
</template>

<style scoped>
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 18px 0;
  transition:
    background 0.35s var(--ease-out),
    box-shadow 0.35s,
    padding 0.35s;
}

.nav--solid {
  padding: 12px 0;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px) saturate(1.4);
  box-shadow: 0 1px 0 var(--border);
}

.nav__inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 28px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  text-decoration: none;
}

.brand__name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.0625rem;
  color: var(--ink);
}

.nav__links {
  display: flex;
  align-items: center;
  gap: 2px;
  margin: 0 auto;
}

.nav__link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 12px;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--ink-soft);
  border-radius: 10px;
  text-decoration: none;
  transition:
    color 0.2s,
    background 0.2s;
}

.nav__link-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: #4e7ca8;
}

.nav__link:hover {
  color: var(--ink);
  background: rgba(10, 15, 26, 0.04);
}

.nav__link--active {
  color: var(--accent-deep);
  background: rgba(0, 119, 230, 0.08);
}

.nav__link--active .nav__link-icon {
  color: var(--accent);
}

.nav__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.co-create-btn,
.user-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
  transition:
    transform 0.22s var(--ease-spring),
    box-shadow 0.22s,
    background 0.22s;
}

.co-create-btn {
  padding: 0 18px;
  background: var(--ink);
  color: #fff;
  font-size: 0.88rem;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(10, 15, 26, 0.12);
}

.co-create-btn svg {
  width: 16px;
  height: 16px;
}

.co-create-btn:hover,
.user-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(10, 15, 26, 0.14);
}

.user-area {
  position: relative;
}

.user-chip {
  padding: 4px 10px 4px 5px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(10, 15, 26, 0.08);
  color: #2d5d8f;
  font-size: 0.86rem;
  font-weight: 800;
}

.user-avatar,
.login-card__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(145deg, #48a2ff, #1f70d4);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.user-avatar {
  width: 32px;
  height: 32px;
}

.user-avatar svg {
  width: 22px;
  height: 22px;
}

.user-chip__chevron {
  width: 14px;
  height: 14px;
}

.user-menu {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  min-width: 190px;
  padding: 8px 0;
  border: 1px solid rgba(10, 15, 26, 0.08);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 44px rgba(10, 15, 26, 0.12);
  overflow: hidden;
}

.user-menu__item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 18px;
  border: none;
  background: transparent;
  color: #5d7488;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  text-align: left;
}

.user-menu__item + .user-menu__item {
  border-top: 1px solid rgba(10, 15, 26, 0.08);
}

.user-menu__item:hover {
  background: rgba(0, 119, 230, 0.06);
}

.user-menu__item--danger {
  color: #f04438;
}

.user-menu__item svg {
  width: 20px;
  height: 20px;
}

.nav__toggle {
  display: none;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
}

.nav__toggle span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--ink);
  position: relative;
  transition: background 0.2s;
}

.nav__toggle span::before,
.nav__toggle span::after {
  content: "";
  position: absolute;
  left: 0;
  width: 100%;
  height: 2px;
  background: var(--ink);
  transition: transform 0.25s var(--ease-out);
}

.nav__toggle span::before {
  top: -6px;
}
.nav__toggle span::after {
  top: 6px;
}
.nav__toggle span.open {
  background: transparent;
}
.nav__toggle span.open::before {
  transform: translateY(6px) rotate(45deg);
}
.nav__toggle span.open::after {
  transform: translateY(-6px) rotate(-45deg);
}

.login-layer {
  position: fixed;
  inset: 0;
  z-index: 220;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 32, 52, 0.22);
  backdrop-filter: blur(12px);
}

.login-card {
  position: relative;
  width: min(420px, 100%);
  padding: 28px;
  border-radius: 26px;
  background: #fff;
  border: 1px solid rgba(10, 15, 26, 0.08);
  box-shadow: 0 30px 80px rgba(10, 15, 26, 0.18);
}

.login-card__close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 12px;
  background: rgba(10, 15, 26, 0.04);
  color: var(--ink-muted);
  cursor: pointer;
}

.login-card__close svg {
  width: 17px;
  height: 17px;
}

.login-card__head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
}

.login-card__avatar {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.login-card__avatar svg {
  width: 32px;
  height: 32px;
}

.login-card__head h2 {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--ink);
}

.login-card__head p {
  margin-top: 4px;
  font-size: 0.84rem;
  color: var(--ink-muted);
}

.login-field {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--ink-soft);
}

.login-field input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid rgba(10, 15, 26, 0.12);
  border-radius: 14px;
  outline: none;
  font-size: 0.92rem;
  color: var(--ink);
  background: #fff;
}

.login-field input:focus {
  border-color: rgba(0, 119, 230, 0.4);
  box-shadow: 0 0 0 4px rgba(0, 119, 230, 0.08);
}

.captcha-row {
  display: grid;
  grid-template-columns: 1fr 110px;
  gap: 10px;
}

.captcha-code {
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid rgba(0, 119, 230, 0.15);
  border-radius: 14px;
  background:
    linear-gradient(135deg, rgba(0, 119, 230, 0.08), rgba(0, 194, 212, 0.1)),
    #f5fbff;
  color: var(--accent-deep);
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 800;
  cursor: pointer;
  letter-spacing: 0.06em;
}

.captcha-code span:nth-child(2n) {
  transform: translateY(1px) rotate(-6deg);
}

.captcha-code span:nth-child(2n + 1) {
  transform: translateY(-1px) rotate(5deg);
}

.login-error {
  margin: 2px 0 12px;
  font-size: 0.82rem;
  color: #f04438;
}

.login-submit {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 999px;
  background: var(--ink);
  color: #fff;
  font-size: 0.95rem;
  font-weight: 800;
  cursor: pointer;
  transition:
    transform 0.22s var(--ease-spring),
    box-shadow 0.22s;
}

.login-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(10, 15, 26, 0.16);
}

.login-enter-active,
.login-leave-active,
.user-menu-enter-active,
.user-menu-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.login-enter-from,
.login-leave-to {
  opacity: 0;
}

.login-enter-from .login-card,
.login-leave-to .login-card {
  transform: translateY(10px) scale(0.98);
}

.user-menu-enter-from,
.user-menu-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 1040px) {
  .nav__link span {
    display: none;
  }

  .nav__link {
    padding: 9px;
  }
}

@media (max-width: 900px) {
  .nav__links {
    position: fixed;
    top: 72px;
    left: 16px;
    right: 16px;
    flex-direction: column;
    align-items: stretch;
    padding: 12px;
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    backdrop-filter: blur(20px);
    box-shadow: 0 16px 48px rgba(10, 15, 26, 0.1);
    opacity: 0;
    visibility: hidden;
    transform: translateY(-8px);
    transition:
      opacity 0.3s,
      transform 0.3s,
      visibility 0.3s;
  }

  .nav__links--open {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
  }

  .nav__link {
    width: 100%;
    justify-content: center;
    padding: 12px;
  }

  .nav__link span {
    display: inline;
  }

  .nav__toggle {
    display: flex;
  }
  .co-create-btn {
    padding: 0 14px;
  }
}
</style>
