<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import api from "./services/api";
import { uploadFoto } from "./api/profile";
import axios from 'axios';
import { 
  LayoutDashboard, 
  Users, 
  Calendar, 
  Wallet, 
  Plus, 
  ArrowLeft, 
  Bell, 
  CheckCircle,
  Package as PackageIcon,
  Settings,
  Search,
  ChevronRight,
  Info,
  Save,
  QrCode,
  Download,
  Filter
} from 'lucide-vue-next';

type Screen =
  | 'login'
  | 'register'
  | 'dashboard'
  | 'client-form'
  | 'clients'
  | 'new-client'
  | 'edit-client'
  | 'client-detail'
  | 'new-package'
  | 'finance'
  | 'settings'
  | 'attendance'
  | 'attendance-new'


// estado do formulário de cadastro
const registerForm = ref({
  // dados do profissional/tenant
  nome_fantasia: '',
  slug: '',
  email: '',
  telefone: '',
  documento: '',
  // dados de acesso
  password: '',
  confirm_password: '',
  // nome de exibição do profissional
  nome_exibicao: '',
})
const registerLoading = ref(false)
const registerError = ref('')
const registerSuccess = ref(false)

async function handleRegister() {
  registerError.value = ''

  if (!registerForm.value.nome_fantasia ||
      !registerForm.value.email ||
      !registerForm.value.password) {
    registerError.value = 'Preencha todos os campos obrigatórios.'
    return
  }

  if (registerForm.value.password !== registerForm.value.confirm_password) {
    registerError.value = 'As senhas não coincidem.'
    return
  }

  try {
    registerLoading.value = true
  // usa axios puro para não enviar token JWT no header
    const { data } = await axios.post(
      'http://127.0.0.1:8000/api/v1/registro-profissional/',
      {
      nome_fantasia: registerForm.value.nome_fantasia,
      nome_exibicao: registerForm.value.nome_exibicao,
      email: registerForm.value.email,
      password: registerForm.value.password,
      telefone: registerForm.value.telefone,
      documento: registerForm.value.documento,
    })

    // salva tokens e já entra no dashboard
    localStorage.setItem('accessToken', data.access)
    localStorage.setItem('refreshToken', data.refresh)

    registerSuccess.value = true

    setTimeout(() => {
      registerSuccess.value = false
      currentScreen.value = 'dashboard'
      loadPackages()
    }, 1500)

  } catch (e: any) {
    const errData = e?.response?.data
    registerError.value = errData?.error
      || errData?.detail
      || errData?.email?.[0]
      || 'Erro ao realizar cadastro.'
  } finally {
    registerLoading.value = false
  }
}

// AUTH STATE
const currentScreen = ref<Screen>('login')
const tenantId = ref('prof_ricardo'); // ou null se não tiver tenant fixo ainda
const isAuthenticated = ref(false);
const loginForm = ref({ email: '', password: '' });
const showPassword = ref(false);
const loginLoading = ref(false);
const loginError = ref('');

// API CONFIG
const API_URL = 'http://127.0.0.1:8000/api/v1';


// LOGIN HANDLER
const handleLogin = async () => {
  if (!loginForm.value.email || !loginForm.value.password) {
    loginError.value = 'Por favor, preencha todos os campos';
    return;
  }

  loginLoading.value = true;
  loginError.value = '';

  try {
    const response = await axios.post('http://127.0.0.1:8000/api/token/', {
      email: loginForm.value.email,          // envia "admin@attend.com"
      password: loginForm.value.password,
    });

  // se chegou aqui, login OK: guarda tokens e troca de tela
    const { access, refresh } = response.data;
  // exemplo:
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
    await loadPerfil();
    currentScreen.value = 'dashboard';
    loginError.value = '';
  } catch (error: any) {
    loginError.value = 'Erro ao fazer login. Verifique suas credenciais.';
  } finally {
    loginLoading.value = false;
  }
};


const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const errorMessage = ref('')

// Perfil do usuário logado
const perfilUsuario = ref({
  nome: 'Profissional',
  email: '',
  foto: null as string | null,
  tipo_usuario: '',
})

function openFilePicker() {
  console.log("clicou na foto")
  fileInput.value?.click()
}

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  errorMessage.value = ''

  try {
      isUploading.value = true
      const response = await uploadFoto(file)
      perfilUsuario.value.foto = response.foto_url || response.foto || null
    } catch (error: any) {
      console.error("Erro no upload:", error)
      console.error("Status:", error?.response?.status)
      console.error("Data:", error?.response?.data)

    errorMessage.value =
      error?.response?.data?.detail ||
      error?.response?.data?.foto?.[0] ||
      "Não foi possível enviar a foto."
  } finally {
    isUploading.value = false
    input.value = ""
  }
}

async function loadPerfil() {
  try {
    const { data } = await api.get('/me/')
    perfilUsuario.value = {
      nome: data.nome ?? 'Profissional',
      email: data.email ?? '',
      foto: data.foto ?? data.foto_url ?? null,
      tipo_usuario: data.tipo_usuario ?? '',
    }
  } catch (e) {
    console.error('Erro ao carregar perfil:', e)
  }
}

// VERIFICAR SE JÁ ESTÁ LOGADO
onMounted(() => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    isAuthenticated.value = true
    currentScreen.value = 'dashboard'
    loadPerfil()
    loadDashboard()
  }
})

// Dashboard
const sessoesHoje = ref<any[]>([])
const loadingDashboard = ref(false)

async function loadDashboard() {
  try {
    loadingDashboard.value = true
    // sessões de hoje
    const hoje = new Date().toISOString().slice(0, 10)
    const { data } = await api.get('/sessoes/', {
      params: { data_inicio: hoje }
    })
    sessoesHoje.value = data
    // clientes já carregados pelo loadclients()
    if (selectedClient.value?.id !== undefined) {
      await loadClientDetail(selectedClient.value.id)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loadingDashboard.value = false
  }
}

// nome do profissional logado
const nomeProfissional = computed(() => {
  const token = localStorage.getItem('accessToken')
  if (!token) return 'Profissional'
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.first_name || payload.email?.split('@')[0] || 'Profissional'
  } catch {
    return 'Profissional'
  }
})



// Conceito de cliente na UI, mas vindo de /clientes/
const clientes = computed(() => clients.value) // apenas um alias

// Busca de clientes
const searchTerm = ref('')
const filteredclients = computed(() => {
  if (!searchTerm.value) return clients.value
  const term = searchTerm.value.toLowerCase()
  return clients.value.filter(client => 
    client.nome?.toLowerCase().includes(term) ||
    client.email?.toLowerCase().includes(term)
  )
})

// =========================
// Estado de navegação
// =========================
// currentScreen já foi declarado acima

// telas possíveis:
// 'dashboard'
// 'clients'
// 'client-detail'
// 'new-client'
// 'new-package'
// 'attendance'

// =========================
// Montagem Inicial
// =========================

onMounted(() => {
  fetchClients();
  fetchPackages();
});

// =========================
// Estado principal
// =========================


interface Cliente {
  id: string | number
  nome: string
  responsavel?: string
  cpf?: string
  data_nascimento?: string | null
  telefone?: string
  email?: string
  observacoes?: string
  tenant?: string
  user?: string | null
  created_at?: string
}

interface ClienteFormData {
  nome: string
  responsavel: string
  cpf: string
  data_nascimento: string
  telefone: string
  email: string
  observacoes: string
}

const clients = ref<Cliente[]>([])
const selectedClient = ref<Cliente | null>(null)
const isSavingClient = ref(false)
const isDeletingClient = ref(false)


// =========================
// Criar cliente
// =========================
const newClient = ref<ClienteFormData>({
  nome: '',
  responsavel: '',
  cpf: '',
  data_nascimento: '',
  telefone: '',
  email: '',
  observacoes: ''
})



const fetchClients = async (): Promise<void> => {
  try {
    const res = await api.get('/clientes/')
    clients.value = res.data
  } catch (error: any) {
    console.error('Erro ao buscar clientes:', error)
    console.error(error?.response?.data)

    alert(
      error?.response?.data?.detail ||
      'Erro ao carregar clientes'
    )
  }
}

