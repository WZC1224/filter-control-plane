<template>
  <div class="page-panel page-panel--fill">
    <header class="page-head page-head-row">
      <div>
        <h1 class="page-title">用户管理</h1>
        <p class="page-sub">控制平面账号 · admin / operator（不映射下游）</p>
      </div>
      <div class="page-head-actions">
        <el-button type="primary" @click="openCreate">新建用户</el-button>
      </div>
    </header>

    <el-card shadow="never" class="list-card">
      <div ref="tableWrap" class="table-scroll">
        <el-table v-loading="loading" :data="rows" :height="tableHeight" stripe>
          <el-table-column prop="id" label="ID" width="72" />
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column label="角色" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="row.role === 'admin' ? 'danger' : 'info'" effect="plain">
                {{ row.role }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.isActive ? 'success' : 'info'" effect="plain">
                {{ row.isActive ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" min-width="160" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button
                link
                :type="row.isActive ? 'warning' : 'success'"
                @click="toggleActive(row)"
              >
                {{ row.isActive ? '停用' : '启用' }}
              </el-button>
              <el-button link @click="openReset(row)">重置密码</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-dialog v-model="createVisible" title="新建用户" width="28rem" destroy-on-close>
      <el-form label-width="88px" @submit.prevent="onCreate">
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" autocomplete="off" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option label="operator" value="operator" />
            <el-option label="admin" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" native-type="submit">创建</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑用户" width="28rem" destroy-on-close>
      <el-form label-width="88px" @submit.prevent="onEdit">
        <el-form-item label="用户名">
          <el-input :model-value="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option label="operator" value="operator" />
            <el-option label="admin" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" native-type="submit">保存</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置密码" width="28rem" destroy-on-close>
      <el-form label-width="88px" @submit.prevent="onReset">
        <el-form-item label="用户名">
          <el-input :model-value="resetForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input v-model="resetForm.password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" native-type="submit">重置</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createUserApi, listUsersApi, patchUserApi } from '@/api/users'
import { useTableFillHeight } from '@/composables/useTableFillHeight'
import type { UserItem, UserRole } from '@/types/api'

const loading = ref(false)
const saving = ref(false)
const rows = ref<UserItem[]>([])
const { tableWrap, tableHeight } = useTableFillHeight()

const createVisible = ref(false)
const editVisible = ref(false)
const resetVisible = ref(false)

const createForm = reactive({ username: '', password: '', role: 'operator' as UserRole })
const editForm = reactive({ id: 0, username: '', role: 'operator' as UserRole })
const resetForm = reactive({ id: 0, username: '', password: '' })

async function load() {
  loading.value = true
  try {
    rows.value = await listUsersApi()
  } catch {
    // 已提示
  } finally {
    loading.value = false
  }
}

function openCreate() {
  createForm.username = ''
  createForm.password = ''
  createForm.role = 'operator'
  createVisible.value = true
}

function openEdit(row: UserItem) {
  editForm.id = row.id
  editForm.username = row.username
  editForm.role = row.role
  editVisible.value = true
}

function openReset(row: UserItem) {
  resetForm.id = row.id
  resetForm.username = row.username
  resetForm.password = ''
  resetVisible.value = true
}

async function onCreate() {
  if (!createForm.username || createForm.password.length < 6) {
    ElMessage.warning('用户名必填，密码至少 6 位')
    return
  }
  saving.value = true
  try {
    await createUserApi({ ...createForm })
    ElMessage.success('已创建')
    createVisible.value = false
    await load()
  } catch {
    //
  } finally {
    saving.value = false
  }
}

async function onEdit() {
  saving.value = true
  try {
    await patchUserApi(editForm.id, { role: editForm.role })
    ElMessage.success('已保存')
    editVisible.value = false
    await load()
  } catch {
    //
  } finally {
    saving.value = false
  }
}

async function onReset() {
  if (resetForm.password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  saving.value = true
  try {
    await patchUserApi(resetForm.id, { password: resetForm.password })
    ElMessage.success('密码已重置')
    resetVisible.value = false
  } catch {
    //
  } finally {
    saving.value = false
  }
}

async function toggleActive(row: UserItem) {
  const next = !row.isActive
  try {
    await ElMessageBox.confirm(
      next ? `启用用户 ${row.username}？` : `停用用户 ${row.username}？停用后无法登录。`,
      '确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await patchUserApi(row.id, { isActive: next })
    ElMessage.success(next ? '已启用' : '已停用')
    await load()
  } catch {
    //
  }
}

onMounted(load)
</script>
