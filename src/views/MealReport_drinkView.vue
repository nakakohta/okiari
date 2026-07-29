<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import MDTable from '@/components/RestockTable/MDTable.vue'
import { useRealtimeRefresh } from '@/composables/useRealtimeRefresh'
import { mastersService, reportService } from '@/lib/services'
import { useAuthStore } from '@/stores/auth'
import type { MealReport, Product, Store } from '@/lib/types'

const auth = useAuthStore()
const stores = ref<Store[]>([])
const products = ref<Product[]>([])
const reports = ref<MealReport[]>([])
const reportDate = ref(new Date().toISOString().slice(0, 10))
const loading = ref(false)
const errorMessage = ref('')

const storeSections = computed(() => {
  const activeStores = stores.value.filter(
    (store) => store.is_active && auth.canViewStore(store.id),
  )
  return [
    {
      title: '1階・VIP・その他売店',
      stores: activeStores.filter(
        (store) => !store.name.startsWith('2-') && !store.name.startsWith('3-'),
      ),
    },
    {
      title: '2階売店',
      stores: activeStores.filter((store) => store.name.startsWith('2-')),
    },
    {
      title: '3階売店',
      stores: activeStores.filter((store) => store.name.startsWith('3-')),
    },
  ].filter((section) => section.stores.length > 0)
})

async function loadReports(silent = false) {
  if (!silent) loading.value = true
  try {
    reports.value = await reportService.mealReports(reportDate.value)
  } catch {
    errorMessage.value = '食数報告情報を取得できませんでした'
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
      mastersService.products('meal'),
      reportService.mealReports(reportDate.value),
    ])
    stores.value = storeData
    products.value = productData.filter((product) => product.is_active)
    reports.value = reportData
  } catch {
    errorMessage.value = '食数報告情報を取得できませんでした'
  } finally {
    loading.value = false
  }
}

function mergeSavedReport(saved: MealReport) {
  const index = reports.value.findIndex((report) => report.id === saved.id)
  if (index >= 0) {
    reports.value[index] = saved
    return
  }
  reports.value.push(saved)
}

function showSaveError(message: string) {
  errorMessage.value = message
}

const { realtimeState } = useRealtimeRefresh('meal_reports', () => loadReports(true))

watch(reportDate, () => {
  errorMessage.value = ''
  void loadReports()
})

onMounted(load)
</script>

<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="食数報告（ドリンク）" description="入力した食数を自動保存し、他の端末へ同期します。" />

      <div class="page-toolbar">
        <label>
          報告日
          <input v-model="reportDate" type="date" />
        </label>
        <span class="realtime-state" :class="realtimeState">
          {{ realtimeState === 'connected' ? '● リアルタイム接続中' : '○ 再接続中' }}
        </span>
      </div>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="loading" class="muted">読み込み中...</p>

      <section v-for="section in storeSections" :key="section.title" class="table-section">
        <MDTable
          :title="section.title"
          :report-date="reportDate"
          :stores="section.stores"
          :products="products"
          :reports="reports"
          :can-edit-store="auth.canEditStore"
          :readonly="!auth.canEditReports"
          @saved="mergeSavedReport"
          @error="showSaveError"
        />
      </section>
    </main>
  </div>
</template>

<style scoped>
.content {
  flex: 1;
  min-width: 0;
  padding: 40px;
}

.page-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px 20px;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
  background: #fff;
}

.page-toolbar label {
  display: grid;
  gap: 7px;
  color: #334155;
  font-weight: 700;
}

.page-toolbar input {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 9px 12px;
  font: inherit;
}

.realtime-state {
  color: #b45309;
  font-size: 13px;
  font-weight: 700;
}

.realtime-state.connected {
  color: #15803d;
}

.table-section {
  margin-bottom: 28px;
  padding: 22px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: white;
}

.muted {
  color: #64748b;
}

.error {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fee2e2;
  color: #b91c1c;
}

@media (max-width: 768px) {
  .content {
    padding: 20px;
  }

  .page-toolbar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
