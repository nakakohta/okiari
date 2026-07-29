<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import DTable from '@/components/RestockTable/DTable.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { Product, RestockReport, Store } from '@/lib/types'

const auth = useAuthStore()
const stores = ref<Store[]>([])
const products = ref<Product[]>([])
const reports = ref<RestockReport[]>([])
const loading = ref(false)
const errorMessage = ref('')

const activeStores = computed(() => stores.value.filter(
  (store) => store.is_active && auth.canViewStore(store.id),
))

function reportsForStore(storeId: number) {
  return reports.value.filter((report) => report.store_id === storeId)
}

async function loadReports(silent = false) {
  if (!silent) loading.value = true
  try {
    reports.value = await reportService.drinkRefills()
  } catch {
    errorMessage.value = 'ドリンク補充情報を取得できませんでした'
  } finally {
    if (!silent) loading.value = false
  }
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [storeData, productData, reportData] = await Promise.all([
      mastersService.stores(),
      mastersService.products('drink'),
      reportService.drinkRefills(),
    ])
    stores.value = storeData
    products.value = productData.filter((product) => product.is_active)
    reports.value = reportData
  } catch {
    errorMessage.value = 'ドリンク補充情報を取得できませんでした'
  } finally {
    loading.value = false
  }
}

function mergeSavedReport(saved: RestockReport) {
  const index = reports.value.findIndex((report) => report.id === saved.id)
  if (index >= 0) {
    reports.value[index] = saved
    return
  }
  reports.value.unshift(saved)
}

function showSaveError(message: string) {
  errorMessage.value = message
}

const { realtimeState } = useRealtimeRefresh('restock_reports', () => loadReports(true))

onMounted(load)
</script>

<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="ドリンク補充" description="補充依頼を自動保存し、他の端末へ同期します。" />

      <div class="store-menu">
        <div class="menu-header">
          <h1>売店一覧</h1>
          <span class="realtime-state" :class="realtimeState">
            {{ realtimeState === 'connected' ? '● リアルタイム接続中' : '○ 再接続中' }}
          </span>
        </div>
        <nav class="store-links" aria-label="売店一覧">
          <a v-for="store in activeStores" :key="store.id" :href="`#store-${store.id}`">
            {{ store.name }}
          </a>
        </nav>
      </div>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <section
        v-for="store in activeStores"
        :id="`store-${store.id}`"
        :key="store.id"
        class="store-section"
      >
        <h2 class="store-title">{{ store.name }}</h2>
        <DTable
          :store="store"
          :products="products"
          :reports="reportsForStore(store.id)"
          :readonly="!auth.canEditStore(store.id)"
          @saved="mergeSavedReport"
          @error="showSaveError"
        />
      </section>

      <p v-if="!loading && activeStores.length === 0" class="empty">
        表示できる売店がありません。
      </p>
    </main>
  </div>
</template>

<style scoped>
.content {
  flex: 1;
  min-width: 0;
  padding: 40px;
  background: #f5f7fa;
}

.store-menu {
  position: sticky;
  top: 20px;
  z-index: 100;
  margin-bottom: 36px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: white;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.menu-header h1 {
  margin: 0;
  font-size: 22px;
}

.store-links {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 14px;
}

.store-links a {
  border-radius: 8px;
  background: #2563eb;
  color: white;
  padding: 8px 14px;
  text-decoration: none;
  font-weight: 700;
}

.realtime-state {
  color: #b45309;
  font-size: 13px;
  font-weight: 700;
}

.realtime-state.connected {
  color: #15803d;
}

.store-section {
  scroll-margin-top: 220px;
  margin-bottom: 38px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: white;
}

.store-title {
  margin: 0 0 22px;
  padding-left: 13px;
  border-left: 5px solid #2563eb;
  font-size: 26px;
}

.error {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fee2e2;
  color: #b91c1c;
}

.empty,
.muted {
  color: #64748b;
}

@media (max-width: 768px) {
  .content {
    padding: 20px;
  }

  .menu-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
