<script setup lang="ts">
import { ref } from "vue"

type ContainerType = "bat" | "jar" | "input"

interface ContainerItem {
  id: number
  name: string
  type: ContainerType
  amount: number
}

interface FoodRow {
  id: number
  icon: string
  name: string
  subtitle: string
  notes: string
  containers: ContainerItem[]
}

type MenuState = {
  rowIndex: number
  containerIndex: number
} | null

const nextRowId = ref(2)
const nextContainerId = ref(3)

const items = ref<FoodRow[]>([
  {
    id: 1,
    icon: "🍛",
    name: "ライス",
    subtitle: "ごはん系",
    notes: "",
    containers: [
      { id: 1, name: "", type: "bat", amount: 100 },
      { id: 2, name: "", type: "bat", amount: 100 },
    ],
  },
])

const draggedRowIndex = ref<number | null>(null)
const openMenu = ref<MenuState>(null)


function deleteRow(index: number) {
  const ok = confirm("この品目を削除しますか？")
  if (!ok) return

  items.value.splice(index, 1)

  if (items.value.length === 0) addRow()
}

function addContainer(rowIndex: number) {
  items.value[rowIndex].containers.push({
    id: nextContainerId.value++,
    name: "",
    type: "input",
    amount: 0,
  })
}

function deleteContainer(rowIndex: number, containerIndex: number) {
  const ok = confirm("この項目を削除しますか？")
  if (!ok) return

  items.value[rowIndex].containers.splice(containerIndex, 1)

  if (items.value[rowIndex].containers.length === 0) {
    addContainer(rowIndex)
  }
}

function selectContainerType(
  rowIndex: number,
  containerIndex: number,
  type: ContainerType
) {
  const container = items.value[rowIndex].containers[containerIndex]
  container.type = type

  if (type === "input") {
    if (container.amount < 0) {
      container.amount = 0
    }
  } else {
    if (container.amount === 0) {
      container.amount = 100
    }
  }

  openMenu.value = null
}

function addRow() {
  items.value.push({
    id: nextRowId.value++,
    icon: "🍛",
    name: "",
    subtitle: "",
    notes: "",
    containers: [
      {
        id: nextContainerId.value++,
        name: "",
        type: "input",
        amount: 0,
      },
    ],
  })
}

function toggleTypeMenu(rowIndex: number, containerIndex: number) {
  const same =
    openMenu.value?.rowIndex === rowIndex &&
    openMenu.value?.containerIndex === containerIndex

  openMenu.value = same ? null : { rowIndex, containerIndex }
}

function closeTypeMenu() {
  openMenu.value = null
}

function getTypeLabel(type: ContainerType) {
  if (type === "bat") return "保温ボックス(青)"
  if (type === "jar") return "フードウォーマー"
  return "打込み"
}

function getTypeEmoji(type: ContainerType) {
  if (type === "bat") return "🍱"
  if (type === "jar") return "🍲"
  return "🔢"
}

function getAmountClass(amount: number) {
  if (amount >= 80) return "good"
  if (amount >= 30) return "warn"
  return "danger"
}

function getWariLabel(amount: number) {
  return `${Math.round(amount / 10)}割`
}

function getBatteryStyle(amount: number) {
  return { width: `${amount}%` }
}

function dragStart(index: number) {
  draggedRowIndex.value = index
}

function dragOver(event: DragEvent) {
  event.preventDefault()
}

function drop(index: number) {
  if (draggedRowIndex.value === null || draggedRowIndex.value === index) return

  const moved = items.value.splice(draggedRowIndex.value, 1)[0]
  items.value.splice(index, 0, moved)
  draggedRowIndex.value = null
  closeTypeMenu()
}
</script>

<template>
  <div class="mf-table" @click="closeTypeMenu">
    <div class="header">
      <div>
        <p class="desc">
          品目ごとに保温ボックス（10割表示）・フードウォーマー（10割表示）・数の直打込みができます。
        </p>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th class="col-item">品目</th>
            <th class="col-container">バット・フードウォーマー</th>
            <th class="col-notes">備考</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(item, rowIndex) in items"
            :key="item.id"
            class="row"
            draggable="true"
            @dragstart="dragStart(rowIndex)"
            @dragover="dragOver"
            @drop="drop(rowIndex)"
          >
            <td class="item-cell">
              <div class="item-head">
                <span class="grip" title="ドラッグして並び替え">⋮⋮</span>

                <div class="item-meta">
                  <div class="item-topline">
                    <span class="item-icon">{{ item.icon }}</span>
                    <input
                      v-model="item.name"
                      class="item-name"
                      type="text"
                      placeholder="品目名"
                    />
                  </div>

                  <input
                    v-model="item.subtitle"
                    class="item-subtitle"
                    type="text"
                    placeholder="サブテキスト"
                  />
                </div>
              </div>

              <button type="button" class="remove-row-btn" @click="deleteRow(rowIndex)">
                削除
              </button>
            </td>

            <td class="container-cell">
              <div class="container-list">
                <div
                  v-for="(container, containerIndex) in item.containers"
                  :key="container.id"
                  class="container-card"
                >
                  <div class="type-switch-wrap">
  <div class="type-row">
    <button
      type="button"
      class="type-trigger"
      @click.stop="toggleTypeMenu(rowIndex, containerIndex)"
    >
      <span class="type-trigger__emoji">{{ getTypeEmoji(container.type) }}</span>
      <span class="type-trigger__label">{{ getTypeLabel(container.type) }}</span>
      <span class="type-trigger__caret">▾</span>
    </button>

    <button
      type="button"
      class="container-delete"
      @click.stop="deleteContainer(rowIndex, containerIndex)"
      aria-label="削除"
    >
      ×
    </button>
  </div>

  <div
    v-if="openMenu?.rowIndex === rowIndex && openMenu?.containerIndex === containerIndex"
    class="type-menu"
    @click.stop
  >
    <button
      type="button"
      class="type-menu__item"
      @click="selectContainerType(rowIndex, containerIndex, 'bat')"
    >
      🍱 バット
    </button>
    <button
      type="button"
      class="type-menu__item"
      @click="selectContainerType(rowIndex, containerIndex, 'jar')"
    >
      🍲 フードウォーマー
    </button>
    <button
      type="button"
      class="type-menu__item"
      @click="selectContainerType(rowIndex, containerIndex, 'input')"
    >
      🔢 打込み
    </button>
  </div>
