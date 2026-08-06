<script setup lang="ts">
import { ref } from "vue"

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

defineProps<{
  title: string
}>()

interface RestockItem {
  boothType: string
  booth: string
  customBooth: string

  name: string
  previous: number
  add: number
  memo: string
  status: string

  extra: string[]
}

const items = ref<RestockItem[]>([
  {
  boothType: "",
  booth: "",
  customBooth: "",

  name: "",
  previous: 0,
  add: 0,
  memo: "",
  status: "ブース",

  extra:[""]
  }
])

const columns = ref([
  { title: "商品名1" }
])

function addRow() {
  items.value.push({
    boothType:"",
    booth:"",
    customBooth:"",

    name:"",
    previous:0,
    add:0,
    memo:"",
    status:"ブース",

    extra:new Array(columns.value.length).fill("")
  })
}

function addColumn() {
  columns.value.push({
    title: `商品名${columns.value.length + 1}`
  })

  items.value.forEach(item => {
    item.extra.push("")
  })
}

function deleteColumn(index: number) {

  const result = confirm("この列を削除しますか？")
  if (!result) return

  // 見出し削除
  columns.value.splice(index, 1)

  // 全行の同じ列も削除
  items.value.forEach(item => {
    item.extra.splice(index, 1)
  })
}

function deleteRow(index: number) {
  const result = confirm("この行を削除しますか？")
  if (!result) return
  items.value.splice(index, 1)
}

function clearData() {
  const result = confirm(
    "書き込まれている食数を一斉クリアしますか？"
  )
  if (!result) return

  items.value.forEach(item => {
  // 追加した列の内容をすべて空白にする
  item.extra = item.extra.map(() => "")
  })
}

const lockMessage = ref(false)

function showLockMessage(){
  lockMessage.value=true
  setTimeout(()=>{
    lockMessage.value=false
  },2000)
}

const boothPopup = ref<number | null>(null)

function toggleBooth(index:number){
  boothPopup.value =
    boothPopup.value===index ? null : index
}

function selectBooth(item: RestockItem, booth: string) {
  item.booth = booth

  if (booth !== "その他") {
    boothPopup.value = null
  }
}

function confirmCustomBooth(item: RestockItem) {
  // 未入力なら何もしない
  if (item.customBooth.trim() === "") return

  // 表示用に「その他」のままにしておく
  item.booth = "その他"

  // ポップアップを閉じる
  boothPopup.value = null
}

const boothGroups = {
  first:[
    "CSL",
    "VIP(ブルー)",
    "VIP(レッド)",
    "その他"
  ],

  second:[
    "2-1",
    "2-2",
    "2-3",
    "2-4",
    "2-5",
    "2-6",
    "2-7",
    "2-8"
  ],

  third:[
    "3-1",
    "3-3",
    "3-5",
    "3-7",
    "3-9",
    "3-11(スイートラウンジ)"
  ]
}

</script>

<template>
  <div class="md-table">

    <div
      v-if="lockMessage"
      class="lock-warning"
      >
      編集したい場合はロックを解除してください
    </div>

    <div class="header">
          <h3>{{ title }}</h3>

      <div class="header-buttons">

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

      <button @click="addColumn">
        ＋列追加
      </button>
    </div>

<div class="table-wrapper">
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>
              売店名
              <button
                class="lock-icon"
                @click="toggleLock('status')"
              >
                {{ columnLock.status ? "🔒" : "🔓" }}
              </button>
            </th>
           
            <th
              v-for="(column,index) in columns"
              :key="index"
              class="dynamic-column"
            >
              <div class="column-header">

                <input
                  v-model="column.title"
                  class="column-title"
                />

                <button
                  class="delete-column-btn"
                  @click="deleteColumn(index)"
                >
                  ×
                </button>

  </div>
</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(item,index) in items"
            :key="index"
          >

<td class="booth-cell">

  <button
    class="booth-btn"
    @click="
      columnLock.status
        ? checkLock('status')
        : toggleBooth(index)
    "
  >
    ブース
  </button>

  <span class="selected-booth">
    {{
      item.booth==="その他"
      ? item.customBooth
      : item.booth
    }}
  </span>

  <div
    v-if="boothPopup===index"
    class="booth-popup"
  >

    <div class="popup-title">
      階数
    </div>

    <div class="floor-buttons">
      <button
        :class="{ active:item.boothType==='first' }"
        @click="item.boothType='first'"
      >
        1階
      </button>

      <button
        :class="{ active:item.boothType==='second' }"
        @click="item.boothType='second'"
      >
        2階
      </button>

      <button
        :class="{ active:item.boothType==='third' }"
        @click="item.boothType='third'"
      >
        3階
      </button>

