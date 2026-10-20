import { createApp, defineComponent, h, nextTick, ref } from 'vue'
import DTable from '@/components/RestockTable/DTable.vue'
import MDTable from '@/components/RestockTable/MDTable.vue'
import MFTable from '@/components/RestockTable/MFTable.vue'
import MTable from '@/components/RestockTable/MTable.vue'
import { provideLiveBoard } from '@/composables/useLiveBoard'
import { listeners, records, writes } from './mocks'
import type { DTableRow } from '@/lib/types'

for (const id of ['left', 'right']) {
  createApp(defineComponent({ setup() {
    const rows = ref<DTableRow[]>(structuredClone(records) as DTableRow[])
    const refresh = () => { rows.value = structuredClone(records) as DTableRow[] }
    listeners.add(refresh)
    provideLiveBoard('drink-refill', refresh)
    return () => h('section', [h('h2', id === 'left' ? 'ユーザーA' : 'ユーザーB'), h(DTable, {
      title: 'ドリンク補充', storeId: 1, scope: 'drink', rows: rows.value, locks: [],
      readonly: false, canManageLocks: false, canDelete: false, onRefresh: refresh,
    }), h(MDTable, {
      title: '食数報告ドリンク', floorGroup: 'first', canEditStructure: true, canSelectBooth: true,
      canManageLocks: false, canDelete: false, canEditBooth: () => true, locks: [],
      rows: [{ id: 101, board_id: 1, floor_group: 'first', booth_type: 'first', booth: 'その他', custom_booth: '', sort_order: 0 }],
      columns: [{ id: 102, board_id: 1, floor_group: 'first', title: '', sort_order: 0 }],
      cells: [{ id: 103, board_id: 1, row_id: 101, column_id: 102, value: '', updated_at: '' }],
    }), h(MFTable, {
      sectionId: 1, readonly: false, canDelete: false,
      rows: [{ id: 104, board_id: 1, section_id: 1, icon: '', item_name: '', subtext: '', note: '', sort_order: 0 }],
      containers: [{ id: 105, board_id: 1, row_id: 104, name: '', quantity: 0, container_type: 'register', sort_order: 0 }],
    }), h(MTable, {
      rows: [{ id: 106, board_id: 1, store_id: 1, product_id: 1, expected_quantity: 0, actual_quantity: 0, difference: 0, note: '', is_confirmed: false, sort_order: 0, updated_at: '' }],
      stores: [], products: [], canEditStore: () => true, canConfirm: false, canDelete: false,
    })])
  } })).mount('#' + id)
}
const input = (client: string, id: number, field = 'item_name') => document.querySelector<HTMLInputElement>(`#${client} [data-live-field="d-rows:${id}:${field}"]`)!
function send(element: HTMLInputElement, value: string, composing = false) {
  element.value = value
  element.dispatchEvent(new InputEvent('input', { bubbles: true, isComposing: composing, inputType: 'insertText' }))
}
function check(condition: boolean, description: string, results: string[]) {
  if (!condition) throw new Error(description)
  results.push('PASS ' + description)
}
document.querySelector('#run')!.addEventListener('click', async () => {
  const results: string[] = []
  try {
    const a = input('left', 2), b = input('right', 2)
    a.focus()
    a.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }))
    send(a, 'お', true); await nextTick()
    check(b.value === 'お', 'Enter前に「お」が他ユーザーへ反映', results)
    send(a, 'おちゃ', true); await nextTick()
    check(b.value === 'おちゃ', '変換途中の「おちゃ」が反映', results)
    listeners.forEach(refresh => refresh()); await nextTick()
    check(a.value === 'おちゃ' && b.value === 'おちゃ', '他ユーザー更新による再描画でIME入力が消えない', results)
    check(writes.length === 0, '未確定IME文字はDB保存しない', results)
    a.value = 'お茶'
    a.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: 'お茶' })); await nextTick()
    check(b.value === 'お茶', '確定した文字が反映', results)
    send(a, 'お'); await nextTick()
    check(b.value === 'お', 'Backspace相当の削除が即時反映', results)
    send(input('left', 3), '行3編集'); await nextTick()
    check(input('right', 3).value === '行3編集' && input('right', 1).value === '行1', '同じ表示順の別行に誤入力されない', results)
    const rowIds = (client: string) => [...document.querySelectorAll(`#${client} .d-table [data-live-field$=":item_name"]`)].map(element => element.getAttribute('data-live-field'))
    check(JSON.stringify(rowIds('left')) === JSON.stringify(rowIds('right')), '重複する表示順も両ユーザーで一致', results)
    for (const client of ['left', 'right']) (document.querySelector(`#${client} .toolbar button`) as HTMLButtonElement).click()
    await new Promise(resolve => setTimeout(resolve, 450)); await nextTick()
    check(JSON.stringify(rowIds('left')) === JSON.stringify(rowIds('right')) && rowIds('left').length === 5, '同時行追加・保存後も行の順番が一致', results)
    check(records.find(row => row.id === 2)?.item_name === 'お', '最後の確定入力がDB保存される', results)
    for (const client of ['left', 'right']) (document.querySelector(`#${client} .booth`) as HTMLButtonElement).click()
    await nextTick()
    const extraFields = [...document.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('#left .md-table [data-live-field], #left .mf-table [data-live-field], #left .m-table [data-live-field]')].filter(element => element.type !== 'number' && element.type !== 'range')
    for (const element of extraFields) {
      const key = element.dataset.liveField!
      const peer = document.querySelector<HTMLInputElement | HTMLTextAreaElement>(`#right [data-live-field="${key}"]`)!
      element.focus(); element.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }))
      element.value = 'あ'
      element.dispatchEvent(new InputEvent('input', { bubbles: true, isComposing: true })); await nextTick()
      check(peer.value === 'あ', `${key}のIME途中が反映`, results)
      element.value = '愛'
      element.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: '愛' })); await nextTick()
      check(peer.value === '愛', `${key}の確定が反映`, results)
    }
    results.push('全ブラウザ回帰テスト成功')
  } catch (error) { results.push('FAIL ' + String(error)) }
  document.querySelector('#result')!.textContent = results.join('\n')
})
