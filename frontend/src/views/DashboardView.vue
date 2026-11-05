
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import { reportService } from '@/lib/services'
import type { InventoryCheck, MealReport, RestockReport } from '@/lib/types'

const loading = ref(false)
const errorMessage = ref('')
const meals = ref<MealReport[]>([])
const refills = ref<RestockReport[]>([])
const inventoryChecks = ref<InventoryCheck[]>([])

const today = new Date().toISOString().slice(0, 10)

const todayMealTotal = computed(() =>
  meals.value
    .filter((report) => report.report_date === today)
    .reduce((sum, report) => sum + report.quantity, 0),
)

const todayRefillCount = computed(() =>
  refills.value.filter(
    (report) => report.requested_at.slice(0, 10) === today,
  ).length,
)

const todayInventoryCount = computed(() =>
  inventoryChecks.value.filter(
    (report) => report.check_date === today,
  ).length,
)

const recentActivities = computed(() =>
  [
    ...meals.value.slice(0, 5).map((item) => ({
      type: '食数',
      title: `${item.store?.name || '-'} / ${item.product?.name || '-'}`,
      detail: `${item.quantity}${item.product?.unit || ''}`,
      date: item.created_at || item.report_date,
    })),
    ...refills.value.slice(0, 5).map((item) => ({
      type: '補充',
      title: `${item.store?.name || '-'} / ${item.product?.name || '-'}`,
      detail: `${item.quantity}${item.product?.unit || ''} / ${item.status}`,
      date: item.requested_at,
    })),
    ...inventoryChecks.value.slice(0, 5).map((item) => ({
      type: '棚卸',
      title: `${item.store?.name || '-'} / ${item.product?.name || '-'}`,
      detail: `差異 ${item.difference ?? item.actual_quantity - item.expected_quantity}`,
      date: item.created_at || item.check_date,
    })),
  ]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 10),
)

