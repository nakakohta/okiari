<script setup lang="ts">
import { ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import Sidebar from '@/components/AppSidebar.vue'
import MFTable from '@/components/RestockTable/MFTable.vue'

type StoreSection = {
  id: number
  name: string
}

const storeOptions = [
  "CSL",
  "2-1",
  "2-2",
  "2-3",
  "2-4",
  "2-5",
  "2-6",
  "2-7",
  "2-8",
  "3-1",
  "3-3",
  "3-5",
  "3-7",
  "3-9",
  "3-11",
  "その他",
]

const tableSections = ref<StoreSection[]>([
  {
    id: 1,
    name: "CSL",
  },
])

let nextSectionId = 2

function addStoreSection() {
  tableSections.value.push({
    id: nextSectionId++,
    name: "CSL",
  })
}

function removeStoreSection(id: number) {
  if (!confirm("この売店を削除しますか？")) return

  tableSections.value = tableSections.value.filter(
    section => section.id !== id
  )
}

const draggedSectionIndex = ref<number | null>(null)

function dragStartSection(index: number) {
  draggedSectionIndex.value = index
}

function dragOverSection(event: DragEvent) {
  event.preventDefault()
}

function dropSection(index: number) {
  if (
    draggedSectionIndex.value === null ||
    draggedSectionIndex.value === index
  ) {
    return
  }

  const moved = tableSections.value.splice(
    draggedSectionIndex.value,
    1
  )[0]

  if (!moved) return
  tableSections.value.splice(index, 0, moved)

  draggedSectionIndex.value = null
}

</script>


<template>
  <div class="layout">
    <Sidebar />
    <main class="content">
      <AppHeader title="食数報告(フード)" description="場所・商品ごとの食数を登録します。" />
<section
  v-for="(section, index) in tableSections"
  :key="section.id"
  class="table-section"
  draggable="true"
  @dragstart="dragStartSection(index)"
  @dragover="dragOverSection"
  @drop="dropSection(index)"
>
  <div class="section-header">

  <div class="section-left">
    <span class="section-grip">⋮⋮</span>

    <select
      v-model="section.name"
      class="store-select"
    >
      <option
        v-for="store in storeOptions"
        :key="store"
        :value="store"
      >
        {{ store }}
      </option>
    </select>
  </div>

  <button
    class="delete-btn"
    @click="removeStoreSection(section.id)"
  >
    🗑
  </button>

</div>

<MFTable />

</section>

<div class="add-section">
  <button
    class="add-btn"
    @click="addStoreSection"
  >
    ＋ 売店を追加
  </button>
</div>
    </main>
  </div>
</template>


<style scoped>
.section-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:20px;
}

.section-left{
  display:flex;
  align-items:center;
  gap:10px;
}

.store-select{
  width:auto;
  min-width:120px;
  padding-right:24px;
  font-size:22px;
  font-weight:bold;
  border:none;
  outline:none;
  background:transparent;
  cursor:pointer;
}

.delete-btn{
   margin-left:auto;
}

.content {
  flex: 1;
  padding: 40px;
}

h2 {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 800;
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
}

.table-section{
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 32px;
}

.table-section h2{
  margin: 0 0 20px;
  font-size: 22px;
  font-weight: bold;
}

.delete-btn:hover{
  background:#dc2626;
  transform:scale(1.05);
}

.add-section{
  display:flex;
  justify-content:center;
}

.add-btn{
  padding:14px 28px;
  border:none;
  border-radius:10px;
  background:#2563eb;
  color:white;
  font-size:16px;
  font-weight:bold;
  cursor:pointer;
  transition:.2s;
}

.add-btn:hover{
  background:#1d4ed8;
}

.section-grip{
  width:28px;
  min-width:28px;
  display:flex;
  justify-content:center;
  align-items:center;
  font-size:22px;
  color:#94a3b8;
  cursor:grab;
  user-select:none;
  letter-spacing:-3px;
  line-height:1;
}

.section-grip:active{
  cursor:grabbing;
}

.section-grip{
  cursor: grab;
}

.section-grip:active{
  cursor: grabbing;
}

.table-section{
  transition: .2s;
}
</style>
