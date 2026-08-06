<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import MDTable from '@/components/RestockTable/MDTable.vue'
import { useRealtimeBoard } from '@/composables/useRealtimeBoard'
import { boardService, mastersService } from '@/lib/services'
import { mergeBoardChange } from '@/lib/boardRealtime'
import { useAuthStore } from '@/stores/auth'
import type { MealDrinkBoardData, Store } from '@/lib/types'

const auth = useAuthStore()
const data = ref<MealDrinkBoardData | null>(null)
const stores = ref<Store[]>([])
const loading = ref(false)
const errorMessage = ref('')
const groups = [
  { key: 'first' as const, title: '1階・VIP・その他' },
  { key: 'second' as const, title: '2階' },
  { key: 'third' as const, title: '3階' },
]

async function load(silent = false) {
  if (!silent) loading.value = true
  try {
    const [board, storeData] = await Promise.all([boardService.mealDrink(), mastersService.stores()])
    data.value = board
    stores.value = storeData
    errorMessage.value = ''
  } catch { errorMessage.value = '食数報告（ドリンク）を取得できませんでした。' }
  finally { if (!silent) loading.value = false }
}
function canEditBooth(name: string) {
  if (auth.role === 'admin' || auth.role === 'leader') return true
  const store = stores.value.find((item) => item.name === name)
  return Boolean(store && auth.canEditStore(store.id))
}
const { realtimeState } = useRealtimeBoard('meal-drink', () => load(true), (change) => (
  data.value ? mergeBoardChange(data.value as MealDrinkBoardData & Record<string, unknown>, change) : false
))
onMounted(load)
</script>

<template>
  <div class="layout"><Sidebar /><main class="content">
    <AppHeader title="食数報告（ドリンク）" description="入力内容は自動保存され、同じ表を開いているユーザーへ反映されます。" />
    <div class="connection"><span :class="['realtime',realtimeState]">{{ realtimeState === 'connected' ? '● リアルタイム接続中' : '● 再接続中' }}</span></div>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p><p v-if="loading" class="muted">読み込み中...</p>
    <section v-for="group in groups" :key="group.key" class="table-section">
      <MDTable v-if="data" :title="group.title" :floor-group="group.key" :rows="data.mdtable_rows.filter(row => row.floor_group === group.key)" :columns="data.mdtable_columns.filter(column => column.floor_group === group.key)" :cells="data.mdtable_cells" :locks="data.mdtable_locks.filter(lock => lock.floor_group === group.key)" :can-edit-structure="auth.role === 'admin' || auth.role === 'leader'" :can-select-booth="auth.canEditReports" :can-manage-locks="auth.canManageLocks" :can-delete="auth.canManage" :can-edit-booth="canEditBooth" @refresh="load(true)" @error="errorMessage = $event" />
    </section>
  </main></div>
</template>

<style scoped>
.content{flex:1;min-width:0;padding:40px;background:#f5f7fa}.connection{display:flex;justify-content:flex-end;margin-bottom:12px}.realtime{color:#b45309;font-size:13px;font-weight:700}.realtime.connected{color:#15803d}.table-section{margin-bottom:26px;padding:22px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.error{padding:10px;background:#fee2e2;color:#b91c1c}.muted{color:#64748b}@media(max-width:700px){.content{padding:20px}}
</style>
