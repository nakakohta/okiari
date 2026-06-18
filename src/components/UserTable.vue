<script setup lang="ts">
// 1ユーザの型定義
interface User {
  name: string
  role: 'admin' | 'leader' | 'subLeader' | 'viewer'
  roleLabel: string
  dept: string
  status: string
}

// ユーザの配列を親から受け取る設定
defineProps<{
  users: User[]
}>()
</script>

<template>
  <div class="table-card">
    <h2>ユーザー一覧</h2>
    <table>
      <thead>
        <tr>
          <th>名前</th>
          <th>権限</th>
          <th>担当</th>
          <th>状態</th>
          <th>最終更新</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(user, index) in users" :key="index">
          <td>{{ user.name }}</td>
          <td :class="{
            'admin': user.role ==='admin',
            'leader': user.role ==='leader',
            'sub': user.role === 'subLeader',
            'gray-text': user.role === 'viewer'
          }">
          {{ user.roleLabel }}
        </td>
        <td>{{ user.dept }}</td>
        <td>
          <span class="status" :class="user.status === '有効' ? 'active-status' : 'inactive-status'">
            {{ user.status }}
          </span>
        </td>
        <td>18:05</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
/* UserManagement.vueからテーブルに関するCSSだけを引っ越し */
.table-card {
  background: white;
  margin-top: 40px;
  padding: 30px;
  border-radius: 24px;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  padding: 18px;
  text-align: left;
  border-bottom: 1px solid #eee;
}
thead { background: #f1f5f9; }
.admin { color: red; font-weight: bold; }
.leader { color: #2563ff; font-weight: bold; }
.sub { color: #16a34a; font-weight: bold; }
.gray-text { color: #6b7280; font-weight: bold; }
.status { padding: 6px 14px; border-radius: 20px; font-size: 13px; }
.active-status { background: #dcfce7; color: #16a34a; }
.inactive-status { background: #fee2e2; color: #ef4444; }
</style>
