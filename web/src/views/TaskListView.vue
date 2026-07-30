<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">任务列表</h1>
          <p class="page-sub">筛选、分页、详情与多格式下载</p>
        </div>
        <div class="page-head-actions">
          <el-button :loading="loading" @click="load">刷新</el-button>
          <el-button type="primary" @click="$router.push({ name: 'task-create' })">新建任务</el-button>
        </div>
      </div>
    </header>

    <el-card shadow="never" class="mb">
      <el-form :inline="true" :model="filters" @submit.prevent="onSearch">
        <el-form-item label="任务号">
          <el-input v-model="filters.taskNo" clearable placeholder="模糊/精确" style="width: 10rem" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.taskType" clearable filterable placeholder="全部" style="width: 10rem">
            <el-option
              v-for="item in filterTypes"
              :key="item.filter_type"
              :label="item.description || item.filter_type"
              :value="item.filter_type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="国家">
          <el-select v-model="filters.countryCode" clearable filterable placeholder="全部" style="width: 10rem">
            <el-option
              v-for="item in countries"
              :key="countryCode(item)"
              :label="`${countryCode(item)} · ${countryName(item)}`"
              :value="countryCode(item)"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.taskStatus" clearable placeholder="全部" style="width: 8rem">
            <el-option label="排队" :value="0" />
            <el-option label="进行中" :value="2" />
            <el-option label="完成" :value="1" />
            <el-option label="失败" :value="-1" />
            <el-option label="关闭" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

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

    <el-card shadow="never">
      <template #header>
        <div class="list-header">
          <span class="section-title">全部任务</span>
          <span v-if="!loading" class="list-meta">共 {{ total }} 条</span>
        </div>
      </template>

      <el-skeleton v-if="loading && !tasks.length" :rows="5" animated />
      <el-empty
        v-else-if="!loading && !tasks.length && !error"
        description="暂无任务。去「新建任务」上传 txt。"
      >
        <el-button type="primary" @click="$router.push({ name: 'task-create' })">新建任务</el-button>
      </el-empty>
      <template v-else>
        <el-table
          v-loading="loading"
          :data="tasks"
          stripe
          class="task-table"
          aria-label="筛选任务表"
          @row-click="onRowClick"
        >
          <el-table-column label="任务号" min-width="140">
            <template #default="{ row }">
              <button
                type="button"
                class="mono copy-btn"
                title="点击复制"
                @click.stop="copyText(taskNo(row))"
              >
                {{ taskNo(row) }}
              </button>
            </template>
          </el-table-column>
          <el-table-column label="名称" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.taskName || '-' }}</template>
          </el-table-column>
          <el-table-column label="类型" width="120">
            <template #default="{ row }">
              <span class="mono">{{ row.taskType || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="国家" width="90">
            <template #default="{ row }">{{ row.country || '-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small" effect="plain">
                {{ statusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="进度" width="90">
            <template #default="{ row }">{{ row.progress ?? '-' }}%</template>
          </el-table-column>
          <el-table-column label="有效量" width="90">
            <template #default="{ row }">{{ row.effectiveQuantity ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <div class="ops-cell" @click.stop>
                <el-button
                  link
                  type="primary"
                  @click="$router.push({ name: 'task-detail', params: { taskNo: taskNo(row) } })"
                >
                  详情
                </el-button>
                <el-dropdown
                  :disabled="row.status !== 1"
                  trigger="click"
                  @command="(fmt: DownloadFormat) => onDownload(row, fmt)"
                >
                  <el-button
                    link
                    type="primary"
                    :disabled="row.status !== 1"
                    :loading="downloadingNo === taskNo(row)"
                  >
                    下载
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-for="f in DOWNLOAD_FORMATS" :key="f.value" :command="f.value">
                        {{ f.label }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-dropdown trigger="click" @command="(cmd: string) => onOps(row, cmd)">
                  <el-button link type="primary">运维</el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="close" :disabled="row.status !== 0">关闭</el-dropdown-item>
                      <el-dropdown-item
                        command="refund"
                        :disabled="row.status !== 1 && row.status !== 3"
                      >
                        退款
                      </el-dropdown-item>
                      <el-dropdown-item
                        command="retry"
                        :disabled="row.status !== -1 && row.status !== 3 && row.status !== 1"
                      >
                        重试
                      </el-dropdown-item>
                      <el-dropdown-item command="export-remaining" :disabled="row.status !== 1">
                        导出剩余号
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <div class="pager">
          <el-pagination
            v-model:current-page="pageNo"
            v-model:page-size="pageSize"
            background
            layout="total, sizes, prev, pager, next"
            :total="total"
            :page-sizes="[10, 20, 50]"
          @current-change="onPageChange"
          @size-change="onSizeChange"
          />
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { filterTypesApi, countriesApi } from '@/api/meta'
import {
  listTasksApi,
  downloadTaskApi,
  closeTaskApi,
  refundTaskApi,
  retryTaskApi,
  exportRemainingApi,
} from '@/api/task'
import { promptObjectPath } from '@/utils/objectPath'
import { copyText } from '@/utils/clipboard'
import { compactQuery, qInt, qStatus, qStr } from '@/utils/querySync'
import {
  DOWNLOAD_FORMATS,
  countryCode,
  countryName,
  statusText,
  statusType,
  taskNo,
  type DownloadFormat,
} from '@/utils/taskDisplay'
import type { CountryItem, FilterTypeItem, TaskItem } from '@/types/api'

const route = useRoute()
const router = useRouter()
const tasks = ref<TaskItem[]>([])
const filterTypes = ref<FilterTypeItem[]>([])
const countries = ref<CountryItem[]>([])
const loading = ref(false)
const error = ref('')
const downloadingNo = ref('')
const total = ref(0)
const pageNo = ref(1)
const pageSize = ref(20)
let pollTimer: ReturnType<typeof setInterval> | undefined

const filters = reactive<{
  taskNo: string
  taskType: string
  countryCode: string
  taskStatus: number | undefined
}>({
  taskNo: '',
  taskType: '',
  countryCode: '',
  taskStatus: undefined,
})

function readQuery() {
  const q = route.query
  filters.taskNo = qStr(q, 'taskNo')
  filters.taskType = qStr(q, 'taskType')
  filters.countryCode = qStr(q, 'countryCode')
  filters.taskStatus = qStatus(q, 'taskStatus')
  pageNo.value = qInt(q, 'pageNo', 1)
  pageSize.value = qInt(q, 'pageSize', 20)
}

function writeQuery() {
  router.replace({
    query: compactQuery({
      taskNo: filters.taskNo,
      taskType: filters.taskType,
      countryCode: filters.countryCode,
      taskStatus: filters.taskStatus,
      pageNo: pageNo.value === 1 ? undefined : pageNo.value,
      pageSize: pageSize.value === 20 ? undefined : pageSize.value,
    }),
  })
}

async function loadMeta() {
  try {
    const [types, list] = await Promise.all([filterTypesApi(), countriesApi()])
    filterTypes.value = types || []
    countries.value = list || []
  } catch {
    filterTypes.value = []
    countries.value = []
  }
}

async function load() {
  loading.value = true
  try {
    const result = await listTasksApi({
      pageNo: pageNo.value,
      pageSize: pageSize.value,
      taskNo: filters.taskNo || undefined,
      taskType: filters.taskType || undefined,
      countryCode: filters.countryCode || undefined,
      taskStatus: filters.taskStatus,
    })
    tasks.value = result.data || []
    total.value = result.total ?? tasks.value.length
    error.value = ''
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载任务失败'
  } finally {
    loading.value = false
  }
}

function onSearch() {
  pageNo.value = 1
  writeQuery()
  load()
}

function onReset() {
  filters.taskNo = ''
  filters.taskType = ''
  filters.countryCode = ''
  filters.taskStatus = undefined
  pageNo.value = 1
  pageSize.value = 20
  writeQuery()
  load()
}

function onSizeChange() {
  pageNo.value = 1
  writeQuery()
  load()
}

function onPageChange() {
  writeQuery()
  load()
}

function onRowClick(row: TaskItem) {
  const no = taskNo(row)
  if (no === '-') return
  router.push({ name: 'task-detail', params: { taskNo: no } })
}

async function onDownload(row: TaskItem, fmt: DownloadFormat) {
  const no = taskNo(row)
  if (no === '-' || row.status !== 1) return
  downloadingNo.value = no
  try {
    await downloadTaskApi(no, fmt)
    ElMessage.success('已开始下载')
  } catch {
    // 已提示
  } finally {
    downloadingNo.value = ''
  }
}

async function onOps(row: TaskItem, cmd: string) {
  const no = taskNo(row)
  if (no === '-') return
  if (cmd === 'export-remaining') {
    if (row.status !== 1) return
    downloadingNo.value = no
    try {
      const r = await exportRemainingApi(no)
      if (r?.objectPath) {
        await promptObjectPath(r.objectPath)
      } else {
        ElMessage.success('剩余号已下载')
      }
    } catch {
      // 已提示
    } finally {
      downloadingNo.value = ''
    }
    return
  }
  const labels: Record<string, string> = { close: '关闭', refund: '退款', retry: '重试' }
  await ElMessageBox.confirm(`确认对 ${no} 执行「${labels[cmd] || cmd}」？`, '运维确认', {
    type: 'warning',
  })
  try {
    if (cmd === 'close') await closeTaskApi(no)
    else if (cmd === 'refund') await refundTaskApi(no)
    else if (cmd === 'retry') await retryTaskApi(no)
    ElMessage.success('已执行')
    await load()
  } catch {
    // 已提示
  }
}

onMounted(async () => {
  readQuery()
  await loadMeta()
  await load()
  pollTimer = setInterval(() => {
    if (tasks.value.some((t) => t.status === 0 || t.status === 2)) load()
  }, 15000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped lang="scss">
.page-head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.page-head-actions {
  display: flex;
  gap: 0.5rem;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.list-meta {
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.mb {
  margin-bottom: 1rem;
}

.copy-btn {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--el-color-primary);
  cursor: pointer;
  font: inherit;
}

.copy-btn:hover {
  text-decoration: underline;
}

.ops-cell {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.15rem;
}

:deep(.task-table .el-table__row) {
  cursor: pointer;
}
</style>
