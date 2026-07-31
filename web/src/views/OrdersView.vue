<template>
  <div class="page-panel page-panel--fill">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">订单</h1>
          <p class="page-sub">管理端订单范围（下游 /admin/third_management/task_list）</p>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <el-card shadow="never" class="mb filter-card">
      <el-form :inline="true" :model="filters" @submit.prevent="onSearch">
        <el-form-item label="订单号">
          <el-input v-model="filters.orderId" clearable placeholder="orderId" style="width: 12rem" />
        </el-form-item>
        <el-form-item label="用户">
          <el-input v-model="filters.username" clearable placeholder="username" style="width: 10rem" />
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
        <el-form-item label="说明">
          <el-input v-model="filters.description" clearable placeholder="模糊" style="width: 10rem" />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="开始"
            end-placeholder="结束"
            style="width: 16rem"
          />
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

    <el-card shadow="never" class="list-card">
      <div ref="tableWrap" class="table-scroll table-scroll--fill">
      <el-table
        v-loading="loading"
        :data="orders"
        stripe
        class="click-table"
        :height="tableHeight"
        @row-click="onRowClick"
      >
        <el-table-column label="订单号" min-width="140">
          <template #default="{ row }">
            <div class="id-cell" @click.stop>
              <router-link
                class="mono link"
                :to="{ name: 'task-detail', params: { taskNo: taskLinkNo(row) }, query: { from: 'orders' } }"
              >
                {{ row.orderId }}
              </router-link>
              <button type="button" class="copy-tiny" title="复制" @click="copyText(row.orderId)">
                复制
              </button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="用户" width="100" prop="userName" show-overflow-tooltip />
        <el-table-column label="类型" width="120" prop="taskType" show-overflow-tooltip />
        <el-table-column label="消费" width="72">
          <template #default="{ row }">{{ consumeTypeText(row.consumeType) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.consumeStatus)" size="small" effect="plain">
              {{ statusText(row.consumeStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="90">
          <template #default="{ row }">{{ intText(row.taskCount) }}</template>
        </el-table-column>
        <el-table-column label="实扣" width="100">
          <template #default="{ row }">{{ intText(row.actualDeduction) }}</template>
        </el-table-column>
        <el-table-column label="余额" width="100">
          <template #default="{ row }">{{ intText(row.currentBalance) }}</template>
        </el-table-column>
        <el-table-column label="渠道" width="100">
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
import { useTableFillHeight } from '@/composables/useTableFillHeight'
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
const dateRange = ref<[string, string] | null>(null)
const { tableWrap, tableHeight } = useTableFillHeight()
const filters = reactive({
  orderId: '',
  username: '',
  taskType: '',
  description: '',
})

function consumeTypeText(v: number | undefined | null) {
  if (v === -1) return '支出'
  if (v === 1) return '收益'
  return '-'
}

function readQuery() {
  const q = route.query
  filters.orderId = qStr(q, 'orderId')
  filters.username = qStr(q, 'username')
  filters.taskType = qStr(q, 'taskType')
  filters.description = qStr(q, 'description')
  const begin = qStr(q, 'createTimeBegin')
  const end = qStr(q, 'createTimeEnd')
  dateRange.value = begin && end ? [begin, end] : null
  pageNo.value = qInt(q, 'pageNo', 1)
  pageSize.value = qInt(q, 'pageSize', 20)
}

function writeQuery() {
  router.replace({
    query: compactQuery({
      orderId: filters.orderId,
      username: filters.username,
      taskType: filters.taskType,
      description: filters.description,
      createTimeBegin: dateRange.value?.[0],
      createTimeEnd: dateRange.value?.[1],
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
      username: filters.username || undefined,
      taskType: filters.taskType || undefined,
      description: filters.description || undefined,
      createTimeBegin: dateRange.value?.[0],
      createTimeEnd: dateRange.value?.[1],
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
  filters.username = ''
  filters.taskType = ''
  filters.description = ''
  dateRange.value = null
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

/** 详情/下载 id = orderId（818 filter/business 均按 order_id）。 */
function taskLinkNo(row: OrderItem): string {
  return (row.orderId || row.taskNo || row.partitionId || '').trim()
}

/** 表格数字去小数（10178.000000 → 10178）。 */
function intText(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '-'
  const n = Number(value)
  if (!Number.isFinite(n)) return String(value)
  return String(Math.trunc(n))
}

function onRowClick(row: OrderItem) {
  const no = taskLinkNo(row)
  if (!no) return
  router.push({ name: 'task-detail', params: { taskNo: no }, query: { from: 'orders' } })
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
</style>
