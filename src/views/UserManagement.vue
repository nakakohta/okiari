<script setup lang="ts">
import { ref } from 'vue'
import type { User } from '@/components/UserTable.vue'
// import { useRouter } from 'vue-router'
import Sidebar from '@/components/AppSidebar.vue'
import SummaryCards from '@/components/SummaryCards.vue'
import UserTable from '@/components/UserTable.vue'
import AppHeader from '@/components/AppHeader.vue'

// const router = useRouter()

// テーブルに表示するためのデータ(FastAPIやSupabaseから取得予定)
const userList = ref<User[]>([
  { name: 'リーダー', role: 'leader', roleLabel:'リーダー', dept: 'フード売店', status:'有効' },
  { name: 'サブリーダー', role: 'subLeader', roleLabel:'サブリーダー', dept: 'ドリンク補充', status:'有効' },
  { name: '管理者', role: 'admin', roleLabel:'管理者', dept: '全体管理', status:'有効' },
  { name: '閲覧専用', role: 'viewer', roleLabel:'閲覧専用', dept: '集計確認', status:'有効' }

])
</script>

<template>
  <div class="layout">
    <Sidebar />

    <main class="content">
      <AppHeader
        title="ユーザ管理"
        description="管理者・リーダー・サブリーダー・閲覧専用ユーザの権限を確認できます"
        show-button
        button-text="新規ユーザ追加"
        button-path="/user-management/add"
      />

      <SummaryCards
        :admin-count="10"
        :leader-count="40"
        :sub-leader-count="10"
        :viewer-count="10"
      />

      <UserTable :users="userList" />

    </main>
  </div>
</template>

<style scoped>
/* 残ったレイアウト全体のCSS */
.content {
  flex: 1;
  padding: 40px;
}
</style>