</div>

                  <template v-if="container.type === 'input'">
                    <div class="manual-entry">
                      <div class="manual-entry__label">打込み</div>

                      <div class="manual-entry__body">
                        <input
                          v-model.number="container.amount"
                          class="manual-entry__input"
                          type="number"
                          min="0"
                          step="1"
                          inputmode="numeric"
                          placeholder="0"
                          @wheel.prevent
                        />
                        <span class="manual-entry__unit">個</span>
                      </div>

                      <div class="manual-entry__hint">
                        数えられるものはこちらに入力
                      </div>
                    </div>
                  </template>

                  <template v-else>
                    <div class="battery-wrap">
                      <div class="battery" :class="getAmountClass(container.amount)">
                        <div class="battery-terminal"></div>
                        <div
                          class="battery-fill"
                          :style="getBatteryStyle(container.amount)"
                        ></div>

                        <div class="battery-content">
                          <span class="battery-amount">{{ getWariLabel(container.amount) }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="container-footer">
                      <input
                        v-model.number="container.amount"
                        class="range"
                        type="range"
                        min="0"
                        max="100"
                        step="5"
                      />
                    </div>
                  </template>
                </div>

                <button type="button" class="add-container-card" @click="addContainer(rowIndex)">
                  <span class="plus">＋</span>
                  <span>追加</span>
                </button>
              </div>
            </td>

            
            <td class="notes-cell">
              <textarea
                v-model="item.notes"
                class="notes"
                placeholder="備考を入力"
              ></textarea>
            </td>
          </tr>

          <tr>
            <td colspan="3" class="add-row-cell">
              <button type="button" class="add-row-btn" @click="addRow">
                ＋ 品目を追加
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.mf-table {
  padding: 20px;
  border-radius: 24px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
}

.header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.desc {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.table-wrap {
  overflow-x: auto;
  border-radius: 20px;
}

.table {
  width: 100%;
  min-width: 1200px;
  border-collapse: separate;
  border-spacing: 0;
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

thead th {
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
  border-bottom: 1px solid #dbe4ee;
  padding: 14px 12px;
  text-align: left;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  position: sticky;
  top: 0;
  z-index: 1;
}

tbody td {
  border-bottom: 1px solid #eef2f7;
  padding: 14px 12px;
  vertical-align: top;
}

tbody tr:last-child td {
  border-bottom: none;
}

.col-item {
  width: 22%;
}

.col-container {
  width: 46%;
}

.col-notes {
  width: 18%;
}

.item-cell {
  min-width: 240px;
}

.item-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 12px 10px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
  border: 1px solid #dbe4ee;
  border-left: 5px solid #2563eb;
}

.grip {
  width: 20px;
  min-width: 20px;
  margin-top: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #94a3b8;
  font-size: 16px;
  cursor: grab;
  user-select: none;
  letter-spacing: -2px;
  line-height: 1;
}

.item-meta {
  flex: 1;
  display: grid;
  gap: 8px;
}

.item-topline {
  display: flex;
  align-items: center;
  gap: 10px;
}

.item-icon {
  font-size: 22px;
  line-height: 1;
  flex-shrink: 0;
  width: 28px;
  text-align: center;
}

.item-name,
.item-subtitle {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #fff;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

.item-name {
  padding: 11px 12px;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.item-subtitle {
  padding: 8px 12px;
  font-size: 12px;
  color: #64748b;
}

.item-name:focus,
.item-subtitle:focus {
  border-color: #60a5fa;
  box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.14);
  transform: translateY(-1px);
}

.remove-row-btn {
  margin-top: 10px;
  border: 1px solid #fecaca;
  background: #fff;
  color: #ef4444;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.remove-row-btn:hover {
  background: #fff5f5;
}

.container-cell {
  min-width: 560px;
}

.container-list {
  display: flex;
  gap: 12px;
  flex-wrap: nowrap;
  align-items: stretch;
  overflow-x: auto;
  padding-bottom: 2px;
}

.container-card,
.add-container-card {
  flex: 0 0 220px;
  min-width: 220px;
  border-radius: 18px;
  padding: 12px;
}

.container-card {
  border: 1px solid #dbe4ee;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.container-card__top {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.container-title {
  flex: 1;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
  padding: 9px 11px;
  font-size: 13px;
  font-weight: 800;
  color: #334155;
  background: #f8fafc;
}

.container-delete {
  flex-shrink:0;

  width:32px;
  height:32px;

  border:1px solid #fecaca;
  border-radius:999px;

  background:#fff;
  color:#ef4444;

  font-size:18px;
  font-weight:700;
  cursor:pointer;
}

.type-switch-wrap {
  position: relative;
  margin-bottom: 10px;
}

.type-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  background: #fff;
  padding: 9px 12px;
  font-size: 12px;
  font-weight: 800;
  color: #334155;
  cursor: pointer;
}

.type-trigger__emoji {
  font-size: 14px;
}

.type-trigger__label {
  flex: 1;
  text-align: left;

  overflow:hidden;
  white-space:nowrap;
  text-overflow:ellipsis;
}

.type-trigger__caret {
  color: #94a3b8;
  font-size: 11px;
}

.type-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 20;
  width: 100%;
  background: #fff;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
  padding: 6px;
  display: grid;
  gap: 6px;
}

.type-menu__item {
  width: 100%;
  border: none;
  border-radius: 10px;
  background: #f8fafc;
  padding: 10px 12px;
  text-align: left;
  font-size: 12px;
  font-weight: 800;
  color: #334155;
  cursor: pointer;
}

.type-menu__item:hover {
  background: #e2e8f0;
}

.manual-entry {
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  padding: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.manual-entry__label {
  font-size: 11px;
  font-weight: 800;
  color: #334155;
  margin-bottom: 8px;
}

.manual-entry__body {
  display: flex;
  align-items: end;
  gap: 6px;
}

.manual-entry__input {
  width: 100%;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
  padding: 10px 10px;
  font-size: 22px;
  font-weight: 900;
  text-align: center;
  outline: none;
  background: #fff;
  color: #0f172a;
}

.manual-entry__unit {
  font-size: 12px;
  font-weight: 800;
  color: #64748b;
  padding-bottom: 8px;
}

.manual-entry__hint {
  margin-top: 6px;
  font-size: 10px;
  color: #64748b;
}

.battery-wrap {
  margin-bottom: 8px;
}

.battery {
  position: relative;
  height: 72px;
  border: 2px solid #cbd5e1;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
  overflow: hidden;
}

.battery-terminal {
  position: absolute;
  top: 25px;
  right: -9px;
  width: 9px;
  height: 20px;
  border-radius: 0 5px 5px 0;
  background: #cbd5e1;
}

.battery-fill {
  position: absolute;
  inset: 0;
  width: 100%;
  transition: width 0.2s ease;
}

.battery.good .battery-fill {
  background: linear-gradient(90deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.34));
}

.battery.warn .battery-fill {
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.18), rgba(245, 158, 11, 0.32));
}

