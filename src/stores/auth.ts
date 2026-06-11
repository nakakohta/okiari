import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isLoggedIn: false,
    role:''
  }),

  actions: {
    login(role: string) {
      this.isLoggedIn = true
      this.role = role
    },

    logout() {
      this.isLoggedIn = false
      this.role = ''
    }
  }
})
