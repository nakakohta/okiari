<script setup lang="ts">
import { ref, computed } from "vue"

// 列ロック状態
const columnLock = ref({
  status:false,
  name:false,
  previous:false,
  add:false,
  memo:false
})

// ロック切替
function toggleLock(column:string){
  columnLock.value[column] =
    !columnLock.value[column]
}

// ロック警告
function checkLock(column:string){
  if(columnLock.value[column]){
    showLockMessage()
  }
}

  function showModeMessage(message:string){
  modeMessageText.value = message
  modeMessage.value = true
  setTimeout(() => {
    modeMessage.value = false
  }, 3000)
}

defineProps<{
  title: string
}>()

interface RestockItem {
  name: string
  previous: number
  add: number
  memo: string
  status: string
}

const prepareMode = ref(false)

function togglePrepareMode() {
  prepareMode.value = !prepareMode.value
  if (prepareMode.value) {
    showModeMessage(
      "売店準備モードです！！ 補充状況が「未補充」「在庫無い為未補充」のみを表示します！"
    )
  } else {
    showModeMessage(
      "興行日モードになりました！！ 在庫確認頑張ってください！！ (◝ ⌄ ◜)"
    )
  }
}

const items = ref<RestockItem[]>([
  {
    name: "",
    previous: 0,
    add: 0,
    memo: "",
    status: "未補充"
  }
])

const filteredItems = computed(() => {
  if (!prepareMode.value) {
    return items.value
  }

  return items.value.filter(
    item =>
      item.status === "未補充" ||
      item.status === "在庫無い為未補充"
  )
})

function addRow() {
  items.value.push({
    name: "",
    previous: 0,
    add: 0,
    memo: "",
    status: "未補充"
  })
}

function deleteRow(index: number) {
  const result = confirm("この行を削除しますか？")
  if (!result) return
  items.value.splice(index, 1)
}

const showModal = ref(false)
const selectedItem = ref<RestockItem | null>(null)

function openStatusModal(item: RestockItem) {
  selectedItem.value = item
  showModal.value = true
}

function setStatus(status: string) {
  if (selectedItem.value) {
    selectedItem.value.status = status
  }
  showModal.value = false
  selectedItem.value = null
}

function clearData() {
  const result = confirm(
    "売店準備で補充が全て終わったら押すボタンです。補充状況・取ってくる数・備考をクリアしますか？"
  )
  if (!result) return
  items.value.forEach(item => {
    item.status = "未補充"
    item.add = 0
    item.memo = ""
  })
prepareMode.value = false
}

const modeMessage = ref(false)
const modeMessageText = ref("")
const lockMessage = ref(false)

function showLockMessage(){
  lockMessage.value=true
  setTimeout(()=>{
    lockMessage.value=false
  },2000)
}
</script>

<template>
  <div class="d-table">

    <div
      v-if="lockMessage"
      class="lock-warning"
      >
      編集したい場合はロックを解除してください
    </div>

    <div
      v-if="modeMessage"
      class="mode-popup"
    >
      {{ modeMessageText }}
    </div>

    <div class="header">
          <h3>{{ title }}</h3>

      <div class="header-buttons">

  <button
    class="prepare-btn"
    :class="{ active: prepareMode }"
    @click="togglePrepareMode"
  >
    {{ prepareMode ? "売店準備" : "興行日"}}
  </button>

  <button
    class="clear-btn"
    @click="clearData"
  >
    クリア
  </button>

</div>
    </div>

    <div class="toolbar">
      <button @click="addRow">
        ＋行追加
      </button>
    </div>

<div class="table-wrapper">
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>
              補充状況
              <button
                class="lock-icon"
                @click="toggleLock('status')"
              >
                {{ columnLock.status ? "🔒" : "🔓" }}
              </button>
            </th>

            <th>
              商品名
              <button
                class="lock-icon"
                @click="toggleLock('name')"
              >
                {{ columnLock.name ? "🔒" : "🔓" }}
              </button>
            </th>

            <th>
              売店内MAX
              <button
                class="lock-icon"
                @click="toggleLock('previous')"
              >
                {{ columnLock.previous ? "🔒" : "🔓" }}
              </button>
            </th>
            <th>
              取ってくる数
              <button
                class="lock-icon"
                @click="toggleLock('add')"
              >
                {{ columnLock.add ? "🔒" : "🔓" }}
              </button>
            </th>

            <th>
              備考
              <button
                class="lock-icon"
                @click="toggleLock('memo')"
              >
                {{ columnLock.memo ? "🔒" : "🔓" }}
              </button>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(item,index) in filteredItems"
            :key="index"
            :class="{
              selectedRow: selectedItem === item
            }"
          >
            <td>
              <div class="status-wrapper">

                <button
                  class="status-btn"
                  :class="{
                    pending:item.status==='未補充',
                    outstock:item.status==='在庫無い為未補充',
                    complete:item.status==='完了'
                  }"
                  @click="columnLock.status
                  ? checkLock('status')
                  : openStatusModal(item)"
                >
                  {{ item.status }}
                </button>

                <button
                  class="remove-btn"
                  @click="deleteRow(index)"
                >
                  ×
                </button>

              </div>
            </td>

            <td
              class="sticky-name">
              <input 
                v-model="item.name" 
                :readonly="columnLock.name"
                @click="checkLock('name')"
              />

            </td>

            <td>
              <input
                type="number"
                v-model.number="item.previous"
                :readonly="columnLock.previous"
                @click="checkLock('previous')"
              />
            </td>

            <td class="sticky-add">
              <input
                type="number"
                v-model.number="item.add"
                :readonly="columnLock.add"
                @click="checkLock('add')"
              />
            </td>

            <td>
              <input 
                v-model="item.memo"
                :readonly="columnLock.memo"
                @click="checkLock('memo')"
              />
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <div
  v-if="showModal"
  class="modal-overlay"
