<template>
  <n-card title="设备管理">
    <n-space style="margin-bottom:12px;">
      <n-input v-model:value="search" placeholder="搜索设备名/IP" clearable style="width:240px" />
      <n-select v-model:value="typeFilter" :options="typeOptions" placeholder="设备类型" clearable style="width:150px" />
      <n-button type="primary" @click="openCreate">+ 添加设备</n-button>
      <n-button @click="loadDevices">刷新</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="filteredDevices" :pagination="pagination" :bordered="false" :loading="loading" />

    <!-- Create/Edit Device Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" :title="editingId ? '编辑设备' : '添加设备'" style="width:560px" :bordered="false">
      <n-form :model="form" label-placement="left" label-width="100">
        <n-form-item label="设备名称" required>
          <n-input v-model:value="form.name" placeholder="例如: PB-1" />
        </n-form-item>
        <n-form-item label="IP 地址" required>
          <n-input v-model:value="form.ip_address" placeholder="管理 IP" />
        </n-form-item>
        <n-form-item label="设备类型" required>
          <n-select v-model:value="form.device_type" :options="typeOptions" />
        </n-form-item>
        <n-form-item label="角色" required>
          <n-select v-model:value="form.role" :options="roleOptions" />
        </n-form-item>
        <n-form-item label="地市">
          <n-input v-model:value="form.city" placeholder="所在地市" />
        </n-form-item>
        <n-form-item label="凭据">
          <n-select v-model:value="form.credential_id" :options="credentialOptions" placeholder="选择 SSH 凭据" clearable filterable />
        </n-form-item>
        <n-form-item label="Enable密码">
          <n-input v-model:value="form.enable_password" type="password" placeholder="特权模式密码" show-password-on="click" />
        </n-form-item>
        <n-form-item label="SNMP Community">
          <n-input v-model:value="form.snmp_community" placeholder="SNMP 读团体字" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="form.description" type="textarea" rows="2" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="saveDevice" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { NButton, NTag, NSpace, useMessage } from 'naive-ui'
import { deviceApi, credentialApi } from '../api'

const message = useMessage()
const search = ref('')
const typeFilter = ref(null)
const allDevices = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const credentialOptions = ref([])

const form = ref({
  name: '',
  ip_address: '',
  device_type: null,
  role: null,
  city: '',
  credential_id: null,
  enable_password: '',
  snmp_community: '',
  description: '',
})

const typeOptions = [
  { label: 'BB 集团骨干', value: 'BB' },
  { label: 'PB 省网核心', value: 'PB' },
  { label: 'MB 城域核心', value: 'MB' },
  { label: 'PC 自有业务', value: 'PC' },
  { label: 'BRAS', value: 'BRAS' },
  { label: 'SR', value: 'SR' },
  { label: 'SW 交换机', value: 'SW' },
  { label: 'PE', value: 'PE' },
  { label: 'RR 路由反射', value: 'RR' },
  { label: 'FW 防火墙', value: 'FW' },
]

const roleOptions = [
  { label: '核心', value: 'core' },
  { label: '汇聚', value: 'aggregation' },
  { label: '接入', value: 'access' },
  { label: '业务接入', value: 'service-access-control' },
  { label: '路由反射', value: 'route-reflector' },
  { label: '城域汇聚', value: 'metro-convergence' },
  { label: '宽带', value: 'broadband' },
  { label: '客户边缘', value: 'customer-edge' },
  { label: '管理', value: 'management' },
]

onMounted(() => {
  loadDevices()
  loadCredentials()
})

async function loadDevices() {
  loading.value = true
  try {
    const { data } = await deviceApi.list({ limit: 200 })
    allDevices.value = data.items || []
  } catch {
    message.error('加载设备列表失败')
  } finally {
    loading.value = false
  }
}

async function loadCredentials() {
  try {
    const { data } = await credentialApi.list()
    credentialOptions.value = (data || []).map((c) => ({
      label: `${c.name} (${c.username})`,
      value: c.id,
    }))
  } catch {
    // non-critical
  }
}

const filteredDevices = computed(() => {
  let list = allDevices.value
  if (search.value) {
    const s = search.value.toLowerCase()
    list = list.filter(d => d.name?.toLowerCase().includes(s) || d.ip_address?.includes(s))
  }
  if (typeFilter.value) list = list.filter(d => d.device_type === typeFilter.value)
  return list
})

const pagination = { pageSize: 10 }

function openEdit(device) {
  editingId.value = device.id
  form.value = {
    name: device.name,
    ip_address: device.ip_address,
    device_type: device.device_type,
    role: device.role,
    city: device.city || '',
    credential_id: device.credential_id,
    enable_password: '',
    snmp_community: '',
    description: device.description || '',
  }
  showCreateModal.value = true
}

function openCreate() {
  editingId.value = null
  form.value = {
    name: '', ip_address: '', device_type: null, role: null,
    city: '', credential_id: null, enable_password: '',
    snmp_community: '', description: '',
  }
  showCreateModal.value = true
}

async function saveDevice() {
  saving.value = true
  try {
    const payload = { ...form.value }
    // Strip empty optional fields
    if (!payload.enable_password) delete payload.enable_password
    if (!payload.snmp_community) delete payload.snmp_community
    if (!payload.description) delete payload.description
    if (!payload.city) delete payload.city
    if (!payload.credential_id) payload.credential_id = null

    if (editingId.value) {
      await deviceApi.update(editingId.value, payload)
      message.success('设备已更新')
    } else {
      await deviceApi.create(payload)
      message.success('设备已创建')
    }
    showCreateModal.value = false
    loadDevices()
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeDevice(device) {
  try {
    await deviceApi.delete(device.id)
    message.success('设备已删除')
    loadDevices()
  } catch (e) {
    message.error(e.response?.data?.detail || '删除失败')
  }
}

const columns = [
  { title: '名称', key: 'name', width: 90, sorter: (a, b) => (a.name || '').localeCompare(b.name || '') },
  { title: 'IP', key: 'ip_address', width: 130 },
  { title: '类型', key: 'device_type', width: 80 },
  { title: '角色', key: 'role', width: 100 },
  { title: '地市', key: 'city', width: 70 },
  {
    title: '状态', key: 'status', width: 70,
    render: (r) => h(NTag, { type: r.status === 'online' ? 'success' : 'error', size: 'small' }, r.status === 'online' ? '在线' : '离线'),
  },
  {
    title: '操作', width: 120,
    render: (r) => h(NSpace, null, [
      h(NButton, { size: 'tiny', quaternary: true, onClick: () => openEdit(r) }, '编辑'),
      h(NButton, { size: 'tiny', quaternary: true, type: 'error', onClick: () => removeDevice(r) }, '删除'),
    ]),
  },
]
</script>