// =========================
// Carregar Detalhes cliente
// =========================
async function loadClientDetail(clientId: string | number): Promise<void> {
  try {
    const response = await api.get<Cliente>(`/clientes/${clientId}/`)
    console.log('detalhe do cliente:', response.data)
    selectedClient.value = response.data
  } catch (error: any) {
    console.error(error)
    console.error(error?.response?.data)
    alert(
      error?.response?.data?.detail ||
      'Erro ao carregar informações do cliente'
    )
  }
}

// =========================
// Abrir Detalhes cliente
// =========================
async function openClientDetail(client: Cliente): Promise<void> {
  await loadClientDetail(client.id)
  currentScreen.value = 'client-detail'

  if (selectedClient.value?.id) {
    await loadClientPackages(selectedClient.value.id)
  }
}

// =========================
// Abrir Cadastro do cliente para edição
// =========================
function openNewClient(): void {
  editingClientId.value = null

  newClient.value = {
    nome: '',
    responsavel: '',
    cpf: '',
    data_nascimento: '',
    telefone: '',
    email: '',
    observacoes: ''
  }

  currentScreen.value = 'client-form'
}

// =========================
// Editar Cadasdro do cliente
// =========================

const editClientForm = ref<ClienteFormData>({
  nome: '',
  cpf: '',
  data_nascimento: '',
  responsavel: '',
  email: '',
  telefone: '',
  observacoes: ''
})
const editingClientId = ref<string | number | null>(null)

function goToEditClient(client: Cliente) {
  editingClientId.value = client.id

  editClientForm.value = {
    nome: client.nome ?? '',
    cpf: client.cpf ?? '',
    data_nascimento: client.data_nascimento ?? '',
    responsavel: client.responsavel ?? '',
    email: client.email ?? '',
    telefone: client.telefone ?? '',
    observacoes: client.observacoes ?? ''
  }

  currentScreen.value = 'edit-client'
}

// =========================
// Salvar Edição do Cliente
// =========================
function saveEditedClient() {
  const id = editingClientId.value
  if (id === null) return

  const index = clients.value.findIndex(client => client.id === id)
  if (index === -1) return

  const updatedClient: Cliente = {
    ...clients.value[index],
    ...editClientForm.value
  }

  clients.value.splice(index, 1, updatedClient)
  selectedClient.value = updatedClient
  currentScreen.value = 'client-detail'
  editingClientId.value = null
}

// =========================
// Salvar cliente
// =========================
async function saveClient(): Promise<void> {
  try {
    isSavingClient.value = true

    console.log('payload novo cliente:', newClient.value)
    console.log('payload json:', JSON.stringify(newClient.value, null, 2))

    let response

    if (editingClientId.value) {
      response = await api.put(`/clientes/${editingClientId.value}/`, newClient.value)
    } else {
      response = await api.post('/clientes/', newClient.value)
    }

    console.log('cliente salvo:', response.data)

    await fetchClients()
    await openClientDetail(response.data)
  } catch (error: any) {
    console.error(error)
    console.error(error?.response?.data)

    const data = error?.response?.data
    const message =
      data?.detail ||
      (typeof data === 'object'
        ? Object.entries(data)
            .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
            .join('\n')
        : null) ||
      'Erro ao salvar cliente'

    alert(message)
  } finally {
    isSavingClient.value = false
  }
}

// =========================
// Deletar Cadastro do Cliente
// =========================

async function deleteClient(clientId: string | number): Promise<void> {
  const confirmed = window.confirm('Tem certeza que deseja excluir este cliente?')
  if (!confirmed) return

  try {
    isDeletingClient.value = true

    await api.delete(`/clientes/${clientId}/`)
    await fetchClients()

    if (selectedClient.value?.id === clientId) {
      selectedClient.value = null
      currentScreen.value = 'clients'
    }
  } catch (error: any) {
    console.error(error)
    console.error(error?.response?.data)
    alert(
      error?.response?.data?.detail ||
      'Erro ao excluir cliente'
    )
  } finally {
    isDeletingClient.value = false
  }
}

// =========================
// Cancelar Formulário de Cliente
// =========================
function cancelClientForm(): void {
  editingClientId.value = null
  currentScreen.value = 'clients'
}






const clientPackages = ref<any[]>([])
const packages = ref<any[]>([])
const loadingPackages = ref(false)
const packageError = ref('')

// =========================
// Carregamentos
// =========================



async function loadClientPackages(clientId: string | number) {
  try {
    loadingPackages.value = true
    packageError.value = ''

    const { data } = await api.get('/pacotes-sessoes/', {
      params: { cliente: clientId },
    })

    clientPackages.value = data
  } catch (error) {
    console.error('Erro ao carregar pacotes:', error)
    packageError.value = 'Erro ao carregar pacotes do cliente'
  } finally {
    loadingPackages.value = false
  }
}

// =========================
// Ações de navegação
// =========================
function goToScreen(screen: Screen) {
  currentScreen.value = screen
}




function openNewPackage(client: any) {
  selectedClient.value = client
  currentScreen.value = 'new-package'
}

function openAttendance(pkg: any) {
  selectedPackage.value = pkg
  newAttendance.value = {
    pacote: pkg.id,
    cliente: pkg.cliente,   // já vem do pacote
    data: new Date().toISOString().slice(0, 10),
    hora_inicio: '',
    hora_fim: '',
    status: 'agendada',
    observacoes: '',
  }
  currentScreen.value = 'attendance-new'
}




// =========================
// Watch de telas
// =========================
watch(currentScreen, async (screen) => {
  if (screen === 'dashboard') {
    await loadDashboard()
  }

  if (screen === 'clients') {
    await fetchClients()
  }

  if (screen === 'new-package') {
    if (selectedClient.value?.id) {
      await loadClientDetail(selectedClient.value.id)
    }
  }

  if (screen === 'attendance' && selectedClient.value) {
    await loadClientSessoes(selectedClient.value.id)
  }
})

function abrirNovoPacote(clienteId: string) {
  newPackage.value = {
    id: null,
    cliente: clienteId,
    descricao: '',
    qtd_sessoes: 0,
    valor_por_sessao: 0,
    qtd_parcelas: 1,
    dia_pagamento: 5,
    data_inicio: new Date().toISOString().slice(0, 10),
    data_fim: '',
  }
  currentScreen.value = 'new-package'
}


const selectedPackage = ref<any | null>(null)
const newAttendance = ref({
  pacote: '',
  cliente: '',
  data: '',           // separamos data e hora para facilitar o input
  hora_inicio: '',
  hora_fim: '',
  status: 'agendada' as string,
  observacoes: '',
})

// Histórico de sessões
const clientSessoes = ref<any[]>([])
const loadingSessoes = ref(false)
const selectedPacoteFilter = ref<string>('') // filtra por pacote, vazio = todos

async function loadClientSessoes(clienteId: string, pacoteId?: string) {
  try {
    loadingSessoes.value = true
    const params: any = { cliente: clienteId }
    if (pacoteId) params.pacote = pacoteId
    const { data } = await api.get('/sessoes/', { params })
    clientSessoes.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loadingSessoes.value = false
  }
}

function openSessaoHistory(clienteId: string) {
  selectedPacoteFilter.value = ''
  loadClientSessoes(clienteId)
  currentScreen.value = 'attendance'
}

async function darBaixaSessao(sessaoId: string) {
  try {
    // Verificar se selectedClient.value não é null
    if (!selectedClient.value) {
      alert('Nenhum cliente selecionado')
      return
    }
    await api.post(`/sessoes/${sessaoId}/dar_baixa/`)

    // Converter id para string se necessário
    const clientId = String(selectedClient.value.id)
    const pacoteId = selectedPacoteFilter.value || undefined

    await loadClientSessoes(clientId, pacoteId)
    await loadClientPackages(clientId)
  } catch (e: any) {
    alert(e?.response?.data?.detail || 'Erro ao dar baixa na sessão.')
  }
}
  

