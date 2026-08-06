<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import MFTable from '@/components/RestockTable/MFTable.vue'
import { useRealtimeBoard } from '@/composables/useRealtimeBoard'
import { boardService, mastersService } from '@/lib/services'
import { mergeBoardChange } from '@/lib/boardRealtime'
import { useAuthStore } from '@/stores/auth'
import type { MealFoodBoardData, MFTableSection, Store } from '@/lib/types'

const auth = useAuthStore()
const data = ref<MealFoodBoardData | null>(null)
const stores = ref<Store[]>([])
const loading = ref(false)
const errorMessage = ref('')
const dragged = ref<number | null>(null)
const sections = computed(() => [...(data.value?.mftable_sections ?? [])].sort((a, b) => a.sort_order - b.sort_order))
const availableStores = computed(() => stores.value.filter((store) => store.is_active && auth.canViewStore(store.id)))

async function load(silent = false) {
  if (!silent) loading.value = true
  try {
    const [board, storeData] = await Promise.all([boardService.mealFood(), mastersService.stores()])
    data.value = board; stores.value = storeData; errorMessage.value = ''
  } catch { errorMessage.value = '食数報告（フード）を取得できませんでした。' }
  finally { if (!silent) loading.value = false }
}

async function addSection() {
  const store = availableStores.value.find((item) => auth.canEditStore(item.id))
  if (!store) { errorMessage.value = '編集できる売店がありません。'; return }
  try { await boardService.create('meal-food', 'mf-sections', { store_id: store.id, store_name: store.name, sort_order: sections.value.length }); await load(true) }
  catch { errorMessage.value = '売店セクションを追加できませんでした。' }
}
async function changeStore(section: MFTableSection, event: Event) {
  const storeId = Number((event.target as HTMLSelectElement).value)
  const store = stores.value.find((item) => item.id === storeId)
  if (!store) return
  try { await boardService.update('meal-food', 'mf-sections', section.id, { store_id: store.id, store_name: store.name }); await load(true) }
  catch { errorMessage.value = '売店名を保存できませんでした。'; await load(true) }
}
async function removeSection(section: MFTableSection) {
  if (!confirm('この売店を削除しますか？')) return
  try { await boardService.remove('meal-food', 'mf-sections', section.id); await load(true) }
  catch { errorMessage.value = '売店を削除できませんでした。' }
}
async function drop(index: number) {
  if (dragged.value === null || dragged.value === index) return
  const ordered = [...sections.value]
  const [moved] = ordered.splice(dragged.value, 1)
  if (!moved) return
  ordered.splice(index, 0, moved); dragged.value = null
  try { await boardService.reorder('meal-food', 'mf-sections', ordered.map((section) => section.id)); await load(true) }
  catch { errorMessage.value = '売店の並び順を保存できませんでした。' }
}
const { realtimeState } = useRealtimeBoard('meal-food', () => load(true), (change) => (
  data.value ? mergeBoardChange(data.value as MealFoodBoardData & Record<string, unknown>, change) : false
))
onMounted(load)
</script>

<template>
  <div class="layout"><Sidebar /><main class="content">
    <AppHeader title="食数報告（フード）" description="品目・容器・割合は自動保存され、同じ表を開いているユーザーへ反映されます。" />
    <div class="connection"><span :class="['realtime',realtimeState]">{{ realtimeState === 'connected' ? '● リアルタイム接続中' : '● 再接続中' }}</span></div>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p><p v-if="loading" class="muted">読み込み中...</p>
    <section v-for="(section,index) in sections" :key="section.id" class="table-section" draggable="true" @dragstart="dragged = index" @dragover.prevent @drop="drop(index)">
      <div class="section-header"><div class="section-left"><span class="grip">⠿</span><select :value="section.store_id ?? ''" :disabled="!section.store_id || !auth.canEditStore(section.store_id)" @change="changeStore(section,$event)"><option v-for="store in availableStores" :key="store.id" :value="store.id">{{ store.name }}</option></select></div><button v-if="auth.canManage" class="delete" @click="removeSection(section)">削除</button></div>
      <MFTable v-if="data" :section-id="section.id" :rows="data.mftable_rows.filter(row => row.section_id === section.id)" :containers="data.mftable_containers" :readonly="!section.store_id || !auth.canEditStore(section.store_id)" :can-delete="auth.canManage" @refresh="load(true)" @error="errorMessage = $event" />
    </section>
    <div class="add"><button :disabled="!auth.canEditReports" @click="addSection">＋売店を追加</button></div>
  </main></div>
</template>

<style scoped>
.content{flex:1;min-width:0;padding:40px;background:#f5f7fa}.connection{display:flex;justify-content:flex-end}.realtime{color:#b45309;font-size:13px;font-weight:700}.realtime.connected{color:#15803d}.table-section{margin:20px 0 30px;padding:24px;border:1px solid #e2e8f0;border-radius:14px;background:white}.section-header,.section-left{display:flex;align-items:center;justify-content:space-between;gap:10px}.section-left select{border:0;background:transparent;font-size:22px;font-weight:800}.grip{font-size:24px;color:#94a3b8;cursor:grab}.delete{border:0;border-radius:7px;background:#fee2e2;color:#b91c1c;padding:8px 12px}.add{display:flex;justify-content:center}.add button{border:0;border-radius:9px;background:#2563eb;color:white;padding:13px 24px;font-weight:700}.error{padding:10px;background:#fee2e2;color:#b91c1c}.muted{color:#64748b}button:disabled,select:disabled{opacity:.55}@media(max-width:700px){.content{padding:20px}}
</style>
