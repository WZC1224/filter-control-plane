<template>
  <div class="page-panel page-panel--fill">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">价目</h1>
          <p class="page-sub">下游只读产品价（/product/list 扁平化）</p>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <el-card shadow="never" class="mb filter-card">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="应用">
          <el-select
            v-model="filters.app"
            clearable
            filterable
            placeholder="全部"
            style="width: 10rem"
            @change="writeQuery"
          >
            <el-option v-for="a in appOptions" :key="a" :label="a" :value="a" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input
            v-model="filters.q"
            clearable
            placeholder="类型 / 名称 / 渠道"
            style="width: 14rem"
            @change="writeQuery"
            @clear="writeQuery"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="onResetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert v-if="error" class="mb" type="error" :title="error" show-icon :closable="false">
      <el-button size="small" @click="load">重试</el-button>
    </el-alert>

    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="list-header">
          <span class="section-title">产品价目</span>
          <span v-if="!loading" class="list-meta">显示 {{ filtered.length }} / {{ rows.length }}</span>
        </div>
      </template>
      <div ref="tableWrap" class="table-scroll table-scroll--fill">
      <el-table v-loading="loading" :data="filtered" stripe :height="tableHeight">
        <el-table-column label="应用" width="120" prop="applicationType" />
        <el-table-column label="业务" width="120" prop="businessType" />
        <el-table-column label="类型" width="140">
          <template #default="{ row }">
            <span class="mono">{{ row.taskType }}</span>
          </template>
        </el-table-column>
        <el-table-column label="名称" min-width="140" prop="name" />
        <el-table-column label="单价" width="100" prop="price" />
        <el-table-column label="数量范围" width="140">
          <template #default="{ row }">
            {{ row.minCount ?? '-' }} ~ {{ row.maxCount ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="渠道" width="110" prop="thirdSource" />
        <el-table-column label="说明" min-width="160" show-overflow-tooltip prop="description" />
      </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { productsApi, type ProductItem } from '@/api/meta'
import { useTableFillHeight } from '@/composables/useTableFillHeight'
import { compactQuery, qStr } from '@/utils/querySync'

const route = useRoute()
const router = useRouter()
const rows = ref<ProductItem[]>([])
const loading = ref(false)
const error = ref('')
const { tableWrap, tableHeight } = useTableFillHeight()
const filters = reactive({ app: '', q: '' })

const appOptions = computed(() => {
  const set = new Set<string>()
  for (const r of rows.value) {
    if (r.applicationType) set.add(r.applicationType)
  }
  return [...set].sort()
})

const filtered = computed(() => {
  const q = filters.q.trim().toLowerCase()
  return rows.value.filter((r) => {
    if (filters.app && r.applicationType !== filters.app) return false
    if (!q) return true
    const hay = [r.taskType, r.name, r.thirdSource, r.businessType, r.description]
      .map((x) => String(x || '').toLowerCase())
      .join(' ')
    return hay.includes(q)
  })
})

function readQuery() {
  filters.app = qStr(route.query, 'app')
  filters.q = qStr(route.query, 'q')
}

function writeQuery() {
  router.replace({
    query: compactQuery({
      app: filters.app,
      q: filters.q.trim(),
    }),
  })
}

function onResetFilters() {
  filters.app = ''
  filters.q = ''
  writeQuery()
}

async function load() {
  loading.value = true
  try {
    rows.value = (await productsApi()) || []
    error.value = ''
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载价目失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  readQuery()
  load()
})
</script>
