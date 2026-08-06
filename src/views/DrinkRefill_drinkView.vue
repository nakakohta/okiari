<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import DTable from '@/components/RestockTable/DTable.vue'
import { useRealtimeBoard } from '@/composables/useRealtimeBoard'
import { boardService, mastersService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { DrinkBoardData, Store } from '@/lib/types'

const auth = useAuthStore()
const stores = ref<Store[]>([])
const data = ref<DrinkBoardData | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const activeStores = computed(() => stores.value.filter((store) => store.is_active && auth.canViewStore(store.id)))

async function load(silent = false) {
  if (!silent) loading.value = true
  try {
    const [storeData, board] = await Promise.all([mastersService.stores(), boardService.drink()])
    stores.value = storeData
    data.value = board
    errorMessage.value = ''
  } catch { errorMessage.value = 'ドリンク補充表を取得できませんでした。' }
  finally { if (!silent) loading.value = false }
}
function rows(storeId: number, scope: 'drink' | 'consumable') { return data.value?.dtable_rows.filter((row) => row.store_id === storeId && row.scope === scope) ?? [] }
function locks(storeId: number, scope: 'drink' | 'consumable') { return data.value?.dtable_locks.filter((lock) => lock.store_id === storeId && lock.scope === scope) ?? [] }
const { realtimeState } = useRealtimeBoard('drink-refill', () => load(true))
onMounted(load)
</script>

<template>
  <div class="layout"><Sidebar /><main class="content">
    <AppHeader title="ドリンク補充" description="入力内容は自動保存され、同じ表を開いているユーザーへ反映されます。" />
    <div class="store-menu"><div class="menu-head"><h2>売店一覧</h2><span :class="['realtime',realtimeState]">{{ realtimeState === 'connected' ? '● リアルタイム接続中' : '● 再接続中' }}</span></div><nav><a v-for="store in activeStores" :key="store.id" :href="`#store-${store.id}`">{{ store.name }}</a></nav></div>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p><p v-if="loading" class="muted">読み込み中...</p>
    <section v-for="store in activeStores" :id="`store-${store.id}`" :key="store.id" class="store-section">
      <h2>{{ store.name }}</h2>
      <DTable title="ドリンク補充" :store-id="store.id" scope="drink" :rows="rows(store.id,'drink')" :locks="locks(store.id,'drink')" :readonly="!auth.canEditStore(store.id)" :can-manage-locks="auth.canManageLocks" :can-delete="auth.canManage" @refresh="load(true)" @error="errorMessage = $event" />
      <DTable title="消耗品補充" :store-id="store.id" scope="consumable" :rows="rows(store.id,'consumable')" :locks="locks(store.id,'consumable')" :readonly="!auth.canEditStore(store.id)" :can-manage-locks="auth.canManageLocks" :can-delete="auth.canManage" @refresh="load(true)" @error="errorMessage = $event" />
    </section>
  </main></div>
</template>

<style scoped>
.content{flex:1;min-width:0;padding:40px;background:#f5f7fa}.store-menu{position:sticky;top:15px;z-index:90;margin-bottom:28px;padding:18px;border:1px solid #e2e8f0;border-radius:12px;background:white;box-shadow:0 8px 22px #0f172a12}.menu-head{display:flex;align-items:center;justify-content:space-between}.menu-head h2{margin:0}nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}nav a{border-radius:7px;background:#2563eb;color:white;padding:7px 12px;text-decoration:none;font-weight:700}.store-section{scroll-margin-top:180px;margin-bottom:30px;padding:24px;border:1px solid #e2e8f0;border-radius:14px;background:#fff}.store-section>h2{padding-left:12px;border-left:5px solid #2563eb}.realtime{color:#b45309;font-size:13px;font-weight:700}.realtime.connected{color:#15803d}.error{padding:10px;background:#fee2e2;color:#b91c1c}.muted{color:#64748b}@media(max-width:700px){.content{padding:20px}}
</style>
