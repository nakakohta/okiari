<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import { roleService, userService } from '@/lib/services'
import type { Role } from '@/lib/types'

const router = useRouter()
const roles = ref<Role[]>([])
const displayName = ref('')
const email = ref('')
const password = ref('')
const roleId = ref<number | ''>('')
const isActive = ref(true)
const saving = ref(false)
const errorMessage = ref('')

async function loadRoles() {
  try {
    roles.value = await roleService.list()
    roleId.value = roles.value.find((role) => role.code === 'viewer')?.id || roles.value[0]?.id || ''
  } catch {
    errorMessage.value = '権限一覧を取得できませんでした'
  }
}

async function handleAddUser() {
  if (roleId.value === '') {
    errorMessage.value = '権限を選択してください'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await userService.create({
      display_name: displayName.value,
      email: email.value,
      password: password.value,
      role_id: Number(roleId.value),
      is_active: isActive.value,
    })
    router.push('/user-management')
  } catch {
    errorMessage.value = 'ユーザを登録できませんでした'
  } finally {
    saving.value = false
  }
}

onMounted(loadRoles)
</script>

<template>
  <div class="layout add-layout">
    <main class="main-container">
      <AppHeader title="ユーザ追加" description="Supabase Authユーザとアプリユーザを同時に作成します。" />

      <form class="form-container" @submit.prevent="handleAddUser">
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <label>
          名前
          <input v-model="displayName" type="text" placeholder="名前" required />
        </label>

        <label>
          メールアドレス
          <input v-model="email" type="email" placeholder="example@example.com" required />
        </label>

        <label>
          初期パスワード
          <input v-model="password" type="password" minlength="8" placeholder="8文字以上" required />
        </label>

        <label>
          権限
          <select v-model.number="roleId" required>
            <option value="" disabled>選択してください</option>
            <option v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</option>
          </select>
        </label>

        <label class="checkbox">
          <input v-model="isActive" type="checkbox" />
          有効ユーザとして登録する
        </label>

        <div class="actions">
          <button type="button" class="secondary" @click="router.push('/user-management')">戻る</button>
          <button type="submit" :disabled="saving">{{ saving ? '登録中...' : '登録する' }}</button>
        </div>
      </form>
    </main>
  </div>
</template>

<style scoped>
.add-layout {
  justify-content: center;
}

.main-container {
  width: min(720px, 100%);
  padding: 40px 24px;
}

.form-container {
  background: white;
  padding: 28px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 700;
  color: #334155;
}

input,
select {
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 15px;
}

.checkbox {
  flex-direction: row;
  align-items: center;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

button {
  border: none;
  background: #ff7a00;
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 800;
  cursor: pointer;
}

button.secondary {
  background: #e2e8f0;
  color: #334155;
}

.error {
  color: #b91c1c;
  background: #fee2e2;
  padding: 10px 12px;
  border-radius: 8px;
}
</style>
