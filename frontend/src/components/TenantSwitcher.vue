<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import api from '@/services/api.js'
import {
  getAvailableTenants,
  getActiveTenant,
  setActiveTenantId,
  setAvailableTenants
} from "./services/tenantSession.ts";

type TenantOption = {
  id: string
  nome: string
  plano: 'free' | 'basico' | 'pro' | 'premium'
}

const tenants = computed<TenantOption[]>(() => getAvailableTenants())
const activeTenant = computed(() => getActiveTenant())
const selectedTenantId = ref('')

async function loadTenants() {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const response = await api.get('/me/')
    const receivedTenants = response.data?.tenants || []

    setAvailableTenants(receivedTenants)

    if (receivedTenants.length === 1) {
      selectedTenantId.value = receivedTenants[0].id
      setActiveTenantId(receivedTenants[0].id)
      return
    }

    if (receivedTenants.length > 1) {
      const current = activeTenant.value?.id || receivedTenants[0].id
      selectedTenantId.value = current
      setActiveTenantId(current)
    }
  } catch (error: any) {
    console.error('Erro ao carregar tenants:', error)
  }
}

function changeTenant() {
  if (!selectedTenantId.value) return
  setActiveTenantId(selectedTenantId.value)
  window.location.reload()
}

onMounted(() => {
  loadTenants()
})
</script>

<template>
  <div v-if="tenants.length > 1" class="tenant-switcher">
    <label for="tenantSelect" class="tenant-switcher__label">
      Tenant
    </label>

    <select
      id="tenantSelect"
      v-model="selectedTenantId"
      @change="changeTenant"
      class="tenant-switcher__select"
    >
      <option
        v-for="tenant in tenants"
        :key="tenant.id"
        :value="tenant.id"
      >
        {{ tenant.nome }} - {{ tenant.plano }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.tenant-switcher {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tenant-switcher__label {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.tenant-switcher__select {
  min-width: 220px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid #cbd5e1;
  padding: 0 12px;
  background: #fff;
  color: #0f172a;
  font-size: 14px;
}
</style>