.battery.danger .battery-fill {
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.16), rgba(239, 68, 68, 0.3));
}

.battery-content {
  position: relative;
  z-index: 1;
  height: 100%;
  display: grid;
  place-items: center;
  text-align: center;
  padding: 6px;
}

.battery-amount {
  font-size: 17px;
  font-weight: 900;
  color: #0f172a;
}

.container-footer {
  display: grid;
  gap: 6px;
}

.range {
  width: 100%;
  accent-color: #2563eb;
}

.add-container-card {
  border: 2px dashed #93c5fd;
  background: #eff6ff;
  color: #2563eb;
  font-weight: 800;
  cursor: pointer;
  display: grid;
  place-items: center;
  gap: 4px;
  align-content: center;
  transition: transform 0.15s ease, background-color 0.15s ease;
}

.add-container-card:hover {
  transform: translateY(-1px);
  background: #dbeafe;
}

.plus {
  font-size: 22px;
  line-height: 1;
}

.average-bar__fill.good {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.average-bar__fill.warn {
  background: linear-gradient(90deg, #f59e0b, #ea580c);
}

.average-bar__fill.danger {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.notes-cell {
  vertical-align: middle;
}

.notes {
  width: 100%;
  min-height: 130px;
  resize: vertical;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.6;
  outline: none;
}

.add-row-cell {
  padding: 14px 12px;
  background: #fff;
}

.add-row-btn {
  width: 100%;
  border: 2px dashed #3b82f6;
  background: #eff6ff;
  color: #1d4ed8;
  border-radius: 18px;
  padding: 14px 16px;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: transform 0.15s ease, background-color 0.15s ease;
}

.add-row-btn:hover {
  transform: translateY(-1px);
  background: #dbeafe;
}

@media (max-width: 768px) {
  .mf-table {
    padding: 14px;
  }

  .container-list {
    overflow-x: auto;
  }
}

.type-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

</style>