// formata data/hora para exibição
function formatDateTime(iso: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function saveAttendance() {
  try {
    const payload = {
      pacote: newAttendance.value.pacote,
      cliente: newAttendance.value.cliente,
      data_hora_inicio: `${newAttendance.value.data}T${newAttendance.value.hora_inicio}:00`,
      data_hora_fim: `${newAttendance.value.data}T${newAttendance.value.hora_fim}:00`,
      status: newAttendance.value.status,
      observacoes: newAttendance.value.observacoes,
    }

    const { data } = await api.post('/sessoes/', payload)

    // se já foi registrada como realizada, dá baixa automática no pacote
    if (newAttendance.value.status === 'realizada') {
      await api.post(`/sessoes/${data.id}/dar_baixa/`)
    }

    if (selectedClient.value) {
      await loadClientPackages(selectedClient.value.id)
    } else {
      alert('Nenhum cliente selecionado')
      return
    }
    await loadClientPackages(selectedClient.value.id)
    currentScreen.value = 'client-detail'
  } catch (e: any) {
    console.error(e)
    alert('Erro ao registrar sessão.')
  }
}

interface NewPackage {
  id: string | null
  cliente: string  // não string | number
  descricao: string
  qtd_sessoes: number
  valor_por_sessao: number
  qtd_parcelas: number
  dia_pagamento: number
  data_inicio: string
  data_fim: string

  // outros campos...
} 

// formulário de novo pacote de sessões (PacoteSessoes)
const newPackage = ref<NewPackage>({
  id: null as string | null,
  cliente: '' as string,        // será preenchido com selectedClient.id
  descricao: '',
  qtd_sessoes: 0,
  valor_por_sessao: 0,
  qtd_parcelas: 1,
  dia_pagamento: 5,
  data_inicio: '',
  data_fim: '',
})

// valores calculados em tempo real
const valorTotal = computed(() => {
  const qtd = Number(newPackage.value.qtd_sessoes) || 0
  const valor = Number(newPackage.value.valor_por_sessao) || 0
  return qtd * valor
})

const valorParcela = computed(() => {
  const total = valorTotal.value
  const parcelas = Number(newPackage.value.qtd_parcelas) || 0
  return parcelas > 0 ? total / parcelas : 0
})

// carrega todos os pacotes do tenant logado
async function loadPackages() {
  try {
    loadingPackages.value = true
    packageError.value = ''
    const { data } = await api.get('/pacotes-sessoes/')
    packages.value = data
  } catch (e: any) {
    console.error(e)
    packageError.value = 'Erro ao carregar pacotes.'
  } finally {
    loadingPackages.value = false
  }
}

// salva novo pacote de sessões (PacoteSessoes)
async function savePackage() {
  try {
    packageError.value = ''

    if (!selectedClient.value) {
      packageError.value = 'Selecione um cliente.'
      return
    }

    // garante cliente e monta payload
    newPackage.value.cliente = selectedClient.value.id

    const payload = {
      cliente: newPackage.value.cliente,
      descricao: newPackage.value.descricao,
      qtd_sessoes: newPackage.value.qtd_sessoes,
      valor_por_sessao: newPackage.value.valor_por_sessao,
      qtd_parcelas: newPackage.value.qtd_parcelas,
      dia_pagamento: newPackage.value.dia_pagamento,
      data_inicio: newPackage.value.data_inicio,
      data_fim: newPackage.value.data_fim,
      // opcionais: backend recalcula, mas mandamos também
      valor_total: valorTotal.value,
      valor_parcela: valorParcela.value,
    }

    await api.post('/pacotes-sessoes/', payload) // ajuste a URL ao seu viewset
    await loadPackages()
    // atualiza pacotes do cliente atual (se você quiser ver o novo na tela de detalhes)
    await loadClientPackages(selectedClient.value.id)
    currentScreen.value = 'client-detail'
  } catch (e: any) {
    console.error(e)
    packageError.value = 'Erro ao salvar pacote de sessões.'
  }
}

// toda vez que entrar na tela de "novo pacote", podemos carregar dados auxiliares
watch(currentScreen, (screen) => {
  if (screen === 'new-package') {
    // se quiser, dá para chamar loadPackages() aqui (para mostrar pacotes existentes)
    // ou carregar lista de professores, etc.
  }
})

const contracts = ref<any[]>([]);


const fetchPackages = async () => {
  try {
    const res = await api.get('/pacotes-sessoes/')
    packages.value = res.data
  } catch (error) {
    console.error('Erro ao buscar pacotes:', error)
  }
}




function navigateTo(screen: Screen) {
  currentScreen.value = screen
}

// Form states



</script>

<template>
  <div class="bg-slate-50 min-h-screen font-sans text-slate-900">

    <!-- LOGIN SCREEN -->
    <div
      v-if="currentScreen === 'login'"
      class="bg-background-light dark:bg-background-dark font-display text-slate-900 dark:text-slate-100 min-h-screen flex flex-col"
    >
      <div class="max-w-md mx-auto w-full bg-white dark:bg-background-dark min-h-screen shadow-xl">
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
        </div>

        <!-- Hero Illustration -->
        <div class="container">
          <div
            class="w-full bg-center bg-no-repeat bg-cover flex flex-col justify-end overflow-hidden rounded-lg min-h-60 relative"
            style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuCWehol3Z-u3d96FuhcIhYxuGSnVIVXZIwjGJUt4M8tgC40Lw-7xt1qqrSdPN3tk655-CaK6HAskXBMIiFkhtIQ46g7pK6ebCXSSLv4ds6LyPoj0MQX4tXwxNRujzITVTEgeUeATEQ8fQvAopOqXbRl8jAghXbMpcugvfpXzh3ueCZXMKc1vtlR3CCBNgG5OWivWxIAxZ7Dr9ZYj5e3Eb4uD8WUk28B-nMIRGVufEF7JJLCSP-l5gpUdwW3CInephi7bQsccO5')"
          >
            <div class="absolute inset-0 bg-gradient-to-t from-blue-600/60 to-transparent"></div>
            <div class="relative p-6">
              <div class="bg-white dark:bg-slate-900 w-14 h-14 rounded-xl flex items-center justify-center shadow-lg mb-2">
                <span
                  class="material-symbols-outlined text-blue-600"
                  style="font-size: 32px; font-variation-settings: 'FILL' 1"
                >
                  menu_book
                </span>
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
            <p class="text-slate-900 dark:text-slate-100 text-sm font-semibold leading-normal pb-2">E-mail</p>
            <div class="relative">
              <span
                class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                style="font-size: 20px"
              >
                mail
              </span>
              <input
                v-model="loginForm.email"
                type="text"
                class="form-input flex w-full rounded-xl text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 h-14 pl-12 pr-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 placeholder:text-slate-400 font-normal transition-all"
                placeholder="seu@email.com"
              />
            </div>
          </label>

          <label class="flex flex-col w-full mt-2">
            <p class="text-slate-900 dark:text-slate-100 text-sm font-semibold leading-normal pb-2">Senha</p>
            <div class="relative">
              <span
                class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                style="font-size: 20px"
              >
                lock
              </span>
              <input
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input flex w-full rounded-xl text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 h-14 pl-12 pr-12 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 placeholder:text-slate-400 font-normal transition-all"
                placeholder="••••••••"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-600"
              >
                <span class="material-symbols-outlined" style="font-size: 20px">
                  {{ showPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </label>

          <div class="flex justify-end">
            <a href="#" class="text-blue-600 text-sm font-semibold hover:underline">Esqueceu a senha?</a>
          </div>

          <button
            @click="handleLogin"
            :disabled="loginLoading"
            class="w-full bg-blue-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-colors mt-4 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <span>{{ loginLoading ? 'Entrando...' : 'Entrar' }}</span>
            <span class="material-symbols-outlined" style="font-size: 20px">login</span>
          </button>

          <div v-if="loginError" class="text-red-500 text-sm text-center mt-2 bg-red-50 p-3 rounded-xl">
            {{ loginError }}
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
            <p class="text-slate-600 dark:text-slate-400 text-sm text-center mb-1">É cliente ou responsável?</p>
            <button
              class="w-full bg-blue-50 text-blue-600 font-bold py-4 rounded-xl border border-blue-100 hover:bg-blue-100 transition-colors flex items-center justify-center gap-2"
            >
              <span class="material-symbols-outlined" style="font-size: 20px">qr_code_scanner</span>
              <span>Acessar via QR Code</span>
            </button>
          </div>
        </div>

      <!-- Cadastro -->
      <div class="px-6 pb-2 text-center">
        <p class="text-slate-500 text-sm">
          Ainda não tem conta?
        </p>
        <button
          @click="currentScreen = 'register'"
          class="w-full mt-3 bg-white text-blue-600 font-bold py-4 rounded-xl border-2 border-blue-600 hover:bg-blue-50 transition-colors flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined" style="font-size: 20px">person_add</span>
          <span>Cadastrar como Profissional</span>
        </button>
      </div>

      <!-- Footer -->
      <div class="mt-auto py-6 px-6 text-center">
        <p class="text-slate-400 text-xs font-medium uppercase tracking-tighter">
          © 2026 INFRALYZE SYSTEMS
        </p>
      </div>
      </div>
    </div>

    <!-- REGISTER SCREEN / CADASTRO DO PROFISSIONAL -->
    <div
      v-else-if="currentScreen === 'register'"
      class="bg-white font-display text-slate-900 min-h-screen flex flex-col max-w-md mx-auto shadow-xl"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button @click="currentScreen = 'login'" class="p-2 rounded-full hover:bg-slate-50">
          <span class="material-symbols-outlined" style="font-size: 20px">arrow_back</span>
        </button>
        <h2 class="text-lg font-bold ml-2 flex-1">Criar conta</h2>
      </header>

      <!-- Sucesso -->
      <div
        v-if="registerSuccess"
        class="m-6 bg-green-50 border border-green-200 rounded-2xl p-6 text-center"
      >
        <span class="material-symbols-outlined text-green-500 text-5xl">check_circle</span>
        <p class="text-green-700 font-bold mt-2">Cadastro realizado com sucesso!</p>
        <p class="text-green-600 text-sm mt-1">Redirecionando para o login...</p>
      </div>

      <form
        v-else
        @submit.prevent="handleRegister"
        class="flex flex-col gap-4 px-6 py-6"
      >

        <!-- Plano info -->
        <div class="bg-blue-50 rounded-2xl p-4 flex items-start gap-3 mb-2">
          <span class="material-symbols-outlined text-blue-600 mt-0.5" style="font-size: 20px">
            info
          </span>
          <div>
            <p class="text-blue-700 font-bold text-sm">Plano Básico — Gratuito</p>
            <p class="text-blue-600 text-xs mt-0.5">
              Ideal para profissionais individuais. Até 10 clientes ativos.
            </p>
          </div>
        </div>

        <!-- Dados profissionais -->
        <p class="text-xs font-bold text-slate-400 uppercase tracking-widest mt-2">
          Dados profissionais
        </p>

        <label class="flex flex-col w-full">
          <p class="text-sm font-semibold pb-2">
            Nome / Nome da clínica / estúdio
            <span class="text-red-500">*</span>
          </p>
          <input
            v-model="registerForm.nome_fantasia"
            type="text"
            required
            placeholder="Ex: Dr. João Silva ou Estúdio Forma"
            class="form-input w-full rounded-xl border border-slate-200 h-14 px-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </label>

        <label class="flex flex-col w-full">
          <p class="text-sm font-semibold pb-2">
            Especialidade
          </p>
          <input
            v-model="registerForm.nome_exibicao"
            type="text"
            placeholder="Ex: Fisioterapeuta, Personal Trainer, Psicólogo..."
            class="form-input w-full rounded-xl border border-slate-200 h-14 px-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </label>

        <label class="flex flex-col w-full">
          <p class="text-sm font-semibold pb-2">Telefone</p>
          <input
            v-model="registerForm.telefone"
            type="tel"
            placeholder="(82) 99999-9999"
            class="form-input w-full rounded-xl border border-slate-200 h-14 px-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </label>

        <label class="flex flex-col w-full">
          <p class="text-sm font-semibold pb-2">CPF / CNPJ</p>
          <input
            v-model="registerForm.documento"
            type="text"
            placeholder="000.000.000-00"
            class="form-input w-full rounded-xl border border-slate-200 h-14 px-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </label>

        <!-- Dados de acesso -->
        <p class="text-xs font-bold text-slate-400 uppercase tracking-widest mt-4">
          Dados de acesso
        </p>

        <label class="flex flex-col w-full">
          <p class="text-sm font-semibold pb-2">
            E-mail <span class="text-red-500">*</span>
          </p>
          <input
            v-model="registerForm.email"
            type="email"
            required
            placeholder="seu@email.com"
            class="form-input w-full rounded-xl border border-slate-200 h-14 px-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </label>

        <label class="flex flex-col w-full">
          <p class="text-sm font-semibold pb-2">
            Senha <span class="text-red-500">*</span>
          </p>
          <input
            v-model="registerForm.password"
            type="password"
            required
            placeholder="Mínimo 8 caracteres"
            class="form-input w-full rounded-xl border border-slate-200 h-14 px-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </label>

        <label class="flex flex-col w-full">
          <p class="text-sm font-semibold pb-2">
            Confirmar senha <span class="text-red-500">*</span>
          </p>
          <input
            v-model="registerForm.confirm_password"
            type="password"
            required
            placeholder="Repita a senha"
            class="form-input w-full rounded-xl border border-slate-200 h-14 px-4 focus:ring-2 focus:ring-blue-600 focus:border-blue-600"
          />
        </label>

        <!-- Erro -->
        <div
          v-if="registerError"
          class="text-red-500 text-sm text-center bg-red-50 p-3 rounded-xl"
        >
          {{ registerError }}
        </div>

        <!-- Botão -->
        <button
          type="submit"
          :disabled="registerLoading"
          class="w-full bg-blue-600 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-colors mt-4 flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span>{{ registerLoading ? 'Cadastrando...' : 'Criar conta gratuita' }}</span>
          <span class="material-symbols-outlined" style="font-size: 20px">arrow_forward</span>
        </button>

        <p class="text-xs text-slate-400 text-center mt-2">
          Ao criar uma conta você concorda com nossos Termos de Uso e Política de Privacidade.
        </p>

      </form>
    </div>

    

    <!-- DASHBOARD SCREEN -->
    <div
      v-else-if="currentScreen === 'dashboard'"
      class="max-w-md mx-auto bg-white min-h-screen shadow-xl pb-24"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button
          type="button"
          class="size-10 rounded-full bg-amber-100 overflow-hidden border-2 border-orange-500 shrink-0 flex items-center justify-center text-orange-700 font-bold"
          @click="openFilePicker"
          :disabled="isUploading"
          aria-label="Alterar foto do perfil"
        >
          <img
            v-if="perfilUsuario.foto"
            :src="perfilUsuario.foto"
            alt="Foto do perfil"
            class="w-full h-full object-cover"
          />
          <span v-else>
            {{ perfilUsuario.nome?.slice(0, 2).toUpperCase() }}
          </span>
        </button>

        <input
          ref="fileInput"
          type="file"
          accept="image/png,image/jpeg,image/webp"
          class="hidden"
          @change="onFileSelected"
        />

        <div class="ml-3 flex-1 min-w-0">
          <p class="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
            Bem-vindo de volta
          </p>
          <h2 class="text-lg font-bold leading-tight truncate">
            Olá, {{ perfilUsuario.nome }}
          </h2>
        </div>

        <button class="relative p-2 rounded-xl bg-slate-50 text-slate-600">
          <Bell :size="20" />
        </button>
      </header>

      <p v-if="isUploading" class="px-4 pt-2 text-sm text-slate-500">
        Enviando foto...
      </p>

      <p v-if="errorMessage" class="px-4 pt-2 text-sm text-red-500">
        {{ errorMessage }}
      </p>

      <div class="p-4 space-y-5">

        <!-- Resumo rápido -->
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-orange-50 border border-orange-100 rounded-2xl p-4">
            <p class="text-orange-600 text-[10px] font-bold uppercase tracking-wider mb-1">
              Clientes Ativos
            </p>
            <p class="text-3xl font-bold text-orange-600">
              {{ clients.length }}
            </p>
          </div>
          <div class="bg-slate-50 border border-slate-100 rounded-2xl p-4">
            <p class="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">
              Sessões Hoje
            </p>
            <p class="text-3xl font-bold text-slate-700">
              {{ sessoesHoje.length }}
            </p>
          </div>
        </div>

        <!-- Ações rápidas -->
        <section>
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">
            Ações Rápidas
          </p>
          <div class="grid grid-cols-3 gap-3">

            <!-- Novo Cliente -->
            <button
              @click="currentScreen = 'new-client'"
              class="flex flex-col items-center gap-2 bg-slate-50 rounded-2xl p-4 hover:bg-orange-50 transition-colors"
            >
              <div class="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
                <Plus :size="20" class="text-orange-600" />
              </div>
              <span class="text-[10px] font-bold text-slate-600 text-center leading-tight">
                Novo Cliente
              </span>
            </button>

            <!-- Novo Pacote -->
            <button
              @click="currentScreen = 'new-package'"
              class="flex flex-col items-center gap-2 bg-slate-50 rounded-2xl p-4 hover:bg-orange-50 transition-colors"
            >
              <div class="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
                <PackageIcon :size="20" class="text-orange-600" />
              </div>
              <span class="text-[10px] font-bold text-slate-600 text-center leading-tight">
                Novo Pacote
              </span>
            </button>

            <!-- Agenda -->
            <button
              @click="currentScreen = 'attendance'"
              class="flex flex-col items-center gap-2 bg-slate-50 rounded-2xl p-4 hover:bg-orange-50 transition-colors"
            >
              <div class="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
                <Calendar :size="20" class="text-orange-600" />
              </div>
              <span class="text-[10px] font-bold text-slate-600 text-center leading-tight">
                Agenda
              </span>
            </button>

          </div>
        </section>

        <!-- Agenda de hoje -->
        <section>
          <div class="flex items-center justify-between mb-3">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Agenda de Hoje
            </p>
            <button
              @click="currentScreen = 'attendance'"
              class="text-xs font-bold text-orange-500"
            >
              Ver tudo
            </button>
          </div>

          <!-- Loading -->
          <p v-if="loadingDashboard" class="text-xs text-slate-400 text-center py-4">
            Carregando...
          </p>

          <!-- Sem sessões hoje -->
          <div
            v-else-if="sessoesHoje.length === 0"
            class="bg-slate-50 rounded-2xl p-6 text-center"
          >
            <Calendar :size="28" class="mx-auto text-slate-300 mb-2" />
            <p class="text-sm text-slate-400">Nenhuma sessão agendada para hoje.</p>
          </div>

          <!-- Lista de sessões do dia -->
          <div v-else class="space-y-2">
            <div
              v-for="sessao in sessoesHoje"
              :key="sessao.id"
              class="flex items-center gap-3 bg-slate-50 rounded-2xl p-3"
            >
              <div class="w-9 h-9 rounded-xl bg-orange-100 flex items-center justify-center shrink-0">
                <Users :size="16" class="text-orange-600" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-bold text-slate-700 truncate">
                  {{ sessao.cliente_nome }}
                </p>
                <p class="text-xs text-slate-400">
                  {{
                    new Date(sessao.data_hora_inicio).toLocaleDateString('pt-BR', {
                      weekday: 'long', day: '2-digit', month: '2-digit'
                    })
                  }}
                  ·
                  {{
                    new Date(sessao.data_hora_inicio).toLocaleTimeString('pt-BR', {
                      hour: '2-digit', minute: '2-digit'
                    })
                  }}
                  –
                  {{
                    new Date(sessao.data_hora_fim).toLocaleTimeString('pt-BR', {
                      hour: '2-digit', minute: '2-digit'
                    })
                  }}
                </p>
              </div>
              <span
                class="text-[10px] font-bold uppercase px-2 py-1 rounded-full shrink-0"
                :class="{
                  'bg-blue-100 text-blue-600':     sessao.status === 'agendada',
                  'bg-green-100 text-green-600':   sessao.status === 'realizada',
                  'bg-red-100 text-red-500':       sessao.status === 'cancelada',
                  'bg-yellow-100 text-yellow-600': sessao.status === 'remarcada',
                }"
              >
                {{ sessao.status }}
              </span>
            </div>
          </div>
        </section>

        <!-- Clientes recentes -->
        <section>
          <div class="flex items-center justify-between mb-3">
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              Clientes Recentes
            </p>
            <button
              @click="currentScreen = 'clients'"
              class="text-xs font-bold text-orange-500"
            >
              Ver todos
            </button>
          </div>

          <div
            v-if="clients.length === 0"
            class="bg-slate-50 rounded-2xl p-6 text-center"
          >
            <Users :size="28" class="mx-auto text-slate-300 mb-2" />
            <p class="text-sm text-slate-400">Nenhum cliente cadastrado ainda.</p>
            <button
              @click="currentScreen = 'new-client'"
              class="mt-3 text-xs font-bold text-orange-500"
            >
              Cadastrar primeiro cliente
            </button>
          </div>

          <div v-else class="space-y-2">
            <div
              v-for="client in clients.slice(0, 3)"
              :key="client.id"
              @click="openClientDetail(client)"
              class="flex items-center gap-3 bg-slate-50 rounded-2xl p-3 cursor-pointer hover:bg-orange-50 transition-colors"
            >
              <div class="w-9 h-9 rounded-xl bg-orange-100 flex items-center justify-center shrink-0">
                <Users :size="16" class="text-orange-600" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-bold text-slate-700 truncate">
                  {{ client.nome }}
                </p>
              </div>
              <ChevronRight :size="16" class="text-slate-300 shrink-0" />
            </div>
          </div>
        </section>

      </div>
    

      <!-- Bottom Navigation -->
    
      <nav class="fixed bottom-0 inset-x-0 mx-auto max-w-md bg-white border-t border-slate-100 px-6 py-4 flex justify-between items-center z-20"
      >
        <button @click="navigateTo('dashboard')" class="flex flex-col items-center gap-1 text-slate-400">
          <LayoutDashboard :size="24" />
          <span class="text-[10px] font-bold">Início</span>
        </button>
        <button @click="navigateTo('clients')" class="flex flex-col items-center gap-1 text-orange-600">
          <Users :size="24" />
          <span class="text-[10px] font-bold">Clientes</span>
        </button>
        <button @click="navigateTo('finance')" class="flex flex-col items-center gap-1 text-slate-400">
          <Wallet :size="24" />
          <span class="text-[10px] font-bold">Financeiro</span>
        </button>
        <button @click="navigateTo('settings')" class="flex flex-col items-center gap-1 text-slate-400">
          <Settings :size="24" />
          <span class="text-[10px] font-bold">Ajustes</span>
        </button>
      </nav>
    </div>
  
    

    <!-- client LIST SCREEN -->
    <div
      v-else-if="currentScreen === 'clients'"
      class="max-w-md mx-auto relative bg-white min-h-screen shadow-xl pb-24"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button @click="navigateTo('dashboard')" class="p-2 rounded-full hover:bg-slate-50">
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-bold ml-2 flex-1">Gestão de Clientes</h2>
        <button class="p-2 rounded-xl bg-slate-50 text-slate-600">
          <Filter :size="20" />
        </button>
      </header>

      <div class="p-4">
        <div class="relative mb-6">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" :size="18" />
          <input
            v-model="searchTerm"
            type="text"
            placeholder="Buscar cliente..."
            class="w-80 pl-10 pr-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
          />
        </div>

        <div class="flex justify-between items-center mb-4">
          <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Clientes Ativos</h3>
          <span class="text-[10px] font-bold bg-orange-50 text-orange-600 px-2 py-1 rounded-full">
            {{ clients.length }} TOTAL
          </span>
        </div>

        <div class="space-y-3">
          <div
            v-for="client in clients"
            :key="client.id"
            @click="openClientDetail(client)"
            class="cursor-pointer bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between"
          >
            <div class="flex items-center gap-4">
              <div class="size-14 rounded-full bg-slate-100 overflow-hidden border-2 border-white shadow-sm">
                <img :src="`https://picsum.photos/seed/client${client.id}/100/100`" alt="Avatar" />
              </div>
              <div class="flex flex-col min-w-0">
                <span class="block text-sm font-semibold text-slate-800">
                  {{ client.nome }}
                </span>
                <span class="block text-[11px] text-slate-500 mt-0.5">
                  {{ client.email || 'Sem e-mail' }}
                </span>
                <p class="text-[10px] text-slate-500 font-bold uppercase tracking-wider mt-1">
                  {{ client.observacoes || 'Sem observações' }}
                </p>
                <div class="w-24 h-1.5 bg-slate-100 rounded-full mt-2 overflow-hidden">
                  <div class="bg-orange-600 h-full w-4/5"></div>
                </div>
              </div>
            </div>
            <button
              class="flex items-center gap-1 text-[10px] font-bold text-slate-500 bg-slate-50 px-3 py-2 rounded-xl"
            >
              CONTRATO <ChevronRight :size="14" />
            </button>
          
        </div>
      </div>
    </div>

    <!-- FAB flutuante real -->
    <div
      v-if="currentScreen === 'clients'"
      class="fixed bottom-24 left-1/2 -translate-x-1/2 w-full max-w-md px-6 z-30 pointer-events-none"
    >
      
        <button
          @click="navigateTo('new-client')"
          class="pointer-events-auto absolute right-6 bottom-0 size-14 bg-orange-600 text-white rounded-full shadow-xl shadow-orange-200 flex items-center justify-center"
        >
          <Plus :size="28" />
        </button>
      
    </div>

      <nav
        class="fixed bottom-0 inset-x-0 mx-auto max-w-md bg-white border-t border-slate-100 px-6 py-4 flex justify-between items-center z-20"
      >
        <button @click="navigateTo('dashboard')" class="flex flex-col items-center gap-1 text-slate-400">
          <LayoutDashboard :size="24" />
          <span class="text-[10px] font-bold">Início</span>
        </button>
        <button @click="navigateTo('clients')" class="flex flex-col items-center gap-1 text-slate-600">
          <Users :size="24" />
          <span class="text-[10px] font-bold">Clientes</span>
        </button>
        <button @click="navigateTo('finance')" class="flex flex-col items-center gap-1 text-slate-400">
          <Wallet :size="24" />
          <span class="text-[10px] font-bold">Financeiro</span>
        </button>
        <button @click="navigateTo('settings')" class="flex flex-col items-center gap-1 text-slate-400">
          <Settings :size="24" />
          <span class="text-[10px] font-bold">Ajustes</span>
        </button>
      </nav>

    </div>


    <!-- NEW client SCREEN -->
    <div v-else-if="currentScreen === 'new-client'"
      class="max-w-md mx-auto bg-white min-h-screen shadow-xl"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button @click="navigateTo('clients')" class="p-2 rounded-full hover:bg-slate-50">
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-bold ml-2 flex-1">Cadastro de Cliente</h2>
        <button @click="navigateTo('clients')" class="text-xs font-bold text-slate-400">CANCELAR</button>
      </header>

      <form @submit.prevent="saveClient" class="p-4 space-y-6">
        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Users :size="18" />
            <h3 class="font-bold">Dados do Cliente</h3>
          </div>
          <div class="space-y-4">
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Nome Completo
              </span>
              <input
                v-model="newClient.nome"
                type="text"
                placeholder="Ex: João Silva"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                CPF
              </span>
              <input
                v-model="newClient.cpf"
                type="cpf"
                placeholder="Ex: 123.456.789-00"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
             <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Data de Nascimento
              </span>
              <input
                v-model="newClient.data_nascimento"
                type="date"
                placeholder="Ex: 123.456.789-00"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Responsável (Opcional)
              </span>
              <input
                v-model="newClient.responsavel"
                type="text"
                placeholder="Ex: Maria Silva"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
          </div>
        </section>

        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Bell :size="18" />
            <h3 class="font-bold">Informações de Contato</h3>
          </div>
          <div class="grid grid-cols-1 gap-4">
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Telefone / WhatsApp
              </span>
              <input
                v-model="newClient.telefone"
                type="tel"
                placeholder="(00) 00000-0000"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                E-mail
              </span>
              <input
                v-model="newClient.email"
                type="email"
                placeholder="email@exemplo.com"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Observações (Opcional)
              </span>
              <input
                v-model="newClient.observacoes"
                type="text"
                placeholder="Observações sobre o cliente..."
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
          </div>
        </section>
        <!-- Botão salvar Cliente -->
        <button @click="saveClient" :disabled="isSavingClient">
          {{ isSavingClient ? 'Salvando...' : editingClientId ? 'Salvar alterações' : 'Salvar cliente' }}
        </button>
        <button @click="cancelClientForm">Cancelar</button>
      </form>
    </div>

    <!-- EDITAR CLIENTE -->
    
      <div
          v-else-if="currentScreen === 'edit-client'"
          class="max-w-md mx-auto bg-white min-h-screen shadow-xl pb-24"
        >
          <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
            <button @click="currentScreen = 'client-detail'" class="p-2 rounded-full hover:bg-slate-50">
              <ArrowLeft :size="20" />
            </button>
            <h2 class="text-lg font-bold ml-2 flex-1">Editar Cliente</h2>
          </header>
        <form @submit.prevent="saveClient" class="p-4 space-y-6">
          <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Users :size="18" />
            <h3 class="font-bold">Dados do Cliente</h3>
          </div>
          <div class="space-y-4">
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Nome Completo
              </span>
              <input
                v-model="editClientForm.nome"
                type="text"
                placeholder="Ex: João Silva"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                CPF
              </span>
              <input
                v-model="editClientForm.cpf"
                type="cpf"
                placeholder="Ex: 123.456.789-00"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
             <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Data de Nascimento
              </span>
              <input
                v-model="editClientForm.data_nascimento"
                type="date"
                placeholder="Ex: 123.456.789-00"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Responsável (Opcional)
              </span>
              <input
                v-model="editClientForm.responsavel"
                type="text"
                placeholder="Ex: Maria Silva"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
          </div>
        </section>

        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Bell :size="18" />
            <h3 class="font-bold">Informações de Contato</h3>
          </div>
          <div class="grid grid-cols-1 gap-4">
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Telefone / WhatsApp
              </span>
              <input
                v-model="editClientForm.telefone"
                type="tel"
                placeholder="(00) 00000-0000"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                E-mail
              </span>
              <input
                v-model="editClientForm.email"
                type="email"
                placeholder="email@exemplo.com"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
            <label class="block">
              <span
                class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block"
              >
                Observações (Opcional)
              </span>
              <input
                v-model="editClientForm.observacoes"
                type="text"
                placeholder="Observações sobre o cliente..."
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
          </div>
        </section>
        <!-- Botão salvar Cliente -->
            <button
              type="button"
              @click="saveEditedClient"
              class="w-full bg-orange-500 text-white py-3 rounded-2xl font-bold"
            >
              Salvar alterações
            </button>
          </form>
    </div>
      

    <!-- NEW PACKAGE / NOVO PACOTE DE SESSÕES -->
    <div v-else-if="currentScreen === 'new-package'"
      class="max-w-md mx-auto bg-white min-h-screen shadow-xl"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button @click="navigateTo('dashboard')" class="p-2 rounded-full hover:bg-slate-50">
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-bold ml-2 flex-1">Novo Pacote de Sessões</h2>
        <button @click="navigateTo('dashboard')" class="text-xs font-bold text-slate-400">
          CANCELAR
        </button>
      </header>

      <form @submit.prevent="savePackage" class="p-4 space-y-6">

        <!-- Cliente -->
        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Users :size="18" />
            <h3 class="font-bold">Cliente</h3>
          </div>
          <div class="space-y-4">
            <label class="block">
              <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
                Cliente
              </span>
              <select
                v-model="selectedClient"
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              >
                <option disabled value="">Selecione o cliente</option>
                <option v-for="client in clients" 
                        :key="client.id" :value="client" 
                        @click="openClientDetail(client.id)"
                        class="cursor-pointer bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex items-center justify-between"
                >
                  {{ client.nome }}
                </option>
              </select>
            </label>
          </div>
        </section>

        <!-- Sessões e valores -->
        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <PackageIcon :size="18" />
            <h3 class="font-bold">Sessões e Valores</h3>
          </div>

          <!-- Quantidade de sessões -->
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Quantas sessões?
            </span>
            <input
              type="number"
              min="1"
              v-model.number="newPackage.qtd_sessoes"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            />
          </label>

          <!-- Valor por sessão -->
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Valor por sessão (R$)
            </span>
            <input
              type="number"
              min="0"
              step="0.01"
              v-model.number="newPackage.valor_por_sessao"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            />
          </label>

          <!-- Total do pacote (somente leitura) -->
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Total do pacote (R$)
            </span>
            <input
              type="text"
              :value="valorTotal.toFixed(2)"
              readonly
              class="w-full px-4 py-3 bg-slate-100 border-none rounded-2xl text-slate-700"
            />
          </label>
        </section>

        <!-- Parcelas e pagamento -->
        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Wallet :size="18" />
            <h3 class="font-bold">Pagamento</h3>
          </div>

          <!-- Quantidade de parcelas -->
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Quantidade de parcelas
            </span>
            <input
              type="number"
              min="1"
              v-model.number="newPackage.qtd_parcelas"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            />
          </label>

          <!-- Valor por parcela (somente leitura) -->
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Valor por parcela (R$)
            </span>
            <input
              type="text"
              :value="valorParcela.toFixed(2)"
              readonly
              class="w-full px-4 py-3 bg-slate-100 border-none rounded-2xl text-slate-700"
            />
          </label>

          <!-- Dia do pagamento -->
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Dia do pagamento
            </span>
            <select
              v-model.number="newPackage.dia_pagamento"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            >
              <option v-for="dia in 31" :key="dia" :value="dia">
                Dia {{ String(dia).padStart(2, '0') }}
              </option>
            </select>
          </label>
        </section>

        <!-- Período -->
        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Calendar :size="18" />
            <h3 class="font-bold">Período</h3>
          </div>

          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Data de início
            </span>
            <input
              type="date"
              v-model="newPackage.data_inicio"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            />
          </label>

          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Data de término
            </span>
            <input
              type="date"
              v-model="newPackage.data_fim"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            />
          </label>
        </section>

        <!-- Descrição -->
        <section class="space-y-2">
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Descrição / Observações
            </span>
            <textarea
              v-model="newPackage.descricao"
              rows="3"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            />
          </label>
        </section>

        <!-- Botão salvar -->
        <button
          type="submit"
          class="w-full py-3 mt-4 rounded-2xl bg-orange-500 text-white font-bold text-sm flex items-center justify-center gap-2"
        >
          <Save :size="18" />
          SALVAR PACOTE
        </button>
      </form>
    </div>

    <!-- CLIENT DETAIL / PERFIL DO CLIENTE -->
    <div v-else-if="currentScreen === 'client-detail' && selectedClient"
      class="max-w-md mx-auto bg-white min-h-screen shadow-xl pb-24"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button @click="currentScreen = 'clients'" class="p-2 rounded-full hover:bg-slate-50">
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-bold ml-2 flex-1">{{ selectedClient.nome }}</h2>
      </header>

      <main class="p-4 space-y-6">

        <!-- Dados básicos -->
        <section class="bg-slate-50 rounded-2xl p-4 space-y-1">
          <p class="text-xs text-slate-500 font-bold uppercase tracking-widest mb-2">
            Informações do Cliente
          </p>
          <p class="text-sm text-slate-700">
            CPF: {{ selectedClient.cpf || 'Não informado' }}
          </p>
          <p class="text-sm text-slate-700">
            Data de Nascimento: {{ selectedClient.data_nascimento || 'Não informado' }}
          </p>
          <p class="text-sm text-slate-700">
            Responsável: {{ selectedClient.responsavel || 'Não informado' }}
          </p>
          <p class="text-sm text-slate-700">
            E-mail: {{ selectedClient.email || 'Não informado' }}
          </p>
          <p class="text-sm text-slate-700">
            Telefone: {{ selectedClient.telefone || 'Não informado' }}
          </p>
          <p class="text-sm text-slate-700">
            Observações: {{ selectedClient.observacoes || '—' }}
          </p>

          <button @click="goToEditClient(selectedClient!)" 
                class="w-15 mt-2 py-2 rounded-xl bg-orange-500 text-white text-xs font-bold">Editar</button>
          <button @click="deleteClient(selectedClient!.id)" :disabled="isDeletingClient"
                  class="w-15 mt-2 py-2 rounded-xl bg-red-500 text-white text-xs font-bold" >
            {{ isDeletingClient ? 'Excluindo...' : 'Excluir' }}
          </button>
        </section>

        
        <!-- Pacotes de Sessões -->
        <section class="space-y-3">
          <div class="flex justify-between items-center">
            <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">
              Pacotes de Sessões
            </p>
            <button
              @click="abrirNovoPacote(selectedClient.id)"
              class="flex items-center gap-1 text-xs font-bold text-orange-500"
            >
              <Plus :size="14" />
              NOVO PACOTE
            </button>

            <button
              @click="openSessaoHistory(selectedClient.id)"
              class="flex items-center gap-1 text-xs font-bold text-slate-500"
            >
              <Calendar :size="14" />
              VER HISTÓRICO
            </button>
          </div>

          <!-- Loading -->
          <p v-if="loadingPackages" class="text-xs text-slate-400 text-center py-4">
            Carregando pacotes...
          </p>

          <!-- Erro -->
          <p v-else-if="packageError" class="text-xs text-red-500 text-center py-4">
            {{ packageError }}
          </p>

          <!-- Sem pacotes -->
          <div
            v-else-if="clientPackages.length === 0"
            class="bg-slate-50 rounded-2xl p-6 text-center"
          >
            <PackageIcon :size="32" class="mx-auto text-slate-300 mb-2" />
            <p class="text-sm text-slate-400">Nenhum pacote cadastrado.</p>
            <button
              @click="abrirNovoPacote(selectedClient.id)"
              class="mt-3 text-xs font-bold text-orange-500"
            >
              Adicionar primeiro pacote
            </button>
          </div>

          <!-- Lista de pacotes -->
          <div
            v-else
            v-for="pkg in clientPackages"
            :key="pkg.id"
            class="bg-slate-50 rounded-2xl p-4 space-y-2"
          >
            <!-- Descrição e status -->
            <div class="flex justify-between items-center">
              <h4 class="font-bold text-sm">
                {{ pkg.descricao || 'Pacote de Sessões' }}
              </h4>
              <span
                class="text-[10px] font-bold uppercase px-2 py-1 rounded-full"
                :class="{
                  'bg-green-100 text-green-600': pkg.status === 'ativo',
                  'bg-slate-200 text-slate-500': pkg.status === 'concluido',
                  'bg-red-100 text-red-500': pkg.status === 'cancelado',
                  'bg-yellow-100 text-yellow-600': pkg.status === 'vencido',
                }"
              >
                {{ pkg.status }}
              </span>
            </div>

            <!-- Sessões -->
            <p class="text-xs text-slate-500">
              Sessões: {{ pkg.qtd_sessoes_usadas }} / {{ pkg.qtd_sessoes }}
              &nbsp;·&nbsp;
              Restantes: {{ pkg.sessoes_restantes }}
            </p>

            <!-- Financeiro -->
            <p class="text-xs text-slate-500">
              Valor total: R$ {{ Number(pkg.valor_total).toFixed(2) }}
              &nbsp;·&nbsp;
              {{ pkg.qtd_parcelas }}x de R$ {{ Number(pkg.valor_parcela).toFixed(2) }}
              &nbsp;·&nbsp;
              Venc. dia {{ pkg.dia_pagamento }}
            </p>

            <!-- Período -->
            <p class="text-xs text-slate-500">
              Período: {{ pkg.data_inicio }} - {{ pkg.data_fim || 'Em aberto' }}
            </p>

            <!-- Botão registrar sessão -->
            <button
              @click="openAttendance(pkg)"
              class="w-full mt-2 py-2 rounded-xl bg-orange-500 text-white text-xs font-bold"
            >
              REGISTRAR SESSÃO
            </button>
          </div>
        </section>

      </main>
    </div>

    
    <!-- ATTENDANCE NEW / REGISTRAR SESSÃO -->
    <div v-else-if="currentScreen === 'attendance-new' && selectedPackage"
      class="max-w-md mx-auto bg-white min-h-screen shadow-xl"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button @click="currentScreen = 'client-detail'" class="p-2 rounded-full hover:bg-slate-50">
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-bold ml-2 flex-1">Registrar Sessão</h2>
        <button @click="currentScreen = 'client-detail'" class="text-xs font-bold text-slate-400">
          CANCELAR
        </button>
      </header>

      <form @submit.prevent="saveAttendance" class="p-4 space-y-6">

        <!-- Resumo do pacote -->
        <section class="bg-slate-50 rounded-2xl p-4 space-y-1">
          <p class="text-xs text-slate-500 font-bold uppercase tracking-widest mb-1">
            Pacote
          </p>
          <p class="text-sm font-bold text-slate-700">
            {{ selectedPackage.descricao || 'Pacote de Sessões' }}
          </p>
          <p class="text-xs text-slate-500">
            Sessões restantes: {{ selectedPackage.sessoes_restantes }}
          </p>
        </section>

        <!-- Data e horário -->
        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <Calendar :size="18" />
            <h3 class="font-bold">Data e Horário</h3>
          </div>

          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Data da sessão
            </span>
            <input
              type="date"
              v-model="newAttendance.data"
              required
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            >
          </label>

          <div class="grid grid-cols-2 gap-3">
            <label class="block">
              <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
                Hora início
              </span>
              <input
                type="time"
                v-model="newAttendance.hora_inicio"
                required
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>

            <label class="block">
              <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
                Hora fim
              </span>
              <input
                type="time"
                v-model="newAttendance.hora_fim"
                required
                class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
              />
            </label>
          </div>
        </section>

        <!-- Status -->
        <section class="space-y-4">
          <div class="flex items-center gap-2 text-orange-600">
            <CheckCircle :size="18" />
            <h3 class="font-bold">Status</h3>
          </div>

          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Status da sessão
            </span>
            <select
              v-model="newAttendance.status"
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            >
              <option value="agendada">Agendada</option>
              <option value="realizada">Realizada</option>
              <option value="cancelada">Cancelada</option>
              <option value="remarcada">Remarcada</option>
              <option value="solicitada_remarcacao">Solicitada Remarcação</option>
            </select>
          </label>
        </section>

        <!-- Observações -->
        <section class="space-y-2">
          <label class="block">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
              Observações
            </span>
            <textarea
              v-model="newAttendance.observacoes"
              rows="3"
              placeholder="Anotações sobre a sessão..."
              class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
            ></textarea>
          </label>
        </section>

        <!-- Botão salvar -->
        <button
          type="submit"
          class="w-full py-3 mt-4 rounded-2xl bg-orange-500 text-white font-bold text-sm flex items-center justify-center gap-2"
        >
          <Save :size="18" />
          REGISTRAR SESSÃO
        </button>

      </form>
    </div>

    <!-- ATTENDANCE / HISTÓRICO DE SESSÕES -->
    <div v-else-if="currentScreen === 'attendance' && selectedClient"
      class="max-w-md mx-auto bg-white min-h-screen shadow-xl pb-24"
    >
      <header class="flex items-center p-4 sticky top-0 bg-white z-10 border-b border-slate-100">
        <button @click="currentScreen = 'client-detail'" class="p-2 rounded-full hover:bg-slate-50">
          <ArrowLeft :size="20" />
        </button>
        <h2 class="text-lg font-bold ml-2 flex-1">
          Histórico de Sessões
        </h2>
      </header>

      <main class="p-4 space-y-4">

        <!-- Nome do cliente -->
        <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">
          {{ selectedClient.nome }}
        </p>

        <!-- Filtro por pacote -->
        <label class="block">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 block">
            Filtrar por pacote
          </span>
          <select
            v-model="selectedPacoteFilter"
            @change="loadClientSessoes(selectedClient.id, selectedPacoteFilter || undefined)"
            class="w-full px-4 py-3 bg-slate-50 border-none rounded-2xl focus:ring-2 focus:ring-orange-500"
          >
            <option value="">Todos os pacotes</option>
            <option
              v-for="pkg in clientPackages"
              :key="pkg.id"
              :value="pkg.id"
            >
              {{ pkg.descricao || 'Pacote de Sessões' }}
              ({{ pkg.qtd_sessoes_usadas }}/{{ pkg.qtd_sessoes }})
            </option>
          </select>
        </label>

        <!-- Loading -->
        <p v-if="loadingSessoes" class="text-xs text-slate-400 text-center py-8">
          Carregando sessões...
        </p>

        <!-- Sem sessões -->
        <div
          v-else-if="clientSessoes.length === 0"
          class="bg-slate-50 rounded-2xl p-8 text-center"
        >
          <Calendar :size="32" class="mx-auto text-slate-300 mb-2" />
          <p class="text-sm text-slate-400">Nenhuma sessão registrada.</p>
        </div>

        <!-- Lista de sessões -->
        <div
          v-else
          v-for="sessao in clientSessoes"
          :key="sessao.id"
          class="bg-slate-50 rounded-2xl p-4 space-y-2"
        >
          <!-- Data e status -->
          <div class="flex justify-between items-start">
            <div>
              <p class="text-sm font-bold text-slate-700">
                {{ formatDateTime(sessao.data_hora_inicio) }}
              </p>
              <p class="text-xs text-slate-400">
                até {{ formatDateTime(sessao.data_hora_fim) }}
              </p>
            </div>
            <span
              class="text-[10px] font-bold uppercase px-2 py-1 rounded-full"
              :class="{
                'bg-blue-100 text-blue-600':   sessao.status === 'agendada',
                'bg-green-100 text-green-600': sessao.status === 'realizada',
                'bg-red-100 text-red-500':     sessao.status === 'cancelada',
                'bg-yellow-100 text-yellow-600': sessao.status === 'remarcada',
                'bg-purple-100 text-purple-600': sessao.status === 'solicitada_remarcacao',
              }"
            >
              {{ sessao.status.replace('_', ' ') }}
            </span>
          </div>

          <!-- Pacote e profissional -->
          <p class="text-xs text-slate-500">
            Pacote: {{ sessao.pacote_descricao || '—' }}
            &nbsp;·&nbsp;
            Profissional: {{ sessao.profissional_nome }}
          </p>

          <!-- Observações -->
          <p v-if="sessao.observacoes" class="text-xs text-slate-500 italic">
            {{ sessao.observacoes }}
          </p>

          <!-- Motivo cancelamento -->
          <p v-if="sessao.motivo_cancelamento" class="text-xs text-red-400 italic">
            Motivo: {{ sessao.motivo_cancelamento }}
          </p>

          <!-- Ações -->
          <div class="flex gap-2 pt-1">
            <!-- Dar baixa: só para sessões agendadas -->
            <button
              v-if="sessao.status === 'agendada'"
              @click="darBaixaSessao(sessao.id)"
              class="flex-1 py-2 rounded-xl bg-green-500 text-white text-xs font-bold"
            >
              DAR BAIXA
            </button>

            <!-- Remarcar: só para agendadas -->
            <button
              v-if="sessao.status === 'agendada'"
              @click="openAttendance(clientPackages.find(p => p.id === sessao.pacote))"
              class="flex-1 py-2 rounded-xl bg-orange-100 text-orange-600 text-xs font-bold"
            >
              REMARCAR
            </button>
          </div>
        </div>

      </main>
    </div>
    

    <!-- DEFAULT / FALLBACK -->
    <div v-else class="flex items-center justify-center min-h-screen">
      <div
        class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-600"
      ></div>
    </div>
  </div>
  
  
</template>




<style>
@import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap');

body {
  font-family: 'Public Sans', sans-serif;
}

/* Custom scrollbar for better mobile feel */
::-webkit-scrollbar {
  width: 0px;
}
</style>
