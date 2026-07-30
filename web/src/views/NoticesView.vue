<template>
  <div class="page-panel">
    <header class="page-head">
      <div class="page-head-row">
        <div>
          <h1 class="page-title">公告</h1>
          <p class="page-sub">已发布系统消息（下游 /sys_msg/list）</p>
        </div>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </header>

    <el-alert v-if="error" class="mb" type="error" :title="error" show-icon :closable="false">
      <el-button size="small" @click="load">重试</el-button>
    </el-alert>

    <el-empty v-if="!loading && !notices.length" description="暂无公告" />
    <div v-else class="notice-list" v-loading="loading">
      <el-card
        v-for="n in notices"
        :key="String(n.id)"
        shadow="never"
        class="mb notice-card"
        @click="$router.push({ name: 'notice-detail', params: { noticeId: String(n.id) } })"
      >
        <div class="notice-head">
          <h2 class="notice-title">{{ n.title }}</h2>
          <el-tag size="small" effect="plain" :type="levelType(n.level)">{{ n.level || 'INFO' }}</el-tag>
        </div>
        <p class="notice-meta">
          <span>{{ n.bizType || '-' }}</span>
          <span>{{ n.createDate || '-' }}</span>
          <span class="link-hint">查看详情</span>
        </p>
        <pre class="notice-body">{{ preview(n.contentMd) }}</pre>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listNoticesApi } from '@/api/notice'
import type { NoticeItem } from '@/types/api'

const notices = ref<NoticeItem[]>([])
const loading = ref(false)
const error = ref('')

function levelType(level?: string): 'info' | 'warning' | 'danger' | 'success' {
  const v = (level || '').toUpperCase()
  if (v.includes('WARN')) return 'warning'
  if (v.includes('ERR') || v.includes('CRIT')) return 'danger'
  if (v.includes('SUCC')) return 'success'
  return 'info'
}

function preview(md?: string) {
  const t = (md || '').trim()
  if (t.length <= 160) return t
  return `${t.slice(0, 160)}…`
}

async function load() {
  loading.value = true
  try {
    notices.value = (await listNoticesApi()) || []
    error.value = ''
  } catch (e) {
    error.value = (e as { message?: string })?.message || '加载公告失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped lang="scss">
.notice-card {
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.notice-card:hover {
  border-color: var(--el-color-primary-light-5);
}

.notice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.notice-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.notice-meta {
  margin: 0.5rem 0 1rem;
  display: flex;
  gap: 1.25rem;
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
}

.link-hint {
  color: var(--el-color-primary);
  margin-left: auto;
}

.notice-body {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--el-text-color-regular);
}
</style>
