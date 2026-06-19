<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter()

defineProps<{
  title: string
  description?: string

  // ボタン関連
  showButton?: boolean
  buttonText?: string
  buttonPath?: string
}>()
</script>

<template>
  <div class="header">
      <div>
        <h1>{{ title }}</h1>
        <p v-if="description">{{ description }}</p>
      </div>
      <div v-if="showButton && buttonPath">
        <button @click="router.push(buttonPath)" class="add-btn">{{ buttonText || '追加' }}</button>
      </div>
    </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 40px;
  margin-bottom: 10px;
}

.header p {
  color: #6b7280;
}

.add-btn {
  background: #ff7a00;
  color: white;
  border: none;
  padding: 14px 30px;
  border-radius: 14px;
  cursor: pointer;
}
</style>
