<template>
  <div class="page-panel">
    <header class="page-head">
      <h1 class="page-title">概览</h1>
      <p class="page-sub">任务状态汇总、下游余额与快捷入口</p>
    </header>

    <el-alert
      v-if="error"
      class="mb"
      type="error"
      :title="error"
      show-icon
      :closable="false"
    >
      <el-button size="small" @click="load">重试</el-button>
    </el-alert>

    <el-alert
      v-for="n in topNotices"
      :key="String(n.id)"
      class="mb notice-alert"
      :type="noticeAlertType(n.level)"
      :title="n.title"
      :description="previewNotice(n.contentMd)"
      show-icon
      closable
      @click="goNotice(n)"
    />

    <div v-loading="loading" class="stat-row">
      <button type="button" class="stat clickable" @click="goTasks()">
        <div class="stat-label">全部任务</div>
        <div class="stat-value">{{ total }}</div>
      </button>
      <button type="button" class="stat clickable" @click="goTasks(0)">
        <div class="stat-label">排队</div>
        <div class="stat-value">{{ counts[0] }}</div>
      </button>
      <button type="button" class="stat clickable" @click="goTasks(2)">
        <div class="stat-label">进行中</div>
        <div class="stat-value">{{ counts[2] }}</div>
      </button>
      <button type="button" class="stat clickable" @click="goTasks(1)">
        <div class="stat-label">已完成</div>
        <div class="stat-value">{{ counts[1] }}</div>
      </button>
      <button type="button" class="stat clickable" @click="goTasks(-1)">
        <div class="stat-label">失败</div>
        <div class="stat-value">{{ counts[-1] }}</div>
      </button>
      <button type="button" class="stat clickable" @click="$router.push({ name: 'system' })">
        <div class="stat-label">下游余额</div>
        <div class="stat-value bal">{{ balanceText }}</div>
      </button>
    </div>

    <el-card shadow="never" class="mb">
      <div class="meta-line">
        <span>下游适配器</span>
        <el-tag size="small" :type="adapter === 'data818' ? 'success' : 'info'" effect="plain">
          {{ adapter || '…' }}
        </el-tag>
      </div>
      <div class="actions">
        <el-button type="primary" @click="$router.push({ name: 'task-create' })">新建任务</el-button>
        <el-button @click="$router.push({ name: 'tasks' })">查看列表</el-button>
        <el-button @click="$router.push({ name: 'products' })">价目</el-button>
        <el-button @click="$router.push({ name: 'orders' })">订单</el-button>
        <el-button @click="$router.push({ name: 'bills' })">账单</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="mb">
      <template #header>
        <div class="list-header">
          <h2 class="section-title">近 30 日完成量</h2>
          <span class="list-meta">合计 {{ statsTotal }}</span>
        </div>
      </template>
      <el-empty v-if="!loading && !statBars.length" description="暂无统计" />
      <div v-else class="bars">
        <div v-for="d in statBars" :key="d.date" class="bar-row">
          <span class="bar-date">{{ d.date.slice(5) }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: barWidth(d.total) }" />
          </div>
          <span class="bar-num">{{ d.total }}</span>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="list-header">
          <h2 class="section-title">最近任务</h2>
          <el-button link type="primary" @click="$router.push({ name: 'tasks' })">全部</el-button>
        </div>
      </template>
      <el-empty v-if="!loading && !recent.length" description="暂无任务" />
      <el-table
        v-else
        :data="recent"
        stripe
        class="click-table"
        @row-click="onRecentClick"
      >
        <el-table-column label="任务号" min-width="140">
          <template #default="{ row }">
            <router-link
              class="mono link"
              :to="{ name: 'task-detail', params: { taskNo: row.taskNo } }"
              @click.stop
            >
              {{ row.taskNo }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="plain">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="90">
          <template #default="{ row }">{{ row.progress ?? '-' }}%</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { balanceApi, healthApi, statisticsApi, type StatDay } from '@/api/meta'
import { listNoticesApi } from '@/api/notice'
import { listTasksApi } from '@/api/task'
import { statusText, statusType } from '@/utils/taskDisplay'
import type { NoticeItem, TaskItem } from '@/types/api'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const adapter = ref('')
const balanceRaw = ref<number | string | null>(null)
const tasks = ref<TaskItem[]>([])
const series = ref<StatDay[]>([])
const notices = ref<NoticeItem[]>([])
const counts = reactive<Record<number, number>>({ [-1]: 0, 0: 0, 1: 0, 2: 0, 3: 0 })

const total = computed(() => tasks.value.length)
const recent = computed(() => tasks.value.slice(0, 8))
const topNotices = computed(() => notices.value.slice(0, 2))
const balanceText = computed(() => {
  if (balanceRaw.value === null || balanceRaw.value === undefined) return '—'
  const n = Number(balanceRaw.value)
  return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(balanceRaw.value)
})
const statsTotal = computed(() => series.value.reduce((s, d) => s + (d.total || 0), 0))
const statBars = computed(() => {
  const nonzero = series.value.filter((d) => (d.total || 0) > 0)
  if (nonzero.length) return nonzero.slice(-14)
  return series.value.slice(-7)
})
const maxBar = computed(() => Math.max(1, ...statBars.value.map((d) => d.total || 0)))

function barWidth(n: number) {
  return `${Math.max(4, Math.round(((n || 0) / maxBar.value) * 100))}%`
}

function noticeAlertType(level?: string): 'info' | 'warning' | 'error' | 'success' {
  const v = (level || '').toUpperCase()
  if (v.includes('WARN')) return 'warning'
  if (v.includes('ERR') || v.includes('CRIT')) return 'error'
  if (v.includes('SUCC')) return 'success'
  return 'info'
}

function previewNotice(md?: string) {
  const t = (md || '').trim()
  if (t.length <= 120) return t
  return `${t.slice(0, 120)}…`
}

function goNotice(n: NoticeItem) {
  if (n.id == null) return
  router.push({ name: 'notice-detail', params: { noticeId: String(n.id) } })
}

function onRecentClick(row: TaskItem) {
  if (!row.taskNo) return
  router.push({ name: 'task-detail', params: { taskNo: row.taskNo } })
}

function goTasks(taskStatus?: number) {
  router.push({
    name: 'tasks',
    query: taskStatus === undefined ? {} : { taskStatus: String(taskStatus) },
  })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [h, list, bal, stats, msgs] = await Promise.all([
      healthApi(),
      listTasksApi({ pageNo: 1, pageSize: 50 }),
      balanceApi().catch(() => null),
      statisticsApi().catch(() => null),
      listNoticesApi().catch(() => []),
    ])
    adapter.value = h.adapter
    tasks.value = list.data || []
    balanceRaw.value = bal?.balance ?? null
    series.value = stats?.series || []
    notices.value = msgs || []
    for (const k of Object.keys(counts)) counts[Number(k)] = 0
    for (const t of tasks.value) {
      const s = t.status
      if (s === -1 || s === 0 || s === 1 || s === 2 || s === 3) counts[s] += 1
    }
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.stat {
  padding: 1rem 1.1rem;
  background: var(--app-surface);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: var(--el-border-radius-base);
  text-align: left;
  color: inherit;
  font: inherit;
}

.stat.clickable {
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.stat.clickable:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-fill-color-blank);
}

.stat.clickable:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
}

.stat-label {
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
}

.stat-value {
  margin-top: 0.35rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-color-primary-dark-2);
}

.stat-value.bal {
  font-size: 1.25rem;
}

.meta-line {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.list-meta {
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
}

.bars {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.bar-row {
  display: grid;
  grid-template-columns: 3rem 1fr 3rem;
  align-items: center;
  gap: 0.5rem;
}

.bar-date {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
}

.bar-track {
  height: 0.5rem;
  background: var(--el-fill-color);
  border-radius: 0.25rem;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--el-color-primary);
  border-radius: 0.25rem;
}

.bar-num {
  font-size: 0.75rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.link {
  color: var(--el-color-primary);
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

:deep(.click-table .el-table__row) {
  cursor: pointer;
}

.mb {
  margin-bottom: 1rem;
}

.notice-alert {
  cursor: pointer;
}

.notice-alert:hover {
  opacity: 0.92;
}

@media (max-width: 720px) {
  .stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .stat-row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
