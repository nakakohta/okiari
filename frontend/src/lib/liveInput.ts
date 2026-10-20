// Read the DOM value rather than v-model: Vue deliberately leaves v-model
// unchanged until an IME composition has been committed.
export function readInputValue(event: Event): string | number {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  const value = target.value
  if ((target.type === 'number' || target.type === 'range') && value !== '') {
    const number = Number(value)
    if (Number.isFinite(number)) return number
  }
  return value
}