>
  <div class="modal">
    <button
      class="modal-close"
      @click="showModal = false"
    >
      ×
    </button>

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
  </div>
</div>
  </div>
</template>



<style scoped>
.d-table{
  margin-bottom:40px;
}

.header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:20px;
}

.header-buttons{
  display:flex;
  gap:10px;
}

.prepare-btn{
  background:#ef4444;
  color:white;
  border:none;
  padding:10px 25px;
  border-radius:6px;
  cursor:pointer;
}

.prepare-btn.active{
  background:#2563eb;
}

.clear-btn{
  background:#6b7280;
  color:white;
  border:none;
  padding:10px 25px;
  border-radius:6px;
  cursor:pointer;
}

.clear-btn:hover{
  background:#4b5563;
}

.toolbar{
  margin-bottom:15px;
}

.toolbar button{
  padding:8px 15px;
  cursor:pointer;
}

.table-container{
  overflow-x:auto;
  width:100%;
}

table{
  width:max-content;
  min-width:100%;
  border-collapse:collapse;
  background:white;
}

th,
td{
  border:1px solid #ddd;
  padding:10px;
  white-space:nowrap;
}

th{
  background:#f3f5f8;
  text-align:center;
}

input{
  border:none;
  outline:none;
  background:transparent;
  min-width:100px;
  width:100%;
  padding:4px;
}

.status-wrapper{
  display:flex;
  align-items:center;
  gap:12px;
}

.status-btn{
  color:white;
  border:none;
  padding:6px 12px;
  border-radius:5px;
  cursor:pointer;
  min-width:120px;
}

.pending{
  background:#ef4444;
}

.outstock{
  background:#9ca3af;
}

.complete{
  background:#22c55e;
}

.remove-btn{
  background:none;
  border:none;
  color:#ef4444;
  font-size:22px;
  cursor:pointer;
}

.modal-overlay{
  position:fixed;
  inset:0;
  background:rgba(0,0,0,.4);
  z-index:1000;

  display:flex;
  justify-content:center;
  align-items:center;
}

.modal{
  position:relative;

  background:white;
  padding:30px;
  border-radius:10px;
  width:320px;

  display:flex;
  flex-direction:column;
  gap:12px;

  z-index:1002;
}
.modal-close{
  position:absolute;
  top:8px;
  right:12px;

  border:none;
  background:none;

  font-size:28px;
  cursor:pointer;

  color:#555;
}

.modal-close:hover{
  color:#000;
}

.status-option{
  border:none;
  padding:12px;
  border-radius:6px;
  color:white;
  cursor:pointer;
}

.status-red{
  background:#ef4444;
}

.status-gray{
  background:#9ca3af;
}

.status-green{
  background:#22c55e;
}

.lock-icon{
  margin-left:6px;
  width:22px;
  height:22px;
  border-radius:50%;
  border:none;
  background:white;
  box-shadow:
    0 1px 4px rgba(0,0,0,.25);
  font-size:13px;
  cursor:pointer;
  display:inline-flex;
  justify-content:center;
  align-items:center;
  vertical-align:middle;
}

/* ロック時入力不可 */
input[readonly]{
  cursor:not-allowed;
  background:#f3f4f6;
}

/* 警告 */
.lock-warning{
  position:sticky;
  top:0;
  z-index:2000;
  background:#fee2e2;
  color:#dc2626;
  border:1px solid #dc2626;
  padding:12px;
  text-align:center;
  font-weight:bold;
  margin-bottom:10px;
  border-radius:6px;
}

.mode-popup{
  position:sticky;
  top:0;
  z-index:1999;
  background:#dbeafe;
  color:#1d4ed8;
  border:1px solid #2563eb;
  padding:12px;
  text-align:center;
  font-weight:bold;
  margin-bottom:10px;
  border-radius:6px;
}

</style>