async function load() {
  loading.value = true
  errorMessage.value = ''

  try {
    const [mealData, refillData, inventoryData] = await Promise.all([
      reportService.mealReports(),
      reportService.drinkRefills(),
      reportService.inventoryChecks(),
    ])

    meals.value = mealData
    refills.value = refillData
    inventoryChecks.value = inventoryData
  } catch {
    errorMessage.value = 'ダッシュボード情報を取得できませんでした'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="layout dashboard-layout">
    <Sidebar />

    <main class="content">
      <AppHeader
        title="ダッシュボード"
        description="本日の業務状況と直近の報告を確認できます。"
      />

      <p v-if="errorMessage" class="error">
        {{ errorMessage }}
      </p>

      <p v-if="loading" class="muted loading">
        読み込み中...
      </p>

      <!-- 本日の集計カード -->
      <section class="summary-grid">

        <div class="summary-card meal-card">
          <div class="card-icon">▤</div>
          <span>本日の食数</span>
          <strong>{{ todayMealTotal }}</strong>
          <small>合計数量</small>
        </div>

        <div class="summary-card refill-card">
          <div class="card-icon">♧</div>
          <span>ドリンク補充</span>
          <strong>{{ todayRefillCount }}</strong>
          <small>本日の補充件数</small>
        </div>

        <div class="summary-card inventory-card">
          <div class="card-icon">▣</div>
          <span>棚卸件数</span>
          <strong>{{ todayInventoryCount }}</strong>
          <small>本日の確認件数</small>
        </div>

      </section>

      <!-- 直近の報告 -->
      <section class="panel">
        <div class="panel-header">
          <h2>直近の報告</h2>
          <span class="activity-count">
            {{ recentActivities.length }}件
          </span>
        </div>

        <!-- パソコン用テーブル -->
        <div class="desktop-table">
          <table>
            <thead>
              <tr>
                <th>種別</th>
                <th>内容</th>
                <th>詳細</th>
                <th>日時</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="activity in recentActivities"
                :key="`${activity.type}-${activity.date}-${activity.title}`"
              >
                <td>{{ activity.type }}</td>
                <td>{{ activity.title }}</td>
                <td>{{ activity.detail }}</td>
                <td>{{ new Date(activity.date).toLocaleString() }}</td>
              </tr>

              <tr v-if="recentActivities.length === 0">
                <td colspan="4" class="empty">
                  報告はまだありません
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- スマートフォン用カード一覧 -->
        <div class="mobile-activities">

          <article
            v-for="activity in recentActivities"
            :key="`mobile-${activity.type}-${activity.date}-${activity.title}`"
            class="activity-card"
          >
            <div class="activity-top">
              <span
                class="activity-type"
                :class="{
                  meal: activity.type === '食数',
                  refill: activity.type === '補充',
                  inventory: activity.type === '棚卸'
                }"
              >
                {{ activity.type }}
              </span>

              <time>
                {{ new Date(activity.date).toLocaleString() }}
              </time>
            </div>

            <p class="activity-title">
              {{ activity.title }}
            </p>

            <p class="activity-detail">
              {{ activity.detail }}
            </p>
          </article>

          <p
            v-if="recentActivities.length === 0"
            class="empty mobile-empty"
          >
            報告はまだありません
          </p>

        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>

/* ==================================
   共通・パソコン表示
================================== */

.dashboard-layout {
  display: flex;
  width: 100%;
  min-width: 0;
  min-height: 100vh;
}

.content {
  flex: 1;
  min-width: 0;
  padding: 40px;
  overflow-x: hidden;
}

/* 集計カード */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card,
.panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.summary-card {
  position: relative;
  padding: 22px;
  min-width: 0;
}

.summary-card span {
  display: block;
  color: #475569;
  font-weight: 700;
}

.summary-card strong {
  display: block;
  margin-top: 8px;
  font-size: 36px;
  color: #172033;
}

.summary-card small {
  display: block;
  margin-top: 4px;
  color: #64748b;
}

.card-icon {
  margin-bottom: 12px;
  color: #2563eb;
  font-size: 24px;
}

/* 報告一覧 */
.panel {
  padding: 24px;
  min-width: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.panel h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #172033;
}

.activity-count {
  color: #64748b;
  font-size: 13px;
}

.desktop-table {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid #eef2f7;
  text-align: left;
  color: #334155;
}

th {
  color: #475569;
  background: #f8fafc;
}

.mobile-activities {
  display: none;
}

.empty,
.muted {
  color: #64748b;
}

.error {
  color: #b91c1c;
  background: #fee2e2;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.loading {
  margin-bottom: 16px;
}

/* ==================================
   スマートフォン表示
================================== */

@media screen and (max-width: 767px) {

  .dashboard-layout {
    display: flex;
    flex-direction: column;
    width: 100%;
    min-width: 0;
    max-width: 100%;
  }

  .content {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    padding: 18px 16px 24px;
    overflow-x: hidden;
  }

  /* 集計カードを2列にする */
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-bottom: 18px;
  }

  .summary-card {
    padding: 14px;
    border-radius: 12px;
  }

  .summary-card span {
    font-size: 13px;
  }

  .summary-card strong {
    font-size: 28px;
    margin-top: 6px;
  }

  .summary-card small {
    font-size: 11px;
  }

  .card-icon {
    font-size: 21px;
    margin-bottom: 8px;
  }

  /* 直近の報告 */
  .panel {
    padding: 15px;
    border-radius: 12px;
  }

  .panel-header {
    margin-bottom: 12px;
  }

  .panel h2 {
    font-size: 17px;
  }

  /* パソコン用テーブルを隠す */
  .desktop-table {
    display: none;
  }

  /* スマホ用カード一覧を表示 */
  .mobile-activities {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .activity-card {
    width: 100%;
    min-width: 0;
    padding: 12px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #ffffff;
  }

  .activity-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;
  }

  .activity-type {
    padding: 4px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
  }

  .activity-type.meal {
    color: #1d4ed8;
    background: #dbeafe;
  }

  .activity-type.refill {
    color: #047857;
    background: #d1fae5;
  }

  .activity-type.inventory {
    color: #7c3aed;
    background: #ede9fe;
  }

  .activity-top time {
    color: #64748b;
    font-size: 10px;
  }

  .activity-title {
    color: #172033;
    font-size: 14px;
    font-weight: 700;
    overflow-wrap: anywhere;
  }

  .activity-detail {
    margin-top: 6px;
    color: #475569;
    font-size: 13px;
    overflow-wrap: anywhere;
  }

  .mobile-empty {
    padding: 20px 8px;
    text-align: center;
  }

}
</style>
