<style>
/* 画面全体の一番シンプルな共通スタイル */
body {
  margin: 0;
  font-family: sans-serif;
  background-color: #f3f4f6;
  color: 333;
}
.app-container {
  min-height: 100vh;
}
</style>

<template>
  <UserManagement />
</template>

<script setup>
import UserManagement from './pages/UserManagement.vue'
</script>
