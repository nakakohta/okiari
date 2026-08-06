<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import MTable from '@/components/RestockTable/MTable.vue'
import { useRealtimeBoard } from '@/composables/useRealtimeBoard'
import { boardService, mastersService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { InventoryBoardData, Product, Store } from '@/lib/types'

const auth = useAuthStore()
const data = ref<InventoryBoardData | null>(null)
const stores = ref<Store[]>([])
const products = ref<Product[]>([])
const loading = ref(false)
const errorMessage = ref('')
async function load(silent = false) {
  if (!silent) loading.value = true
  try {
    const [board, storeData, productData] = await Promise.all([boardService.inventory(), mastersService.stores(), mastersService.products('inventory')])
    data.value = board; stores.value = storeData; products.value = productData; errorMessage.value = ''
  } catch { errorMessage.value = '棚卸表を取得できませんでした。' }
  finally { if (!silent) loading.value = false }
}
const { realtimeState } = useRealtimeBoard('inventory', () => load(true))
onMounted(load)
</script>

<template>
  <div class="layout"><Sidebar /><main class="content">
    <AppHeader title="棚卸" description="予定数と実数の差分を確認し、確定すると既存在庫へ反映します。" />
    <div class="connection"><span :class="['realtime',realtimeState]">{{ realtimeState === 'connected' ? '● リアルタイム接続中' : '● 再接続中' }}</span></div>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p><p v-if="loading" class="muted">読み込み中...</p>
    <section class="panel"><MTable v-if="data" :rows="data.mtable_rows" :stores="stores" :products="products" :can-edit-store="auth.canEditStore" :can-confirm="auth.role === 'admin' || auth.role === 'leader'" :can-delete="auth.canManage" @refresh="load(true)" @error="errorMessage = $event" /></section>
  </main></div>
</template>

<style scoped>
.content{flex:1;min-width:0;padding:40px;background:#f5f7fa}.connection{display:flex;justify-content:flex-end;margin-bottom:12px}.realtime{color:#b45309;font-size:13px;font-weight:700}.realtime.connected{color:#15803d}.panel{padding:24px;border:1px solid #e2e8f0;border-radius:14px;background:white}.error{padding:10px;background:#fee2e2;color:#b91c1c}.muted{color:#64748b}@media(max-width:700px){.content{padding:20px}}
</style>
