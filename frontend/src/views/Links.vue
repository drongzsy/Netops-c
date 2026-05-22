<template>
  <n-card title="链路管理">
    <n-space style="margin-bottom:12px">
      <n-button type="primary" @click="showCreateModal = true">+ 新增链路</n-button>
      <n-button @click="loadLinks">刷新</n-button>
    </n-space>
    <n-data-table :columns="columns" :data="links" :bordered="false" :loading="loading" :pagination="{ pageSize: 15 }" />

    <n-modal v-model:show="showCreateModal" preset="card" title="新增链路" style="width:560px" :bordered="false">
      <n-form :model="form" label-placement="left" label-width="100">
        <n-form-item label="链路名称" required>
          <n-input v-model:value="form.name" placeholder="例如: PB-1_to_PB-2" />
        </n-form-item>
        <n-form-item label="设备 A" required>
          <n-select v-model:value="form.device_a_id" :options="deviceOptions" filterable placeholder="选择设备" />
        </n-form-item>
        <n-form-item label="接口 A" required>
          <n-input v-model:value="form.interface_a" placeholder="GE0/0/1" />
        </n-form-item>
        <n-form-item label="设备 Z" required>
          <n-select v-model:value="form.device_z_id" :options="deviceOptions" filterable placeholder="选择设备" />
        </n-form-item>
        <n-form-item label="接口 Z" required>
          <n-input v-model:value="form.interface_z" placeholder="GE0/0/1" />
        </n-form-item>
        <n-form-item label="带宽">
          <n-select v-model:value="form.bandwidth" :options="bwOptions" />
        </n-form-item>
        <n-form-item label="链路类型">
          <n-select v-model:value="form.link_type" :options="linkTypeOptions" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="saveLink" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NButton, NTag, NSpace, useMessage } from 'naive-ui'
import { api, deviceApi } from '../api'

const message = useMessage()
const loading = ref(false)
const saving = ref(false)
const links = ref([])
const deviceOptions = ref([])
const showCreateModal = ref(false)

const form = ref({
  name: '', device_a_id: null, interface_a: '', device_z_id: null, interface_z: '',
  bandwidth: '10GE', link_type: 'trunk',
})

const bwOptions = [
  { label: '1GE', value: '1GE' }, { label: '10GE', value: '10GE' },
  { label: '25GE', value: '25GE' }, { label: '40GE', value: '40GE' },
  { label: '100GE', value: '100GE' },
]

const linkTypeOptions = [
  { label: 'Trunk', value: 'trunk' }, { label: 'Access', value: 'access' }, { label: 'Routed', value: 'routed' },
]

onMounted(async () => {
  await loadDevices()
  await loadLinks()
})

async function loadDevices() {
  try {
    const { data } = await deviceApi.list({ limit: 100 })
    deviceOptions.value = (data.items || []).map(d => ({ label: `${d.name} (${d.ip_address})`, value: d.id }))
  } catch { /* ignore */ }
}

async function loadLinks() {
  loading.value = true
  try {
    const { data } = await api.get('/links')
    links.value = data || []
  } catch { links.value = [] }
  finally { loading.value = false }
}

async function saveLink() {
  saving.value = true
  try {
    await api.post('/links', form.value)
    message.success('链路已创建')
    showCreateModal.value = false
    form.value = { name: '', device_a_id: null, interface_a: '', device_z_id: null, interface_z: '', bandwidth: '10GE', link_type: 'trunk' }
    loadLinks()
  } catch (e) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally { saving.value = false }
}

const columns = [
  { title: '链路名称', key: 'name', width: 140 },
  { title: '设备A', key: 'device_a_id', width: 70 },
  { title: '接口A', key: 'interface_a', width: 90 },
  { title: '设备Z', key: 'device_z_id', width: 70 },
  { title: '接口Z', key: 'interface_z', width: 90 },
  { title: '带宽', key: 'bandwidth', width: 70 },
  { title: '类型', key: 'link_type', width: 70 },
  {
    title: '状态', key: 'status', width: 70,
    render: (r) => h(NTag, { size: 'small', type: r.status === 'up' ? 'success' : 'error' }, r.status === 'up' ? 'Up' : 'Down'),
  },
]
</script>
