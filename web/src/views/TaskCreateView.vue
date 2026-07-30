<template>
  <div class="page-panel">
    <header class="page-head">
      <h1 class="page-title">新建任务</h1>
      <p class="page-sub">上传号码文件并提交到下游筛选</p>
    </header>

    <el-card v-loading="loadingMeta" shadow="never" class="form-card">
      <el-form
        :model="createForm"
        label-width="88px"
        label-position="right"
        @submit.prevent="onCreate"
      >
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="筛选类型" required>
              <el-select v-model="createForm.filterType" placeholder="选择类型" class="w-full" filterable>
                <el-option
                  v-for="item in filterTypes"
                  :key="item.filter_type"
                  :label="item.description || item.filter_type"
                  :value="item.filter_type"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="国家" required>
              <el-select
                v-model="createForm.countryCode"
                filterable
                placeholder="选择国家"
                class="w-full"
              >
                <el-option
                  v-for="item in countries"
                  :key="countryCode(item)"
                  :label="`${countryCode(item)} · ${countryName(item)}`"
                  :value="countryCode(item)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="说明">
              <el-input v-model="createForm.describe" placeholder="可选备注" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="号码文件" required>
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :limit="1"
                accept=".txt,text/plain"
                :on-change="onFileChange"
                :on-remove="onFileRemove"
              >
                <el-button>选择 .txt</el-button>
                <template #tip>
                  <div class="el-upload__tip">仅 txt，一行一号</div>
                </template>
              </el-upload>
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          v-if="priceHint"
          class="mb"
          type="info"
          :closable="false"
          show-icon
          :title="priceHint"
        />
        <el-alert
          v-else-if="createForm.filterType && !loadingMeta"
          class="mb"
          type="warning"
          :closable="false"
          show-icon
          title="当前类型在价目中未找到单价（仍可提交；以下游扣费为准）"
        />

        <el-form-item>
          <el-button type="primary" :loading="creating" native-type="submit" @click="onCreate">
            提交任务
          </el-button>
          <el-button @click="$router.push({ name: 'tasks' })">返回列表</el-button>
          <el-button link type="primary" @click="$router.push({ name: 'products' })">查看价目</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadFile, type UploadInstance } from 'element-plus'
import { filterTypesApi, countriesApi, productsApi, type ProductItem } from '@/api/meta'
import { createTaskApi } from '@/api/task'
import { countryCode, countryName } from '@/utils/taskDisplay'
import type { CountryItem, FilterTypeItem } from '@/types/api'

const router = useRouter()
const filterTypes = ref<FilterTypeItem[]>([])
const countries = ref<CountryItem[]>([])
const products = ref<ProductItem[]>([])
const loadingMeta = ref(false)
const creating = ref(false)
const uploadRef = ref<UploadInstance>()
const fileRaw = ref<File | null>(null)
const lineCount = ref<number | null>(null)

const createForm = reactive({
  filterType: '',
  countryCode: '',
  describe: '',
})

const selectedProduct = computed(() => {
  const t = createForm.filterType
  if (!t) return null
  return products.value.find((p) => p.taskType === t) || null
})

const selectedFilterMeta = computed(() => {
  const t = createForm.filterType
  if (!t) return null
  return filterTypes.value.find((f) => f.filter_type === t) || null
})

const priceHint = computed(() => {
  const p = selectedProduct.value
  const meta = selectedFilterMeta.value
  if (!p && !meta) return ''
  const parts: string[] = []
  if (p?.price != null && p.price !== '') {
    parts.push(`单价 ${p.price}`)
  }
  const minC = p?.minCount ?? meta?.min_count
  const maxC = p?.maxCount ?? meta?.max_count
  if (minC != null || maxC != null) {
    parts.push(`数量 ${minC ?? '-'} ~ ${maxC ?? '-'}`)
  }
  if (p?.thirdSource) parts.push(`渠道 ${p.thirdSource}`)
  if (lineCount.value != null) {
    parts.push(`文件约 ${lineCount.value} 行`)
    const priceNum = Number(p?.price)
    if (Number.isFinite(priceNum) && lineCount.value > 0) {
      const est = priceNum * lineCount.value
      parts.push(`粗估扣费 ≈ ${est.toFixed(4)}（以下游为准）`)
    }
  }
  return parts.join(' · ')
})

async function countLines(file: File): Promise<number> {
  const text = await file.text()
  return text.split(/\r?\n/).filter((l) => l.trim()).length
}

async function onFileChange(file: UploadFile) {
  fileRaw.value = (file.raw as File) || null
  lineCount.value = null
  if (fileRaw.value) {
    try {
      lineCount.value = await countLines(fileRaw.value)
    } catch {
      lineCount.value = null
    }
  }
}

function onFileRemove() {
  fileRaw.value = null
  lineCount.value = null
}

async function loadMeta() {
  loadingMeta.value = true
  try {
    const [types, list, prod] = await Promise.all([
      filterTypesApi(),
      countriesApi(),
      productsApi().catch(() => [] as ProductItem[]),
    ])
    filterTypes.value = types || []
    countries.value = list || []
    products.value = prod || []
    if (!createForm.filterType && filterTypes.value.length) {
      createForm.filterType = filterTypes.value[0].filter_type
    }
    if (!createForm.countryCode && countries.value.length) {
      createForm.countryCode = countryCode(countries.value[0])
    }
  } catch (e) {
    ElMessage.error((e as { message?: string })?.message || '加载元数据失败')
  } finally {
    loadingMeta.value = false
  }
}

async function onCreate() {
  if (!createForm.filterType || !createForm.countryCode) {
    ElMessage.warning('请选择筛选类型和国家')
    return
  }
  if (!fileRaw.value) {
    ElMessage.warning('请选择 txt 文件')
    return
  }
  const minC = selectedProduct.value?.minCount ?? selectedFilterMeta.value?.min_count
  const maxC = selectedProduct.value?.maxCount ?? selectedFilterMeta.value?.max_count
  if (lineCount.value != null) {
    if (minC != null && lineCount.value < Number(minC)) {
      ElMessage.warning(`号码行数 ${lineCount.value} 低于最小 ${minC}`)
      return
    }
    if (maxC != null && lineCount.value > Number(maxC)) {
      ElMessage.warning(`号码行数 ${lineCount.value} 超过最大 ${maxC}`)
      return
    }
  }
  const fd = new FormData()
  fd.append('filterType', createForm.filterType)
  fd.append('countryCode', createForm.countryCode)
  fd.append('describe', createForm.describe)
  fd.append('file', fileRaw.value)
  creating.value = true
  try {
    const result = await createTaskApi(fd)
    const no = (result.taskNo as string) || ''
    ElMessage.success(`已提交：${no || 'ok'}`)
    fileRaw.value = null
    lineCount.value = null
    uploadRef.value?.clearFiles()
    if (no) {
      await router.push({ name: 'task-detail', params: { taskNo: no } })
    } else {
      await router.push({ name: 'tasks' })
    }
  } catch {
    // 拦截器已提示；保留表单与文件便于改完重试
  } finally {
    creating.value = false
  }
}

onMounted(loadMeta)
</script>

<style scoped lang="scss">
.w-full {
  width: 100%;
}
</style>
