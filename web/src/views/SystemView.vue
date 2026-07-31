<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">系统</h1>
          <p class="page-sub">健康检查、下游凭证、余额与三方渠道</p>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
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

    <div class="sys-stack">
      <el-card v-loading="loading" shadow="never">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="服务">{{ health?.service || '-' }}</el-descriptions-item>
          <el-descriptions-item label="版本">
            <span class="mono">{{ health?.version || '0.1.0' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="适配器">
            <el-tag size="small" :type="isLiveAdapter ? 'success' : 'info'" effect="plain">
              {{ health?.adapter || '…' }}
            </el-tag>
            <el-tag
              v-if="health?.mock != null"
              size="small"
              class="ml"
              :type="health.mock ? 'warning' : 'success'"
              effect="plain"
            >
              {{ health.mock ? 'Mock' : '真实下游' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="服务时间(UTC)">
            <span class="mono">{{ health?.time || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="下游凭证">
            <el-tag
              size="small"
              effect="plain"
              :type="health?.tokenKind === 'login' ? 'success' : health?.tokenKind === 'agent' ? 'warning' : 'info'"
            >
              {{ health?.tokenKind || '—' }}
            </el-tag>
            <el-tag
              v-if="health?.adapter === 'data818'"
              size="small"
              class="ml"
              effect="plain"
              :type="health?.hasAgentToken ? 'success' : 'warning'"
            >
              agent {{ health?.hasAgentToken ? '已配' : '未配' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下游余额">{{ balanceText }}</el-descriptions-item>
          <el-descriptions-item label="前端">
            <span class="mono">web@{{ webVersion }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="说明">
            下游仅 data818（或 Mock）。凭证可在下方热更新；文件覆盖优先于 `.env`。
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card v-loading="secretsLoading" shadow="never">
        <template #header>
          <div class="block-head">
            <h2 class="section-title">下游凭证</h2>
            <span class="block-meta">
              {{ secrets?.filePath || 'downstream_secrets.json' }} · admin · 保存即热加载
            </span>
          </div>
        </template>
        <div class="secrets-body">
          <el-alert
            class="secrets-hint"
            type="info"
            :closable="false"
            show-icon
            title="粘贴新 Token 后保存。点「清除覆盖」再保存可回退 .env。勿提交 git。"
          />
          <el-form label-width="9rem" class="secrets-form" @submit.prevent="onSaveSecrets">
          <el-form-item label="818 登录 JWT">
            <div class="secret-field">
              <el-input
                v-model="form.data818Token"
                type="password"
                show-password
                clearable
                placeholder="新 Token（改动后才提交）"
                autocomplete="off"
                @input="dirty.data818Token = true"
              />
              <div class="secret-foot">
                <p class="secret-meta">当前：{{ formatSecret(secrets?.data818Token) }}</p>
                <el-button
                  link
                  type="danger"
                  :disabled="secrets?.data818Token?.source !== 'file'"
                  @click="markClear('data818Token')"
                >
                  清除覆盖
                </el-button>
              </div>
            </div>
          </el-form-item>
          <el-form-item label="818 agent">
            <div class="secret-field">
              <el-input
                v-model="form.data818AgentToken"
                type="password"
                show-password
                clearable
                placeholder="新 agent Token"
                autocomplete="off"
                @input="dirty.data818AgentToken = true"
              />
              <div class="secret-foot">
                <p class="secret-meta">当前：{{ formatSecret(secrets?.data818AgentToken) }}</p>
                <el-button
                  link
                  type="danger"
                  :disabled="secrets?.data818AgentToken?.source !== 'file'"
                  @click="markClear('data818AgentToken')"
                >
                  清除覆盖
                </el-button>
              </div>
            </div>
          </el-form-item>
          <el-form-item>
            <div class="secret-actions">
              <el-button type="primary" native-type="submit" :loading="saving">保存并热加载</el-button>
              <el-button @click="resetForm">清空输入</el-button>
            </div>
          </el-form-item>
        </el-form>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <h2 class="section-title">三方渠道余额</h2>
        </template>
        <el-empty
          v-if="!loading && !thirds.length"
          description="暂无数据（下游三方接口失败或无权限时也会显示为空）"
        />
        <div v-else class="table-scroll">
          <el-table :data="thirds" stripe max-height="18rem">
            <el-table-column label="渠道" min-width="160">
              <template #default="{ row }">{{ row.thirdSourceName || '-' }}</template>
            </el-table-column>
            <el-table-column label="余额" min-width="120">
              <template #default="{ row }">{{ row.balance ?? '-' }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  balanceApi,
  downstreamSecretsApi,
  healthApi,
  putDownstreamSecretsApi,
  thirdBalancesApi,
  type DownstreamSecretInfo,
  type DownstreamSecretsResult,
  type ThirdBalanceItem,
} from '@/api/meta'
import type { HealthResult } from '@/types/api'

const webVersion = '0.1.0'
const loading = ref(false)
const secretsLoading = ref(false)
const saving = ref(false)
const error = ref('')
const health = ref<HealthResult | null>(null)
const balanceRaw = ref<number | string | null>(null)
const thirds = ref<ThirdBalanceItem[]>([])
const secrets = ref<DownstreamSecretsResult | null>(null)

type SecretField = 'data818Token' | 'data818AgentToken'

const form = reactive<Record<SecretField, string>>({
  data818Token: '',
  data818AgentToken: '',
})
const dirty = reactive<Record<SecretField, boolean>>({
  data818Token: false,
  data818AgentToken: false,
})

const balanceText = computed(() => {
  if (balanceRaw.value === null || balanceRaw.value === undefined) return '—'
  const n = Number(balanceRaw.value)
  return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(balanceRaw.value)
})

const isLiveAdapter = computed(() => health.value?.adapter === 'data818')

function formatSecret(info?: DownstreamSecretInfo) {
  if (!info?.configured) return '未配置'
  const bits = [info.masked, info.kind, info.source]
  if (info.exp) bits.push(`exp ${info.exp}`)
  return bits.filter(Boolean).join(' · ')
}

function resetForm() {
  ;(Object.keys(form) as SecretField[]).forEach((k) => {
    form[k] = ''
    dirty[k] = false
  })
}

function markClear(field: SecretField) {
  form[field] = ''
  dirty[field] = true
  ElMessage.info('已标记清除，点保存后回退 .env')
}

async function loadSecrets() {
  secretsLoading.value = true
  try {
    secrets.value = await downstreamSecretsApi()
  } catch {
    secrets.value = null
    // http 拦截器已提示
  } finally {
    secretsLoading.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [h, bal, tb] = await Promise.all([
      healthApi(),
      balanceApi().catch(() => null),
      thirdBalancesApi().catch(() => []),
    ])
    health.value = h
    balanceRaw.value = bal?.balance ?? null
    thirds.value = tb || []
    await loadSecrets()
  } catch (e) {
    error.value = (e as { message?: string })?.message || '健康检查失败'
    health.value = null
  } finally {
    loading.value = false
  }
}

async function onSaveSecrets() {
  const body: Partial<Record<SecretField, string>> = {}
  ;(Object.keys(dirty) as SecretField[]).forEach((k) => {
    if (dirty[k]) body[k] = form[k]
  })
  if (!Object.keys(body).length) {
    ElMessage.info('没有改动')
    return
  }
  saving.value = true
  try {
    secrets.value = await putDownstreamSecretsApi(body)
    resetForm()
    ElMessage.success('已保存并热加载')
    await load()
  } catch {
    // http 拦截器已提示
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.ml {
  margin-left: 0.5rem;
}

.sys-stack {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding-bottom: 0.5rem;
}

.sys-stack > .mb {
  margin-bottom: 0;
}

.block-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem 1rem;
}

.block-meta {
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
}

.secrets-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.secrets-hint {
  margin: 0;
}

.secrets-form {
  max-width: 40rem;
  margin: 0;
}

.secrets-form :deep(.el-form-item) {
  margin-bottom: 1rem;
  align-items: flex-start;
}

.secrets-form :deep(.el-form-item__label) {
  height: auto;
  line-height: 32px;
  padding-top: 0;
}

.secrets-form :deep(.el-form-item__content) {
  line-height: 1.4;
  display: block;
}

.secrets-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.secret-field {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.secret-foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.secret-meta {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 0.75rem;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
  word-break: break-all;
}

.secret-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
