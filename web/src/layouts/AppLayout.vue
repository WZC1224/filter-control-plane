<template>
  <el-container class="app-shell">
    <div
      v-if="mobile && !collapsed"
      class="aside-mask"
      aria-hidden="true"
      @click="collapsed = true"
    />
    <el-aside :width="asideWidth" class="app-aside" :class="{ 'app-aside--open': mobile && !collapsed }">
      <div class="brand" :class="{ 'brand--mini': collapsed && !mobile }">
        <span class="brand-mark" aria-hidden="true" />
        <span v-if="!collapsed || mobile" class="brand-text">筛选控制台</span>
      </div>
      <el-menu
        :default-active="active"
        :collapse="collapsed && !mobile"
        router
        class="app-menu"
        background-color="transparent"
        text-color="var(--el-text-color-primary)"
        active-text-color="var(--el-color-primary)"
        :collapse-transition="false"
        @select="onMenuSelect"
      >
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <span>概览</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon>
          <span>任务列表</span>
        </el-menu-item>
        <el-menu-item index="/tasks/create">
          <el-icon><Plus /></el-icon>
          <span>新建任务</span>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><Ticket /></el-icon>
          <span>订单</span>
        </el-menu-item>
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <span>价目</span>
        </el-menu-item>
        <el-menu-item index="/bills">
          <el-icon><Wallet /></el-icon>
          <span>账单</span>
        </el-menu-item>
        <el-menu-item index="/notices">
          <el-icon><Bell /></el-icon>
          <span>公告</span>
        </el-menu-item>
        <el-menu-item index="/account">
          <el-icon><User /></el-icon>
          <span>账号</span>
        </el-menu-item>
        <el-menu-item index="/system">
          <el-icon><Setting /></el-icon>
          <span>系统</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="app-main-wrap">
      <el-header class="app-header" height="56px">
        <el-button text class="collapse-btn" :aria-label="collapsed ? '展开侧栏' : '收起侧栏'" @click="toggleCollapse">
          <el-icon :size="18"><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        </el-button>
        <div class="header-spacer" />
        <el-button
          text
          class="theme-btn"
          :aria-label="theme.isDark ? '切换白天模式' : '切换黑夜模式'"
          @click="theme.toggle()"
        >
          <el-icon :size="18"><Moon v-if="!theme.isDark" /><Sunny v-else /></el-icon>
        </el-button>
        <el-tag v-if="balanceText !== null" size="small" effect="plain" type="primary" class="bal">
          余额 {{ balanceText }}
        </el-tag>
        <span class="who">{{ user.username }}</span>
        <el-button text type="primary" @click="onLogout">退出</el-button>
      </el-header>
      <el-main class="app-main">
        <el-alert
          v-if="tokenKind === 'agent'"
          class="token-banner"
          type="warning"
          show-icon
          :closable="false"
          title="下游为 agent_token"
          description="余额/类型/建任务/查询/下载可用。任务列表、订单、价目、公告、账单需把 .env 的 DATA818_TOKEN 换成带过期时间的登录 JWT。"
        />
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, Expand, Fold, Goods, List, Moon, Odometer, Plus, Setting, Sunny, Ticket, User, Wallet } from '@element-plus/icons-vue'
import { balanceApi, healthApi } from '@/api/meta'
import { useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'

const MOBILE_MQ = '(max-width: 768px)'
const COLLAPSE_KEY = 'fcp-aside-collapsed'

const user = useUserStore()
const theme = useThemeStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const mobile = ref(false)
const balanceRaw = ref<number | string | null>(null)
const tokenKind = ref('')
let timer: ReturnType<typeof setInterval> | undefined
let mq: MediaQueryList | undefined

function readDesktopCollapse(): boolean {
  try {
    return localStorage.getItem(COLLAPSE_KEY) === '1'
  } catch {
    return false
  }
}

function writeDesktopCollapse(v: boolean) {
  try {
    localStorage.setItem(COLLAPSE_KEY, v ? '1' : '0')
  } catch {
    // ignore quota / private mode
  }
}

function toggleCollapse() {
  collapsed.value = !collapsed.value
  if (!mobile.value) writeDesktopCollapse(collapsed.value)
}

const asideWidth = computed(() => {
  if (mobile.value) return '0px'
  return collapsed.value ? '64px' : '220px'
})

const active = computed(() => {
  const p = route.path
  if (p.startsWith('/tasks/create')) return '/tasks/create'
  if (p.startsWith('/tasks/') && p !== '/tasks') return '/tasks'
  if (p.startsWith('/notices/')) return '/notices'
  return p
})

const balanceText = computed(() => {
  if (balanceRaw.value === null || balanceRaw.value === undefined) return null
  const n = Number(balanceRaw.value)
  return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(balanceRaw.value)
})

async function loadBalance() {
  try {
    const r = await balanceApi()
    balanceRaw.value = r.balance ?? null
  } catch {
    balanceRaw.value = null
  }
}

async function loadHealth() {
  try {
    const h = await healthApi()
    tokenKind.value = h.tokenKind || ''
  } catch {
    tokenKind.value = ''
  }
}

function onLogout() {
  user.logout()
  router.replace({ name: 'login' })
}

function onMenuSelect() {
  if (mobile.value) collapsed.value = true
}

function syncMobile(e?: MediaQueryList | MediaQueryListEvent) {
  const matches = e ? e.matches : !!mq?.matches
  const wasMobile = mobile.value
  mobile.value = matches
  if (matches && !wasMobile) collapsed.value = true
  if (!matches && wasMobile) collapsed.value = readDesktopCollapse()
}

onMounted(() => {
  mq = window.matchMedia(MOBILE_MQ)
  mobile.value = mq.matches
  collapsed.value = mq.matches ? true : readDesktopCollapse()
  mq.addEventListener('change', syncMobile)
  loadBalance()
  loadHealth()
  timer = setInterval(loadBalance, 60000)
})

onUnmounted(() => {
  mq?.removeEventListener('change', syncMobile)
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.app-shell {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--app-bg, #eef5fb);
}

.app-aside {
  flex-shrink: 0;
  height: 100%;
  background: linear-gradient(
    180deg,
    var(--app-aside-start) 0%,
    var(--app-aside-mid) 40%,
    var(--app-aside-end) 100%
  );
  border-right: 1px solid var(--el-border-color-lighter);
  transition: width 0.2s ease, transform 0.2s ease;
  overflow-x: hidden;
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  height: 56px;
  padding: 0 1rem;
  border-bottom: 1px solid var(--app-brand-border);
}

.brand--mini {
  justify-content: center;
  padding: 0;
}

.brand-mark {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 0.2rem;
  background: var(--el-color-primary);
  flex-shrink: 0;
}

.brand-text {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.app-menu {
  border-right: none;
  padding: 0.5rem 0;
  height: calc(100% - 56px);
  overflow-y: auto;
}

.app-main-wrap {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.app-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 1rem;
  background: var(--app-header-bg);
  border-bottom: 1px solid var(--el-border-color-lighter);
  backdrop-filter: blur(8px);
}

.header-spacer {
  flex: 1;
  min-width: 0;
}

.bal {
  margin-right: 0.25rem;
}

.who {
  color: var(--el-text-color-secondary);
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 8rem;
}

.app-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: 1.5rem 1.75rem 2.75rem;
}

.token-banner {
  margin-bottom: 1rem;
}

.aside-mask {
  display: none;
}

@media (max-width: 768px) {
  .app-aside {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 30;
    height: 100vh;
    height: 100dvh;
    width: 220px !important;
    transform: translateX(-100%);
    box-shadow: none;
  }

  .app-aside--open {
    transform: translateX(0);
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.18);
  }

  .aside-mask {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 25;
    background: rgba(0, 0, 0, 0.35);
  }

  .app-main-wrap {
    width: 100%;
    margin-left: 0;
  }

  .app-main {
    padding: 1.125rem 1rem 2.25rem;
  }

  .who {
    max-width: 4.5rem;
  }

  .bal {
    display: none;
  }
}
</style>
