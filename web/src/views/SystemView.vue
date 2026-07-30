<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">系统</h1>
          <p class="page-sub">健康检查、适配器、余额与三方渠道</p>
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
          <el-tag
            size="small"
            :type="isLiveAdapter ? 'success' : 'info'"
            effect="plain"
          >
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
          <el-tag
            v-if="health?.adapter === 'data_center'"
            size="small"
            class="ml"
            effect="plain"
            :type="health?.hasApiKey ? 'success' : 'warning'"
          >
            API Key {{ health?.hasApiKey ? '已配' : '未配' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="下游余额">{{ balanceText }}</el-descriptions-item>
        <el-descriptions-item label="前端">
          <span class="mono">web@{{ webVersion }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="说明">
          独占下游（DOWNSTREAM）。data818 需登录 JWT + agent；data_center 需 JWT + X-Api-Key。三方余额与关单需 admin ACL。
        </el-descriptions-item>
      </el-descriptions>
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
import { computed, onMounted, ref } from 'vue'
import { balanceApi, healthApi, thirdBalancesApi, type ThirdBalanceItem } from '@/api/meta'
import type { HealthResult } from '@/types/api'

/** 与 web/package.json version 对齐 */
const webVersion = '0.1.0'
const loading = ref(false)
const error = ref('')
const health = ref<HealthResult | null>(null)
const balanceRaw = ref<number | string | null>(null)
const thirds = ref<ThirdBalanceItem[]>([])

const balanceText = computed(() => {
  if (balanceRaw.value === null || balanceRaw.value === undefined) return '—'
  const n = Number(balanceRaw.value)
  return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(balanceRaw.value)
})

const isLiveAdapter = computed(
  () => health.value?.adapter === 'data818' || health.value?.adapter === 'data_center',
)
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
  } catch (e) {
    error.value = (e as { message?: string })?.message || '健康检查失败'
    health.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.ml {
  margin-left: 0.5rem;
}

.hint {
  margin-left: 0.5rem;
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
}

.sys-stack {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.sys-stack > .mb {
  margin-bottom: 0;
}
</style>
