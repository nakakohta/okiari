import { ref, computed } from "vue";
<template>
  <div class="d-table">

    <div class="header">
      <div>
        <h3>補充表</h3>
        <p>セルへ直接入力できます</p>
      </div>

      <div class="header-buttons">
        <button
          class="prepare-btn"
          @click="togglePrepareMode"
        >
          {{ prepareMode ? '全件表示' : '売店準備' }}
        </button>

        <button
          class="save-btn"
          @click="saveData"
        >
          エクスポート
        </button>
      </div>
    </div>

    <div class="toolbar">
      <button @click="addRow">
        ＋行追加
      </button>
    </div>

    <table>
      <thead>
        <tr>
          <th>補充状況</th>
          <th>商品名</th>
          <th>売店内にMAX置く数</th>
          <th>取ってくる数</th>
          <th>備考</th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="(item, index) in filteredItems"
          :key="index"
        >
          <td>
            <button
              class="status-btn"
              :class="{
                pending: item.status === '未補充',
                outstock: item.status === '在庫無い為未補充',
                complete: item.status === '完了'
              }"
              @click="openStatusModal(item)"
            >
              {{ item.status }}
            </button>
          </td>

          <td>
            <input v-model="item.name" />
          </td>

          <td>
            <input
              type="number"
              v-model.number="item.previous"
            />
          </td>

          <td>
            <input
              type="number"
              v-model.number="item.add"
            />
          </td>

          <td>
            <input v-model="item.memo" />
          </td>
        </tr>
      </tbody>
    </table>

    <div
      v-if="showModal"
      class="modal-overlay"
    >
      <div class="modal">
        <h3>補充状況を選択</h3>

        <button
          class="status-option status-red"
          @click="setStatus('未補充')"
        >
          未補充
        </button>

        <button
          class="status-option status-gray"
          @click="setStatus('在庫無い為未補充')"
        >
          在庫無い為未補充
        </button>

        <button
          class="status-option status-green"
          @click="setStatus('完了')"
        >
          完了
        </button>

        <button
          class="close-btn"
          @click="showModal = false"
        >
          キャンセル
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">

interface RestockItem {
  name: string;
  previous: number;
  add: number;
  memo: string;
  status: string;
}

const prepareMode = ref(false);

function togglePrepareMode() {
  prepareMode.value = !prepareMode.value;
}

const items = ref<RestockItem[]>([
  {
    name: "",
    previous: 0,
    add: 0,
    memo: "",
    status: "未補充"
  }
]);

const filteredItems = computed(() => {
  if (!prepareMode.value) {
    return items.value;
  }

  return items.value.filter(
    item =>
      item.status === "未補充" ||
      item.status === "在庫無い為未補充"
  );
});

function addRow() {
  items.value.push({
    name: "",
    previous: 0,
    add: 0,
    memo: "",
    status: "未補充"
  });
}

const showModal = ref(false);

const selectedItem = ref<RestockItem | null>(null);

function openStatusModal(item: RestockItem) {
  selectedItem.value = item;
  showModal.value = true;
}

function setStatus(status: string) {
  if (selectedItem.value) {
    selectedItem.value.status = status;
  }

  showModal.value = false;
}

function saveData() {
  console.log(items.value);
  alert("エクスポートしました");
}
</script>

<style scoped>
.restock-table {
  margin-bottom: 40px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-buttons {
  display: flex;
  gap: 10px;
}

.save-btn {
  background: #2f6df6;
  color: white;
  border: none;
  padding: 10px 25px;
  border-radius: 6px;
  cursor: pointer;
}

.prepare-btn {
  background: #f59e0b;
  color: white;
  border: none;
  padding: 10px 25px;
  border-radius: 6px;
  cursor: pointer;
}

.toolbar {
  margin-bottom: 15px;
}

.toolbar button {
  padding: 8px 15px;
  cursor: pointer;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

th {
  background: #f3f5f8;
  padding: 12px;
  border: 1px solid #ddd;
}

td {
  border: 1px solid #ddd;
  padding: 8px;
}

input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
}

.status-btn {
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 5px;
  cursor: pointer;
  min-width: 120px;
}

.pending {
  background: #ef4444;
}

.outstock {
  background: #9ca3af;
}

.complete {
  background: #22c55e;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);

  display: flex;
  justify-content: center;
  align-items: center;
}

.modal {
  background: white;
  padding: 30px;
  border-radius: 10px;
  width: 320px;

  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-option {
  border: none;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  color: white;
}

.status-red {
  background: #ef4444;
}

.status-gray {
  background: #9ca3af;
}

.status-green {
  background: #22c55e;
}

.close-btn {
  background: #e5e7eb;
  border: none;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
}
</style>