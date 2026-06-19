<script setup lang="ts">
import Sidebar from '../components/AppSidebar.vue'
import AppHeader from '@/components/AppHeader.vue';
</script>

<template>
  <div class="layout">
    <Sidebar />

    <main class="content">
      <AppHeader
        title="権限設定"
        description="各役職のアクセス権限を編集できます（デザイン案作成中）"
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
