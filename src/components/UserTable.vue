<script setup lang="ts">
import type { AppUser, Role } from '@/lib/types'

defineProps<{
  users: AppUser[]
  roles: Role[]
  busyUserId?: string | null
}>()

defineEmits<{
  roleChange: [userId: string, roleId: number]
  statusChange: [userId: string, isActive: boolean]
}>()

function roleClass(code?: string) {
  return {
    admin: code === 'admin',
    leader: code === 'leader',
    sub: code === 'sub_leader',
    viewer: code === 'viewer',
  }
}
</script>

<template>
  <div class="table-card">
    <h2>ユーザー一覧</h2>
    <table>
      <thead>
        <tr>
          <th>名前</th>
          <th>メール</th>
          <th>権限</th>
          <th>状態</th>
          <th>更新日時</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.display_name || '-' }}</td>
          <td>{{ user.email }}</td>
          <td>
            <select
              :value="user.role_id"
              :disabled="busyUserId === user.id"
              :class="roleClass(user.role?.code)"
              @change="$emit('roleChange', user.id, Number(($event.target as HTMLSelectElement).value))"
            >
              <option v-for="role in roles" :key="role.id" :value="role.id">
                {{ role.name }}
              </option>
            </select>
          </td>
          <td>
            <button
              type="button"
              class="status"
              :class="user.is_active ? 'active-status' : 'inactive-status'"
              :disabled="busyUserId === user.id"
              @click="$emit('statusChange', user.id, !user.is_active)"
            >
              {{ user.is_active ? '有効' : '停止' }}
            </button>
          </td>
          <td>{{ user.updated_at ? new Date(user.updated_at).toLocaleString() : '-' }}</td>
        </tr>
        <tr v-if="users.length === 0">
          <td colspan="5" class="empty">ユーザーが登録されていません</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-card {
  background: white;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.table-card h2 {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 800;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 14px;
  text-align: left;
  border-bottom: 1px solid #eef2f7;
}

thead {
  background: #f8fafc;
}

select {
  min-width: 140px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
  font-weight: 700;
}

.admin {
  color: #dc2626;
}
.leader {
  color: #2563eb;
}
.sub {
  color: #16a34a;
}
.viewer {
  color: #64748b;
}

.status {
  border: none;
  padding: 7px 14px;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 700;
}

.active-status {
  background: #dcfce7;
  color: #15803d;
}

.inactive-status {
  background: #fee2e2;
  color: #b91c1c;
}

.empty {
  color: #64748b;
  text-align: center;
}
</style>
