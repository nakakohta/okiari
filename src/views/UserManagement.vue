<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import SummaryCards from '@/components/SummaryCards.vue'
import UserTable from '@/components/UserTable.vue'
import { roleService, userService } from '@/lib/services'
import type { AppUser, Role } from '@/lib/types'

const users = ref<AppUser[]>([])
const roles = ref<Role[]>([])
const loading = ref(false)
const errorMessage = ref('')
const busyUserId = ref<string | null>(null)

const counts = computed(() => {
  const result = { admin: 0, leader: 0, sub_leader: 0, viewer: 0 }
  for (const user of users.value) {
    const code = user.role?.code
    if (code === 'admin') result.admin += 1
    if (code === 'leader') result.leader += 1
    if (code === 'sub_leader') result.sub_leader += 1
    if (code === 'viewer') result.viewer += 1
  }
  return result
})

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [userData, roleData] = await Promise.all([userService.list(), roleService.list()])
    users.value = userData
    roles.value = roleData
  } catch {
    errorMessage.value = 'ユーザー情報を取得できませんでした'
  } finally {
    loading.value = false
  }
}

async function changeRole(userId: string, roleId: number) {
  busyUserId.value = userId
  errorMessage.value = ''
  try {
    const updated = await userService.updateRole(userId, roleId)
    users.value = users.value.map((user) => (user.id === userId ? updated : user))
  } catch {
    errorMessage.value = '権限を更新できませんでした'
  } finally {
    busyUserId.value = null
  }
}

async function changeStatus(userId: string, isActive: boolean) {
  busyUserId.value = userId
  errorMessage.value = ''
  try {
    const updated = await userService.updateStatus(userId, isActive)
    users.value = users.value.map((user) => (user.id === userId ? updated : user))
  } catch {
    errorMessage.value = '状態を更新できませんでした'
  } finally {
    busyUserId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="layout">
    <Sidebar />

    <main class="content">
      <AppHeader
        title="ユーザー管理"
        description="管理者・リーダー・サブリーダー・閲覧専用ユーザーを管理します。"
        show-button
        button-text="新規ユーザー追加"
        button-path="/user-management/add"
      />

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <SummaryCards
        :admin-count="counts.admin"
        :leader-count="counts.leader"
        :sub-leader-count="counts.sub_leader"
        :viewer-count="counts.viewer"
      />

      <UserTable
        :users="users"
        :roles="roles"
        :busy-user-id="busyUserId"
        @role-change="changeRole"
        @status-change="changeStatus"
      />
    </main>
  </div>
</template>

<style scoped>
.content {
  flex: 1;
  padding: 40px;
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
