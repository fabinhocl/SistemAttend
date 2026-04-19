<template>
  <div class="min-h-screen bg-background-light dark:bg-background-dark p-6">
    <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">
      Dashboard
    </h1>
    <p class="text-slate-600 dark:text-slate-400 mt-4">
      Bem-vindo! Dashboard em construção...
    </p>
    <button
      @click="logout"
      class="mt-6 bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600"
    >
      Logout
    </button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { logout: authLogout } = useAuth()

const logout = () => {
  authLogout()
}
</script>
