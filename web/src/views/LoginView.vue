<template>
  <div class="login-wrap">
    <el-button
      text
      class="theme-fab"
      :aria-label="theme.isDark ? '切换白天模式' : '切换黑夜模式'"
      @click="theme.toggle()"
    >
      <el-icon :size="18"><Moon v-if="!theme.isDark" /><Sunny v-else /></el-icon>
    </el-button>
    <main class="login-main">
      <el-card class="login-card" shadow="never" role="region" aria-labelledby="login-title">
        <template #header>
          <h1 id="login-title" class="login-title">筛选控制台</h1>
          <p class="login-sub">内部运营 · 账号由管理员开通</p>
        </template>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="onSubmit"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              id="login-username"
              v-model="form.username"
              name="username"
              autocomplete="username"
              clearable
            />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              id="login-password"
              v-model="form.password"
              name="password"
              type="password"
              show-password
              autocomplete="current-password"
              @keyup.enter="onSubmit"
            />
          </el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            class="login-btn"
            @click="onSubmit"
          >
            登录
          </el-button>
        </el-form>
      </el-card>
    </main>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const theme = useThemeStore()
const router = useRouter()
const route = useRoute()
const loading = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  const ok = await formRef.value?.validate().catch(() => false)
  if (!ok) return
  loading.value = true
  try {
    await user.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    await router.replace(redirect)
  } catch {
    // http 拦截器已提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-wrap {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%, var(--app-bg-accent) 0%, transparent 55%),
    linear-gradient(165deg, var(--app-login-top) 0%, var(--app-login-mid) 45%, var(--app-login-bottom) 100%);
}

.theme-fab {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
}

.login-main {
  width: 100%;
  max-width: 26rem;
}

.login-card {
  border: 1px solid var(--el-border-color-lighter);
}

.login-card :deep(.el-card__header) {
  padding: 1.5rem 1.5rem 0.85rem;
}

.login-card :deep(.el-card__body) {
  padding: 0.85rem 1.5rem 1.5rem;
}

.login-title {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 600;
  line-height: 1.4;
  color: var(--el-text-color-primary);
}

.login-sub {
  margin: 0.4rem 0 0;
  font-size: 0.8125rem;
  color: var(--el-text-color-secondary);
}

.login-btn {
  width: 100%;
  margin-top: 0.75rem;
}
</style>
