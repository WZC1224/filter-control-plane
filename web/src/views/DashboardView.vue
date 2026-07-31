<template>
  <div class="page-panel page-panel--fill dash">
    <header class="page-head dash-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">概览</h1>
          <p class="page-sub">近 30 日完成趋势与近期任务</p>
        </div>
        <div class="page-head-actions">
          <el-button type="primary" @click="$router.push({ name: 'task-create' })">新建任务</el-button>
          <el-button text type="primary" @click="$router.push({ name: 'tasks' })">全部任务</el-button>
        </div>
      </div>
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
      v-if="topNotice"
      class="mb notice-alert"
      :type="noticeAlertType(topNotice.level)"
      :title="topNotice.title"
      :description="previewNotice(topNotice.contentMd)"
      show-icon
      closable
      @click="goNotice(topNotice)"
    />

    <div v-loading="loading" class="kpi-row mb">
      <button type="button" class="kpi" @click="goTasks()">
        <span class="kpi-label">任务总数</span>
        <span class="kpi-value">{{ total }}</span>
        <span class="kpi-foot">排队 {{ counts[0] }} · 失败 {{ counts[-1] }}</span>
      </button>
      <button type="button" class="kpi" @click="goTasks(2)">
        <span class="kpi-label">进行中</span>
        <span class="kpi-value">{{ counts[2] }}</span>
        <span class="kpi-foot">点击查看列表</span>
      </button>
      <button type="button" class="kpi" @click="goTasks(1)">
        <span class="kpi-label">已完成</span>
        <span class="kpi-value">{{ counts[1] }}</span>
        <span class="kpi-foot">本页样本内统计</span>
      </button>
      <button type="button" class="kpi" @click="$router.push({ name: 'system' })">
        <span class="kpi-label">下游余额</span>
        <span class="kpi-value kpi-value--sm">{{ balanceText }}</span>
        <span class="kpi-foot">
          适配器 {{ adapter || '…' }}
        </span>
      </button>
    </div>

    <div class="dash-main">
      <el-card shadow="never" class="chart-card">
        <template #header>
          <div class="block-head">
            <h2 class="section-title">近 30 日完成量</h2>
            <span class="block-meta">按周汇总 · 合计 {{ statsTotal }}</span>
          </div>
        </template>
        <el-empty v-if="!loading && !weekBars.length" description="暂无统计" />
        <div
          v-else
          class="week-chart"
          role="img"
          :aria-label="`近30日按周完成量合计 ${statsTotal}`"
        >
          <div
            v-for="w in weekBars"
            :key="w.key"
            class="week-col"
            :title="`${w.label}：${w.total}`"
          >
            <div class="week-bar-track">
              <div
                class="week-bar"
                :class="{ 'is-empty': w.total <= 0 }"
                :style="{ height: barHeight(w.total) }"
              />
            </div>
            <div class="week-total">{{ w.total }}</div>
            <div class="week-label">{{ w.label }}</div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="list-card">
        <template #header>
          <div class="block-head">
            <h2 class="section-title">最近任务</h2>
            <el-button link type="primary" @click="$router.push({ name: 'tasks' })">查看全部</el-button>
          </div>
        </template>
        <el-empty v-if="!loading && !recent.length" description="暂无任务" />
        <div v-else ref="tableWrap" class="table-scroll table-scroll--fill">
          <el-table
            :data="recent"
            stripe
            class="click-table"
            :height="tableHeight"
            @row-click="onRecentClick"
          >
            <el-table-column label="任务号" min-width="160">
              <template #default="{ row }">
                <router-link
                  class="mono link"
                  :to="{ name: 'task-detail', params: { taskNo: row.taskNo }, query: { from: 'dashboard' } }"
                  @click.stop
                >
                  {{ row.taskNo }}
                </router-link>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small" effect="plain">
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="100">
              <template #default="{ row }">{{ row.progress ?? '-' }}%</template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { balanceApi, healthApi, statisticsApi, type StatDay } from '@/api/meta'
import { listNoticesApi } from '@/api/notice'
import { listTasksApi } from '@/api/task'
import { useTableFillHeight } from '@/composables/useTableFillHeight'
import { statusText, statusType } from '@/utils/taskDisplay'
import type { NoticeItem, TaskItem } from '@/types/api'

interface WeekBar {
  key: string
  label: string
  total: number
}

