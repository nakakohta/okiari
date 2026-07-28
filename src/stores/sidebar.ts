import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSidebarStore = defineStore('sidebar', () => {
  const mealMenuOpen = ref(false)
  const drinkMenuOpen = ref(false)

  function toggleMealMenu() {
    mealMenuOpen.value = !mealMenuOpen.value
  }

  function toggleDrinkMenu() {
    drinkMenuOpen.value = !drinkMenuOpen.value
  }

  return {
    mealMenuOpen,
    drinkMenuOpen,
    toggleMealMenu,
    toggleDrinkMenu
  }
})