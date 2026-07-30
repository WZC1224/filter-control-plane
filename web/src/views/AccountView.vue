<template>
  <div class="page-panel">
    <header class="page-head">
      <h1 class="page-title">账号</h1>
      <p class="page-sub">控制平面独立账号（不映射下游用户）</p>
    </header>

    <div class="form-stack">
    <el-card shadow="never" class="form-card">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ user.username || '-' }}</el-descriptions-item>
        <el-descriptions-item label="登录态">
          <el-tag size="small" :type="user.token ? 'success' : 'info'" effect="plain">
            {{ user.token ? '已登录' : '未登录' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <div class="actions">
        <el-button type="primary" @click="onLogout">退出登录</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="form-card">
      <template #header>
        <h2 class="section-title">修改密码</h2>
      </template>
      <el-form label-width="96px" style="max-width: 28rem" @submit.prevent="onChangePassword">
        <el-form-item label="原密码" required>
          <el-input v-model="pwd.oldPassword" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="pwd.newPassword" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="确认新密码" required>
          <el-input v-model="pwd.confirm" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" native-type="submit">保存</el-button>
        </el-form-item>
      </el-form>
      <p class="hint">多用户 RBAC / 与 data818 账号打通仍不做；仅本机控制台密码。</p>
    </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePasswordApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const router = useRouter()
const saving = ref(false)
const pwd = reactive({
  oldPassword: '',
  newPassword: '',
  confirm: '',
})

function onLogout() {
  user.logout()
  router.replace({ name: 'login' })
}

async function onChangePassword() {
  if (!pwd.oldPassword || !pwd.newPassword) {
    ElMessage.warning('请填写原密码与新密码')
    return
  }
  if (pwd.newPassword.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (pwd.newPassword !== pwd.confirm) {
    ElMessage.warning('两次新密码不一致')
    return
  }
  saving.value = true
  try {
    await changePasswordApi(pwd.oldPassword, pwd.newPassword)
    ElMessage.success('密码已更新，请重新登录')
    user.logout()
    await router.replace({ name: 'login' })
  } catch {
    // 已提示
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.actions {
  margin-top: 1.25rem;
}

.hint {
  margin: 0.75rem 0 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}
</style>
