<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps<{
  title: string
  description?: string
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
    <button v-if="showButton && buttonPath" class="add-btn" type="button" @click="router.push(buttonPath)">
      {{ buttonText || '追加' }}
    </button>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 28px;
}

.header h1 {
  font-size: 36px;
  font-weight: 800;
  line-height: 1.2;
  margin: 0 0 8px;
  color: #172033;
}

.header p {
  color: #6b7280;
  margin: 0;
}

.add-btn {
  background: #ff7a00;
  color: white;
  border: none;
  padding: 12px 22px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 700;
  white-space: nowrap;
}
</style>
