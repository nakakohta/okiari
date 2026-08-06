<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { roleService } from '@/lib/services'
import type { Role } from '@/lib/types'

const basicRoles = new Set(['admin', 'leader', 'sub_leader', 'viewer'])
const roles = ref<Role[]>([])
const code = ref('')
const name = ref('')
const description = ref('')
const editingId = ref<number | null>(null)
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    roles.value = await roleService.list()
  } catch {
    errorMessage.value = '権限一覧を取得できませんでした'
  } finally {
    loading.value = false
  }
}

function startEdit(role: Role) {
  editingId.value = role.id
  code.value = role.code
  name.value = role.name
  description.value = role.description || ''
}

function resetForm() {
  editingId.value = null
  code.value = ''
  name.value = ''
  description.value = ''
}

async function saveRole() {
  saving.value = true
  errorMessage.value = ''
  try {
    if (editingId.value) {
      const current = roles.value.find((role) => role.id === editingId.value)
      const payload = basicRoles.has(current?.code || '')
        ? { name: name.value, description: description.value || null }
        : { code: code.value, name: name.value, description: description.value || null }
      await roleService.update(editingId.value, payload)
    } else {
      await roleService.create({ code: code.value, name: name.value, description: description.value || null })
    }
    resetForm()
    await load()
  } catch {
    errorMessage.value = '権限を保存できませんでした'
  } finally {
    saving.value = false
  }
}

async function removeRole(role: Role) {
  if (basicRoles.has(role.code)) {
    errorMessage.value = '基本権限は削除できません'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await roleService.remove(role.id)
    await load()
  } catch {
    errorMessage.value = '権限を削除できませんでした'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="layout">
    <Sidebar />

    <main class="content">
      <AppHeader title="権限設定" description="ユーザに割り当てる権限名と説明を管理します。" />

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <section class="panel form-panel">
        <h2>{{ editingId ? '権限を編集' : '権限を追加' }}</h2>
        <form @submit.prevent="saveRole">
          <label>
            コード
            <input v-model="code" type="text" :disabled="Boolean(editingId && basicRoles.has(code))" required />
          </label>
          <label>
            表示名
            <input v-model="name" type="text" required />
          </label>
          <label>
            説明
            <input v-model="description" type="text" />
          </label>
          <div class="actions">
            <button v-if="editingId" type="button" class="secondary" @click="resetForm">キャンセル</button>
            <button type="submit" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
          </div>
        </form>
      </section>

      <section class="panel">
        <h2>権限一覧</h2>
        <table>
          <thead>
            <tr>
              <th>コード</th>
              <th>表示名</th>
              <th>説明</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="role in roles" :key="role.id">
              <td>{{ role.code }}</td>
              <td>{{ role.name }}</td>
              <td>{{ role.description || '-' }}</td>
              <td class="row-actions">
                <button type="button" class="secondary" @click="startEdit(role)">編集</button>
                <button type="button" class="danger" :disabled="basicRoles.has(role.code)" @click="removeRole(role)">
                  削除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  </div>
</template>

<style scoped>
.content {
  flex: 1;
  padding: 40px;
}

.panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.panel h2 {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 800;
}

.form-panel form {
  display: grid;
  grid-template-columns: repeat(3, minmax(160px, 1fr)) auto;
  gap: 14px;
  align-items: end;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 700;
}

input {
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid #eef2f7;
  text-align: left;
}

.actions,
.row-actions {
  display: flex;
  gap: 8px;
}

button {
  border: none;
  background: #ff7a00;
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
  font-weight: 800;
  cursor: pointer;
}

button.secondary {
  background: #e2e8f0;
  color: #334155;
}

button.danger {
  background: #dc2626;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  color: #b91c1c;
  background: #fee2e2;
  padding: 10px 12px;
  border-radius: 8px;
}

.muted {
  color: #64748b;
}
</style>
