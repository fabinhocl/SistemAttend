<template>
  <div class="bg-background-light dark:bg-background-dark font-display text-slate-900 dark:text-slate-100 min-h-screen flex flex-col">
    <!-- Header Section -->
    <div class="relative flex h-auto w-full flex-col bg-white dark:bg-background-dark overflow-x-hidden">
      <div class="flex items-center bg-white dark:bg-background-dark p-4 pb-2 justify-between">
        <div class="text-slate-900 dark:text-slate-100 flex size-12 shrink-0 items-center justify-start">
          <span class="material-symbols-outlined" style="font-size: 24px">arrow_back</span>
        </div>
        <h2 class="text-slate-900 dark:text-slate-100 text-lg font-bold leading-tight tracking-tight flex-1 text-center pr-12">
          Attend
        </h2>
      </div>

      <!-- Hero Illustration Logo Area -->
      <div class="container">
        <div class="w-full bg-center bg-no-repeat bg-cover flex flex-col justify-end overflow-hidden bg-primary10 rounded-lg min-h-60 relative"
          style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuCWehol3Z-u3d96FuhcIhYxuGSnVIVXZIwjGJUt4M8tgC40Lw-7xt1qqrSdPN3tk655-CaK6HAskXBMIiFkhtIQ46g7pK6ebCXSSLv4ds6LyPoj0MQX4tXwxNRujzITVTEgeUeATEQ8fQvAopOqXbRl8jAghXbMpcugvfpXzh3ueCZXMKc1vtlR3CCBNgG5OWivWxIAxZ7Dr9ZYj5e3Eb4uD8WUk28B-nMIRGVufEF7JJLCSP-l5gpUdwW3CInephi7bQsccO5')">
          <div class="absolute inset-0 bg-gradient-to-t from-primary-60 to-transparent"></div>
          <div class="relative p-6">
            <div class="bg-white dark:bg-slate-900 w-14 h-14 rounded-xl flex items-center justify-center shadow-lg mb-2">
              <span class="material-symbols-outlined text-primary" style="font-size: 32px; font-variation-settings: 'FILL' 1">
                menu_book
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Welcome Text -->
    <div class="px-6 pt-8 pb-4">
      <h1 class="text-slate-900 dark:text-slate-100 tracking-tight text-3xl font-bold leading-tight">
        Bem-vindo de volta
      </h1>
      <p class="text-slate-600 dark:text-slate-400 text-base font-normal mt-2">
        Gerencie suas aulas e acompanhe o progresso com facilidade.
      </p>
    </div>

    <!-- Login Form -->
    <div class="flex flex-col gap-4 px-6 py-2">
      <label class="flex flex-col w-full">
        <p class="text-slate-900 dark:text-slate-100 text-sm font-semibold leading-normal pb-2">
          E-mail
        </p>
        <div class="relative">
          <span class="material-symbols-outlined absolute left-4 top-12 -translate-y-12 text-slate-400" style="font-size: 20px">
            mail
          </span>
          <input
            v-model="form.email"
            type="email"
            class="form-input flex w-full rounded-xl text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 h-14 pl-12 pr-4 focus:ring-2 focus:ring-primary focus:border-primary placeholder:text-slate-400 font-normal transition-all"
            placeholder="seu@email.com"
          />
        </div>
      </label>

     <label class="flex flex-col w-full mt-2">
        <p class="text-slate-900 dark:text-slate-100 text-sm font-semibold leading-normal pb-2">
          Senha
        </p>
        <div class="relative">
          <span class="material-symbols-outlined absolute left-4 top-12 -translate-y-12 text-slate-400" style="font-size: 20px">
            lock
          </span>
          <input
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            class="form-input flex w-full rounded-xl text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 h-14 pl-12 pr-12 focus:ring-2 focus:ring-primary focus:border-primary placeholder:text-slate-400 font-normal transition-all"
            placeholder="•••••••••"
          />
          <button
            type="button"
            @click="showPassword = !showPassword"
            class="absolute right-4 top-12 -translate-y-12 text-slate-400 hover:text-primary"
          >
            <span class="material-symbols-outlined" style="font-size: 20px">
              {{ showPassword ? 'visibility_off' : 'visibility' }}
            </span>
          </button>
        </div>
      </label>

      <div class="flex justify-end">
        <a href="#" class="text-primary text-sm font-semibold hover:underline">
          Esqueceu a senha?
        </a>
      </div>

      <button
        @click="handleLogin"
        :disabled="loading"
        class="w-full bg-primary text-white font-bold py-4 rounded-xl shadow-lg shadow-primary/20 hover:bg-primary/90 transition-colors mt-4 flex items-center justify-center gap-2 disabled:opacity-50"
      >
        <span>{{ loading ? 'Entrando...' : 'Entrar' }}</span>
        <span class="material-symbols-outlined" style="font-size: 20px">login</span>
      </button>

      <!-- Error Message -->
      <div v-if="error" class="text-red-500 text-sm text-center mt-2">
        {{ error }}
      </div>
    </div>

    <!-- Alternative Access -->
    <div class="px-6 py-8">
      <div class="relative flex items-center gap-4 mb-6">
        <div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
        <span class="text-slate-400 text-xs font-bold uppercase tracking-widest">Acesso Rápido</span>
        <div class="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
      </div>

      <div class="flex flex-col gap-3">
        <p class="text-slate-600 dark:text-slate-400 text-sm text-center mb-1">
          É aluno ou responsável?
        </p>
        <button class="w-full bg-primary/10 text-primary font-bold py-4 rounded-xl border border-primary/20 hover:bg-primary/20 transition-colors flex items-center justify-center gap-2">
          <span class="material-symbols-outlined" style="font-size: 20px">qr_code_scanner</span>
          <span>Acessar via QR Code</span>
        </button>
        <button class="w-full bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 font-medium py-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center justify-center gap-2 mt-2">
          <span class="material-symbols-outlined text-slate-500" style="font-size: 20px">info</span>
          <span class="text-sm">Primeiro acesso? Clique aqui</span>
        </button>
      </div>
    </div>

    <!-- Footer -->
    <div class="mt-auto py-6 px-6 text-center">
      <p class="text-slate-400 text-xs font-medium uppercase tracking-tighter">
        © 2026 INFRALYZE SYSTEMS
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login } = useAuth()

const form = ref({
  email: '',
  password: ''
})

const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) {
    error.value = 'Por favor, preencha todos os campos'
    return
  }

  loading.value = true
  error.value = ''

  try {
    // Converter email para username (ou ajustar conforme sua API)
    const username = form.value.email.split('@')[0]
    
    const response = await login(username, form.value.password)
    
    if (response) {
      router.push('/dashboard')
    }
  } catch (err: any) {
    error.value = err.message || 'Erro ao fazer login'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-input {
  transition: all 0.3s ease;
}
</style>
