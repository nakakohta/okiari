<script setup lang="ts">
// 外部(親画面)から人数データを受け取るための型定義
interface Props {
  adminCount: number
  leaderCount: number
  subLeaderCount: number
  viewerCount: number
}

// 初期値(デフォルト値)を設定しつつ定義
withDefaults(defineProps<Props>(), {
  adminCount: 0,
  leaderCount: 0,
  subLeaderCount: 0,
  viewerCount: 0
})
</script>

<template>
  <div class="cards">
    <div class="card">
      <h3>管理者</h3>
      <h2 class="orange">{{ adminCount }}名</h2>
      <p>上限人数</p>
    </div>

    <div class="card">
      <h3>リーダー</h3>
      <h2 class="blue">{{ leaderCount }}名</h2>
      <p>上限人数</p>
    </div>

    <div class="card">
      <h3>サブリーダー</h3>
      <h2 class="green">{{ subLeaderCount }}名</h2>
      <p>上限人数</p>
    </div>

    <div class="card">
      <h3>閲覧専用</h3>
      <h2 class="gray">{{ viewerCount }}名</h2>
      <p>上限人数</p>
    </div>
  </div>
</template>

<style scoped>
/* UserManagement.vueからカードに関するCSSだけを引っ越し */
.cards {
  display: flex;
  gap: 20px;
  margin-top: 40px;
}
.card {
  background: white;
  width: 220px;
  padding: 25px;
  border-radius: 20px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); /* 少し影を足すと綺麗です */
}
.card h2 { font-size: 36px; }
.orange { color: #ff7a00; }
.blue { color: #2563ff; }
.green { color: #16a34a; }
.gray { color: #6b7280; }
</style>
