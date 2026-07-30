<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">账单</h1>
          <p class="page-sub">账本流水（下游 /admin/bill/list）</p>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <el-card shadow="never" class="mb">
      <el-form :inline="true" :model="filters" @submit.prevent="onSearch">
        <el-form-item label="账单号">
          <el-input v-model="filters.billId" clearable style="width: 11rem" />
        </el-form-item>
        <el-form-item label="订单号">
          <el-input v-model="filters.orderId" clearable style="width: 11rem" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select
            v-model="filters.ledgerType"
            clearable
            filterable
            placeholder="全部类型"
            style="width: 12rem"
          >
            <el-option
              v-for="t in ledgerTypes"
              :key="t.ledgerType"
              :label="`${t.description || t.ledgerType}`"
              :value="t.ledgerType"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert v-if="error" class="mb" type="error" :title="error" show-icon :closable="false">
      <el-button size="small" @click="load">重试</el-button>
    </el-alert>

    <el-card shadow="never">
      <div class="table-scroll">
      <el-table
        v-loading="loading"
        :data="bills"
        stripe
        class="click-table"
        max-height="calc(100dvh - 15rem)"
        @row-click="onRowClick"
      >
        <el-table-column label="账单号" min-width="140">
          <template #default="{ row }">
            <button
              type="button"
              class="mono copy-btn"
              title="点击复制"
              @click.stop="copyText(row.billId)"
            >
              {{ row.billId }}
            </button>
          </template>
        </el-table-column>
        <el-table-column label="业务单" min-width="130">
          <template #default="{ row }">
            <router-link
              v-if="row.bizId"
              class="mono link"
              :to="{ name: 'task-detail', params: { taskNo: row.bizId } }"
              @click.stop
            >
              {{ row.bizId }}
            </router-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="账本类型" width="130" prop="ledgerType" />
        <el-table-column label="方向" width="80" prop="consumeType" />
        <el-table-column label="金额" width="100">
          <template #default="{ row }">{{ row.amount ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="变动后" width="100">
          <template #default="{ row }">{{ row.balanceAfter ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="业务类型" width="110" prop="bizType" />
        <el-table-column label="时间" min-width="160" prop="createDate" />
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
import { listBillsApi } from '@/api/notice'
import { ledgerTypesApi, type LedgerTypeItem } from '@/api/meta'
import { copyText } from '@/utils/clipboard'
import { compactQuery, qInt, qStr } from '@/utils/querySync'
import type { BillItem } from '@/types/api'

const route = useRoute()
const router = useRouter()
const bills = ref<BillItem[]>([])
const ledgerTypes = ref<LedgerTypeItem[]>([])
const loading = ref(false)
const error = ref('')
const total = ref(0)
const pageNo = ref(1)
const pageSize = ref(20)
const filters = reactive({ billId: '', orderId: '', ledgerType: '' })

function readQuery() {
  const q = route.query
  filters.billId = qStr(q, 'billId')
  filters.orderId = qStr(q, 'orderId')
  filters.ledgerType = qStr(q, 'ledgerType')
  pageNo.value = qInt(q, 'pageNo', 1)
  pageSize.value = qInt(q, 'pageSize', 20)
}

function writeQuery() {
  router.replace({
    query: compactQuery({
      billId: filters.billId,
      orderId: filters.orderId,
      ledgerType: filters.ledgerType,
      pageNo: pageNo.value === 1 ? undefined : pageNo.value,
      pageSize: pageSize.value === 20 ? undefined : pageSize.value,
    }),
  })
}

async function load() {
  loading.value = true
  try {
    const result = await listBillsApi({
      pageNo: pageNo.value,
      pageSize: pageSize.value,
      billId: filters.billId || undefined,
      orderId: filters.orderId || undefined,
      ledgerType: filters.ledgerType || undefined,
    })
    bills.value = result.data || []
    total.value = result.total ?? bills.value.length
    error.value = ''
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载账单失败'
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
  filters.billId = ''
  filters.orderId = ''
  filters.ledgerType = ''
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

function onRowClick(row: BillItem) {
  if (!row.bizId) return
  router.push({ name: 'task-detail', params: { taskNo: row.bizId } })
}

onMounted(async () => {
  readQuery()
  try {
    ledgerTypes.value = (await ledgerTypesApi()) || []
  } catch {
    ledgerTypes.value = []
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

:deep(.click-table .el-table__row) {
  cursor: pointer;
}

.mb {
  margin-bottom: 1rem;
}
</style>
