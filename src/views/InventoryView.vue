<script setup lang="ts">
import Sidebar from '../components/AppSidebar.vue'
</script>

<template>
  <div class="layout">
    <Sidebar />

    <main class="content">
      <div class="header">
        <div>
          <h1>棚卸</h1>
          <p>棚卸確認ページ（デザイン案作成中）</p>
        </div>
      </div>

      </main>
  </div>
</template>

<style scoped>
/* UserManagement.vueと共通のレイアウト用CSS */
.content {
  flex: 1;
  padding: 40px;
}
.header h1 {
  font-size: 40px;
  margin-bottom: 10px;
}
.header p {
  color: #6b7280;
}
</style>
