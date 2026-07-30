<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">任务详情</h1>
          <p class="page-sub mono">{{ taskNoParam }}</p>
        </div>
        <div class="page-head-actions">
          <el-button @click="$router.push({ name: 'tasks' })">返回列表</el-button>
          <el-button :loading="loading" @click="load">刷新</el-button>
          <el-dropdown :disabled="!canDownload" trigger="click" @command="onDownload">
            <el-button type="primary" :disabled="!canDownload" :loading="downloading">
              下载结果
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="f in DOWNLOAD_FORMATS" :key="f.value" :command="f.value">
                  {{ f.label }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button
            :disabled="!canDownload"
            :loading="exporting"
            @click="onExportRemaining"
          >
            导出剩余号
          </el-button>
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

    <div class="detail-stack">
    <el-card v-loading="loading" shadow="never">
      <template v-if="summary">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务号">
            <button
              type="button"
              class="mono copy-btn"
              title="点击复制"
              @click="copyText(String(summary.taskNo || taskNoParam))"
            >
              {{ summary.taskNo || taskNoParam }}
            </button>
          </el-descriptions-item>
          <el-descriptions-item label="名称">{{ summary.taskName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <span class="mono">{{ summary.taskType || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="国家">{{ summary.country || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(summary.status)" size="small" effect="plain">
              {{ statusText(summary.status) }}
            </el-tag>
            <span v-if="polling" class="poll-hint">自动刷新中</span>
          </el-descriptions-item>
          <el-descriptions-item label="进度">
            <el-progress
              v-if="summary.progress != null"
              :percentage="Number(summary.progress) || 0"
              :status="summary.status === 1 ? 'success' : undefined"
              style="max-width: 14rem"
            />
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="有效量">
            {{ summary.effectiveQuantity ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ summary.createDate || '-' }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <h2 class="section-title">运维操作</h2>
      </template>
      <p class="ops-hint">对齐 data818：关单（排队未上传）、退款（完成/关闭）、重试（超管）。真实下游需 TOKEN 具备 admin/super 权限。</p>
      <div class="ops-row">
        <el-button :disabled="summary?.status !== 0" :loading="opsLoading === 'close'" @click="onClose">
          关闭任务
        </el-button>
        <el-button
          type="warning"
          :disabled="summary?.status !== 1 && summary?.status !== 3"
          :loading="opsLoading === 'refund'"
          @click="onRefund"
        >
          退款
        </el-button>
        <el-button
          type="danger"
          plain
          :disabled="summary?.status !== -1 && summary?.status !== 3 && summary?.status !== 1"
          :loading="opsLoading === 'retry'"
          @click="onRetry"
        >
          重试查询
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <h2 class="raw-title">原始响应</h2>
      <pre class="detail-pre" tabindex="0">{{ detailText }}</pre>
    </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  queryTaskApi,
  downloadTaskApi,
  closeTaskApi,
  refundTaskApi,
  retryTaskApi,
  exportRemainingApi,
} from '@/api/task'
import { promptObjectPath } from '@/utils/objectPath'
import { copyText } from '@/utils/clipboard'
import {
  DOWNLOAD_FORMATS,
  isActiveStatus,
  statusText,
  statusType,
  type DownloadFormat,
} from '@/utils/taskDisplay'
import type { TaskItem } from '@/types/api'

const route = useRoute()
const loading = ref(false)
const downloading = ref(false)
const exporting = ref(false)
const opsLoading = ref('')
const error = ref('')
const detailText = ref('')
const summary = ref<Partial<TaskItem> | null>(null)
const polling = ref(false)
let pollTimer: ReturnType<typeof setInterval> | undefined

const taskNoParam = computed(() => String(route.params.taskNo || ''))
const canDownload = computed(() => summary.value?.status === 1)

function stopPoll() {
  polling.value = false
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = undefined
  }
}

function startPoll() {
  stopPoll()
  if (!isActiveStatus(summary.value?.status)) return
  polling.value = true
  pollTimer = setInterval(load, 5000)
}

async function load() {
  if (!taskNoParam.value) return
  loading.value = true
  error.value = ''
  try {
    const detail = await queryTaskApi(taskNoParam.value)
    detailText.value = JSON.stringify(detail, null, 2)
    summary.value = detail as Partial<TaskItem>
    if (isActiveStatus(summary.value.status)) {
      if (!pollTimer) startPoll()
    } else {
      stopPoll()
    }
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载详情失败'
    summary.value = null
    detailText.value = ''
    stopPoll()
  } finally {
    loading.value = false
  }
}

async function onDownload(fmt: DownloadFormat) {
  if (!canDownload.value) return
  downloading.value = true
  try {
    await downloadTaskApi(taskNoParam.value, fmt)
    ElMessage.success('已开始下载')
  } catch {
    // 已提示
  } finally {
    downloading.value = false
  }
}

async function onExportRemaining() {
  if (!canDownload.value) return
  exporting.value = true
  try {
    const r = await exportRemainingApi(taskNoParam.value)
    if (r?.objectPath) {
      await promptObjectPath(r.objectPath)
    } else {
      ElMessage.success('剩余号已下载')
    }
  } catch {
    // 已提示
  } finally {
    exporting.value = false
  }
}

async function onClose() {
  await ElMessageBox.confirm('关闭排队任务并退回扣费（Mock/有权限下游）？', '关闭任务', {
    type: 'warning',
  })
  opsLoading.value = 'close'
  try {
    await closeTaskApi(taskNoParam.value)
    ElMessage.success('已关闭')
    await load()
  } catch {
    // 已提示
  } finally {
    opsLoading.value = ''
  }
}

async function onRefund() {
  await ElMessageBox.confirm('对当前任务发起退款？', '退款', { type: 'warning' })
  opsLoading.value = 'refund'
  try {
    await refundTaskApi(taskNoParam.value)
    ElMessage.success('已退款')
    await load()
  } catch {
    // 已提示
  } finally {
    opsLoading.value = ''
  }
}

async function onRetry() {
  await ElMessageBox.confirm('将任务置为进行中以触发下游重查？', '重试', { type: 'warning' })
  opsLoading.value = 'retry'
  try {
    await retryTaskApi(taskNoParam.value)
    ElMessage.success('已重试')
    await load()
  } catch {
    // 已提示
  } finally {
    opsLoading.value = ''
  }
}

watch(taskNoParam, () => {
  stopPoll()
  load()
})

onMounted(load)
onUnmounted(stopPoll)
</script>

<style scoped lang="scss">
.poll-hint {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
}

.ops-hint {
  margin: 0 0 1rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.ops-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.raw-title {
  margin: 0 0 0.75rem;
  font-size: 0.9375rem;
  font-weight: 600;
}

.detail-pre {
  margin: 0;
  max-height: 26rem;
  overflow: auto;
  padding: 1rem 1.1rem;
  font-size: 0.75rem;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-all;
  background: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-base);
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
</style>
