<script setup lang="ts">
// import { useAuthStore } from '@/stores/auth'
import Sidebar from '@/components/AppSidebar.vue'
import AppHeader from '@/components/AppHeader.vue';

// const auth = useAuthStore()
</script>

<template>
  <div class="layout">
    <Sidebar />

    <main class="content">
      <AppHeader
        title="ダッシュボード"
        description="今日の業務を選択してください"
      />
    </main>
  </div>
</template>

<style scoped>
.content {
  flex: 1;
  padding: 40px;
}
</style>
