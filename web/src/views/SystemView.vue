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

    <el-card v-loading="loading" shadow="never" class="mb">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="服务">{{ health?.service || '-' }}</el-descriptions-item>
        <el-descriptions-item label="版本">
          <span class="mono">{{ health?.version || '0.1.0' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="适配器">
          <el-tag
            size="small"
            :type="health?.adapter === 'data818' ? 'success' : 'info'"
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
        <el-descriptions-item label="下游余额">{{ balanceText }}</el-descriptions-item>
        <el-descriptions-item label="前端">
          <span class="mono">web@{{ webVersion }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="说明">
          三方余额需 admin ACL。关单/退款/重试同理。充值/商品仍不在本台。
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <h2 class="section-title">三方渠道余额</h2>
      </template>
      <el-empty v-if="!loading && !thirds.length" description="无数据或无权限" />
      <el-table v-else :data="thirds" stripe>
        <el-table-column label="渠道" min-width="160">
          <template #default="{ row }">{{ row.thirdSourceName || '-' }}</template>
        </el-table-column>
        <el-table-column label="余额" min-width="120">
          <template #default="{ row }">{{ row.balance ?? '-' }}</template>
        </el-table-column>
      </el-table>
    </el-card>
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
.page-head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.ml {
  margin-left: 0.5rem;
}

.mb {
  margin-bottom: 1rem;
}
</style>
