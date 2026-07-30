<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">公告详情</h1>
          <p class="page-sub">#{{ noticeId }}</p>
        </div>
        <div class="page-head-actions">
          <el-button @click="$router.push({ name: 'notices' })">返回列表</el-button>
          <el-button :loading="loading" @click="load">刷新</el-button>
        </div>
      </div>
    </header>

    <el-alert v-if="error" class="mb" type="error" :title="error" show-icon :closable="false">
      <el-button size="small" @click="load">重试</el-button>
    </el-alert>

    <el-card v-loading="loading" shadow="never" class="form-card">
      <template v-if="notice">
        <div class="notice-head">
          <h2 class="notice-title">{{ notice.title }}</h2>
          <el-tag size="small" effect="plain" :type="levelType(notice.level)">
            {{ notice.level || 'INFO' }}
          </el-tag>
        </div>
        <p class="notice-meta">
          <span>{{ notice.bizType || '-' }}</span>
          <span>{{ notice.publishStatus || '-' }}</span>
          <span>{{ notice.createDate || '-' }}</span>
          <span v-if="notice.expireDate">到期 {{ notice.expireDate }}</span>
        </p>
        <pre class="notice-body">{{ notice.contentMd || '' }}</pre>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getNoticeApi } from '@/api/notice'
import type { NoticeItem } from '@/types/api'

const route = useRoute()
const notice = ref<NoticeItem | null>(null)
const loading = ref(false)
const error = ref('')

const noticeId = computed(() => String(route.params.noticeId || ''))

function levelType(level?: string): 'info' | 'warning' | 'danger' | 'success' {
  const v = (level || '').toUpperCase()
  if (v.includes('WARN')) return 'warning'
  if (v.includes('ERR') || v.includes('CRIT')) return 'danger'
  if (v.includes('SUCC')) return 'success'
  return 'info'
}

async function load() {
  if (!noticeId.value) return
  loading.value = true
  try {
    notice.value = await getNoticeApi(noticeId.value)
    error.value = ''
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载详情失败'
    notice.value = null
  } finally {
    loading.value = false
  }
}

watch(noticeId, load)
onMounted(load)
</script>

<style scoped lang="scss">
.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.25rem;
}

.notice-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  line-height: 1.4;
}

.notice-meta {
  margin: 0.75rem 0 1.25rem;
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
}

.notice-body {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 0.9375rem;
  line-height: 1.65;
  color: var(--el-text-color-regular);
}
</style>