</div>

    <hr>

    <template
      v-if="item.boothType==='first'"
    >
      <div class="booth-list">
        <button
          v-for="b in boothGroups.first"
          :key="b"
          @click="selectBooth(item, b)"
        >
          {{ b }}
        </button>
      </div>
    </template>

    <template
      v-if="item.boothType==='second'"
    >
      <div class="booth-list">
        <button
          v-for="b in boothGroups.second"
          :key="b"
          @click="selectBooth(item, b)"
        >
          {{ b }}
        </button>
      </div>
    </template>

    <template
      v-if="item.boothType==='third'"
    >
      <div class="booth-list">
        <button
          v-for="b in boothGroups.third"
          :key="b"
          @click="selectBooth(item, b)"
        >
          {{ b }}
        </button>
      </div>
    </template>

   <div
  v-if="item.booth === 'その他'"
  class="custom-booth"
>
  <input
    v-model="item.customBooth"
    :readonly="columnLock.status"
    @click="columnLock.status && checkLock('status')"
    placeholder="売店名を入力"
  />

  <button
    class="ok-btn"
    @click="confirmCustomBooth(item)"
  >
    OK
  </button>
</div>

  </div>

  <button
    class="remove-btn"
    @click="
      columnLock.status
        ? checkLock('status')
        : deleteRow(index)
    "
  >
    ×
  </button>

</td>

<td
  v-for="(cell,colIndex) in item.extra"
  :key="colIndex"
>
  <input
    v-model="item.extra[colIndex]"
  />
</td>
          </tr>
        </tbody>
      </table>
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
  overflow-y:visible;
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

.remove-btn{
  background:none;
  border:none;
  color:#ef4444;
  font-size:22px;
  cursor:pointer;
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

.booth-cell{
  position:relative;
  min-width:220px;
}

.booth-btn{
  background:#2563eb;
  color:white;
  border:none;
  border-radius:6px;
  padding:8px 14px;
  font-weight:bold;
  cursor:pointer;
}

.selected-booth{
  margin-left:10px;
  font-weight:bold;
  display:inline-block;
  max-width:130px;
  word-break:break-word;
}

.booth-popup{
  position:absolute;
  top:42px;
  left:0;

  width:320px;

  background:#fff;
  border:1px solid #d1d5db;
  border-radius:12px;

  padding:16px;

  box-shadow:0 10px 25px rgba(0,0,0,.18);

  display:flex;
  flex-direction:column;
  gap:14px;

  z-index:99999;
}

.popup-title{
  font-size:15px;
  font-weight:bold;
  margin-bottom:4px;
}

.booth-popup button.active{
  background:#2563eb;
  color:white;
  font-weight:bold;
}

.custom-booth{
  width:100%;
  display:flex;
  gap:8px;
  margin-top:10px;
}

.custom-booth input{
  flex:1;
}

.ok-btn{
  padding:6px 14px;
  border:none;
  border-radius:6px;
  background:#2563eb;
  color:white;
  cursor:pointer;
}

.ok-btn:hover{
  background:#1d4ed8;
}

.column-title{
  width:100%;
  text-align:center;
  border:none;
  background:transparent;
  font-weight:bold;
  font-size:15px;
}

.floor-buttons{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:8px;
}

.booth-list{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:8px;
}

.booth-popup button{
  padding:8px 10px;
  border:none;
  border-radius:8px;
  background:#f3f4f6;
  cursor:pointer;
  transition:.2s;
}

.booth-popup button:hover{
  background:#dbeafe;
}

.table-section{
  position: relative;
  background:#fff;
  border-radius:16px;
  padding:28px;
  margin-bottom:40px;
  border:1px solid #e5e7eb;
  box-shadow:
    0 4px 12px rgba(0,0,0,.05);
  overflow: visible;
}

.table-section h2{
  display:inline-block;
  margin:0 0 20px;
  padding:8px 18px;
  background:#2563eb;
  color:white;
  border-radius:999px;
  font-size:18px;
  font-weight:700;
}

.booth-popup{
  position:absolute;
  top:48px;
  left:0;
  width:340px;
  background:white;
  border-radius:14px;
  border:1px solid #d1d5db;
  box-shadow:
      0 18px 50px rgba(0,0,0,.25);
  padding:18px;
  z-index:99999;
}

.booth-popup::before{
    content:"";
    position:absolute;
    top:-10px;
    left:25px;
    border-left:10px solid transparent;
    border-right:10px solid transparent;
    border-bottom:10px solid white;
}

.dynamic-column{
  min-width:150px;
}

.column-header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:6px;
}

.delete-column-btn{
  width:22px;
  height:22px;

  border:none;
  background:none;

  color:#ef4444;
  font-size:18px;

  cursor:pointer;
  border-radius:50%;
}

.delete-column-btn:hover{
  background:#fee2e2;
}

</style>