<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">订单</h1>
          <p class="page-sub">消费/订单流水（下游 /order/list）</p>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <el-card shadow="never" class="mb">
      <el-form :inline="true" :model="filters" @submit.prevent="onSearch">
        <el-form-item label="订单号">
          <el-input v-model="filters.orderId" clearable placeholder="orderId" style="width: 12rem" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="filters.taskType"
            clearable
            filterable
            placeholder="全部类型"
            style="width: 12rem"
          >
            <el-option
              v-for="t in taskTypes"
              :key="t.taskType"
              :label="t.description || t.taskType"
              :value="t.taskType"
            />
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
      <div class="table-scroll">
      <el-table
        v-loading="loading"
        :data="orders"
        stripe
        class="click-table"
        max-height="calc(100dvh - 15rem)"
        @row-click="onRowClick"
      >
        <el-table-column label="订单号" min-width="140">
          <template #default="{ row }">
            <div class="id-cell" @click.stop>
              <router-link
                class="mono link"
                :to="{ name: 'task-detail', params: { taskNo: row.orderId } }"
              >
                {{ row.orderId }}
              </router-link>
              <button type="button" class="copy-tiny" title="复制" @click="copyText(row.orderId)">
                复制
              </button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120" prop="taskType" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.consumeStatus)" size="small" effect="plain">
              {{ statusText(row.consumeStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="90">
          <template #default="{ row }">{{ row.taskCount ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="实扣" width="100">
          <template #default="{ row }">{{ row.actualDeduction ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="渠道" width="110">
          <template #default="{ row }">{{ row.thirdSource || '-' }}</template>
        </el-table-column>
        <el-table-column label="时间" min-width="160" prop="createTime" />
        <el-table-column label="说明" min-width="140" show-overflow-tooltip prop="description" />
      </el-table>
      </div>
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
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listOrdersApi } from '@/api/order'
import { orderTaskTypesApi, type OrderTaskTypeItem } from '@/api/meta'
import { statusText, statusType } from '@/utils/taskDisplay'
import { copyText } from '@/utils/clipboard'
import { compactQuery, qInt, qStr } from '@/utils/querySync'
import type { OrderItem } from '@/types/api'

const route = useRoute()
const router = useRouter()
const orders = ref<OrderItem[]>([])
const taskTypes = ref<OrderTaskTypeItem[]>([])
const loading = ref(false)
const error = ref('')
const total = ref(0)
const pageNo = ref(1)
const pageSize = ref(20)
const filters = reactive({ orderId: '', taskType: '' })

function readQuery() {
  const q = route.query
  filters.orderId = qStr(q, 'orderId')
  filters.taskType = qStr(q, 'taskType')
  pageNo.value = qInt(q, 'pageNo', 1)
  pageSize.value = qInt(q, 'pageSize', 20)
}

function writeQuery() {
  router.replace({
    query: compactQuery({
      orderId: filters.orderId,
      taskType: filters.taskType,
      pageNo: pageNo.value === 1 ? undefined : pageNo.value,
      pageSize: pageSize.value === 20 ? undefined : pageSize.value,
    }),
  })
}

async function load() {
  loading.value = true
  try {
    const result = await listOrdersApi({
      pageNo: pageNo.value,
      pageSize: pageSize.value,
      orderId: filters.orderId || undefined,
      taskType: filters.taskType || undefined,
    })
    orders.value = result.data || []
    total.value = result.total ?? orders.value.length
    error.value = ''
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载订单失败'
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
  filters.orderId = ''
  filters.taskType = ''
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

function onRowClick(row: OrderItem) {
  if (!row.orderId) return
  router.push({ name: 'task-detail', params: { taskNo: row.orderId } })
}

onMounted(async () => {
  readQuery()
  try {
    taskTypes.value = (await orderTaskTypesApi()) || []
  } catch {
    taskTypes.value = []
  }
  load()
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

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.link {
  color: var(--el-color-primary);
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.id-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.copy-tiny {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  font-size: 0.75rem;
}

.copy-tiny:hover {
  color: var(--el-color-primary);
}

:deep(.click-table .el-table__row) {
  cursor: pointer;
}

.mb {
  margin-bottom: 1rem;
}
</style>
