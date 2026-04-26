export type TenantOption = {
  id: string
  nome: string
  plano: 'free' | 'basico' | 'pro' | 'premium'
}

let activeTenantId: string | null = null
let availableTenants: TenantOption[] = []

export function setAvailableTenants(tenants: TenantOption[]) {
  availableTenants = tenants || []
}

export function getAvailableTenants(): TenantOption[] {
  return availableTenants
}

export function setActiveTenantId(tenantId: string | null) {
  activeTenantId = tenantId
}

export function getActiveTenantId(): string | null {
  return activeTenantId
}

export function getActiveTenant(): TenantOption | null {
  return availableTenants.find((tenant) => tenant.id === activeTenantId) || null
}