const router = useRouter()
const loading = ref(false)
const error = ref('')
const adapter = ref('')
const balanceRaw = ref<number | string | null>(null)
const tasks = ref<TaskItem[]>([])
const series = ref<StatDay[]>([])
const notices = ref<NoticeItem[]>([])
const counts = reactive<Record<number, number>>({ [-1]: 0, 0: 0, 1: 0, 2: 0, 3: 0 })
const { tableWrap, tableHeight } = useTableFillHeight(140)

const total = computed(() => tasks.value.length)
const recent = computed(() => tasks.value.slice(0, 6))
const topNotice = computed(() => notices.value[0] || null)
const balanceText = computed(() => {
  if (balanceRaw.value === null || balanceRaw.value === undefined) return '—'
  const n = Number(balanceRaw.value)
  return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(balanceRaw.value)
})
const statsTotal = computed(() => series.value.reduce((s, d) => s + (d.total || 0), 0))

/** 近 30 日压成约 5 根周柱，避免 30 日挤在一起 */
const weekBars = computed((): WeekBar[] => {
  const days = series.value.slice(-30)
  if (!days.length) return []
  const chunks: StatDay[][] = []
  for (let i = 0; i < days.length; i += 7) {
    chunks.push(days.slice(i, i + 7))
  }
  return chunks.map((chunk, idx) => {
    const first = chunk[0]?.date || ''
    const last = chunk[chunk.length - 1]?.date || first
    const total = chunk.reduce((s, d) => s + (d.total || 0), 0)
    return {
      key: `${first}-${idx}`,
      label: `${shortDate(first)}–${shortDate(last)}`,
      total,
    }
  })
})

const maxBar = computed(() => Math.max(1, ...weekBars.value.map((w) => w.total)))

function barHeight(n: number) {
  if (!n) return '4px'
  return `${Math.max(12, Math.round((n / maxBar.value) * 100))}%`
}

function shortDate(date: string) {
  const parts = date.split('-')
  if (parts.length >= 3) return `${Number(parts[1])}/${Number(parts[2])}`
  return date.slice(5) || date
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
  if (t.length <= 80) return t
  return `${t.slice(0, 80)}…`
}

function goNotice(n: NoticeItem) {
  if (n.id == null) return
  router.push({ name: 'notice-detail', params: { noticeId: String(n.id) } })
}

function onRecentClick(row: TaskItem) {
  if (!row.taskNo) return
  router.push({ name: 'task-detail', params: { taskNo: row.taskNo }, query: { from: 'dashboard' } })
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
.dash {
  --dash-gap: 1.25rem;
}

.dash-head {
  margin-bottom: 1.25rem;
}

.page-head-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
}

.page-head-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--dash-gap);
}

.kpi {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 1.25rem 1.35rem;
  min-height: 7.5rem;
  text-align: left;
  color: inherit;
  font: inherit;
  background: var(--app-surface);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: calc(var(--el-border-radius-base) + 2px);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.kpi:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.02);
}

.kpi:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
}

.kpi-label {
  font-size: 0.875rem;
  color: var(--el-text-color-secondary);
}

.kpi-value {
  font-size: 2rem;
  font-weight: 650;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
}

.kpi-value--sm {
  font-size: 1.5rem;
}

.kpi-foot {
  margin-top: auto;
  font-size: 0.75rem;
  color: var(--el-text-color-placeholder);
}

.block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.block-meta {
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.week-chart {
  flex: 1;
  min-height: 11rem;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0.75rem 1.25rem 0.5rem;
}

.week-col {
  flex: 1;
  max-width: 7rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.week-bar-track {
  flex: 1;
  width: 100%;
  min-height: 8rem;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.week-bar {
  width: 48%;
  min-width: 1.75rem;
  max-width: 2.75rem;
  border-radius: 0.4rem 0.4rem 0.15rem 0.15rem;
  background: var(--el-color-primary);
  transition: height 0.2s ease;
}

.week-bar.is-empty {
  background: var(--el-fill-color);
}

.week-total {
  font-size: 0.9375rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--el-text-color-primary);
}

.week-label {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
  text-align: center;
  line-height: 1.3;
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
  margin-bottom: var(--dash-gap);
  flex-shrink: 0;
}

.notice-alert {
  cursor: pointer;
}

.notice-alert:hover {
  opacity: 0.92;
}

@media (max-width: 960px) {
  .kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .week-chart {
    gap: 0.75rem;
    padding-inline: 0.5rem;
  }
}

@media (max-width: 640px) {
  .page-head-row {
    flex-direction: column;
    align-items: stretch;
  }

  .kpi-row {
    grid-template-columns: 1fr;
  }

  .week-chart {
    min-height: 10rem;
    overflow-x: auto;
  }

  .week-col {
    min-width: 4.5rem;
  }
}
</style>
