<script setup lang="ts">
import Sidebar from '../components/AppSidebar.vue'
import AppHeader from '../components/AppHeader.vue';
</script>

<template>
  <div class="layout">
    <Sidebar />

    <main class="content">
      <AppHeader
        title="食数報告"
        description="食数報告確認ページ（デザイン案作成中）"
      />

      </main>
  </div>
</template>

<style scoped>
/* UserManagement.vueと共通のレイアウト用CSS */
.content {
  flex: 1;
  padding: 40px;
}
</style>
