<template>
  <n-space vertical :size="16">
    <n-card title="IP 地址管理 (IPAM)">
      <n-space style="margin-bottom:12px">
        <n-button type="primary" @click="showCreateSubnet = true">+ 新增子网</n-button>
        <n-button @click="loadSubnets">刷新</n-button>
      </n-space>

      <n-tabs v-model:value="activeTab" type="line">
        <n-tab-pane name="subnets" tab="子网列表">
          <n-data-table :columns="subnetColumns" :data="subnets" :bordered="false" :loading="loading"
            :pagination="{ pageSize: 15 }" @update:checked-row-keys="onSubnetSelect" />
        </n-tab-pane>

        <n-tab-pane name="addresses" tab="IP 地址明细">
          <n-space style="margin-bottom:12px">
            <n-select v-model:value="filterSubnetId" :options="subnetOptions" placeholder="选择子网" clearable filterable style="width:260px" @update:value="loadAddresses" />
            <n-select v-model:value="filterStatus" :options="statusOptions" placeholder="状态" clearable style="width:120px" @update:value="loadAddresses" />
            <n-input v-model:value="searchIP" placeholder="搜索 IP" clearable style="width:200px" @keyup.enter="loadAddresses" />
          </n-space>
          <n-data-table :columns="addressColumns" :data="addresses" :bordered="false" size="small" :loading="loading" :pagination="{ pageSize: 20 }" />
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <!-- Create Subnet Modal -->
    <n-modal v-model:show="showCreateSubnet" preset="card" title="新增子网段" style="width:520px" :bordered="false">
      <n-form :model="subnetForm" label-placement="left" label-width="100">
        <n-form-item label="网段" required>
          <n-input v-model:value="subnetForm.network" placeholder="例如: 10.255.1.0/30" />
        </n-form-item>
        <n-form-item label="用途">
          <n-select v-model:value="subnetForm.purpose" :options="purposeOptions" placeholder="选择用途" />
        </n-form-item>
        <n-form-item label="VLAN ID">
          <n-input-number v-model:value="subnetForm.vlan_id" :min="1" :max="4094" placeholder="可选" />
        </n-form-item>
        <n-form-item label="VRF">
          <n-input v-model:value="subnetForm.vrf" placeholder="default" />
        </n-form-item>
        <n-form-item label="所在地">
          <n-select v-model:value="subnetForm.location" :options="locationOptions" placeholder="选择地市" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="subnetForm.description" type="textarea" rows="2" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateSubnet = false">取消</n-button>
          <n-button type="primary" @click="saveSubnet" :loading="saving">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NButton, NTag, NSpace, useMessage } from 'naive-ui'
import { api } from '../api'

const message = useMessage()
const activeTab = ref('subnets')
const loading = ref(false)
const saving = ref(false)
const subnets = ref([])
const addresses = ref([])
const showCreateSubnet = ref(false)
const filterSubnetId = ref(null)
const filterStatus = ref(null)
const searchIP = ref('')

const subnetForm = ref({
  network: '',
  purpose: null,
  vlan_id: null,
  vrf: 'default',
  location: null,
  description: '',
})

const purposeOptions = [
  { label: '互联地址 (Interconnect)', value: 'interconnect' },
  { label: '环回地址 (Loopback)', value: 'loopback' },
  { label: '管理地址 (Management)', value: 'management' },
  { label: '业务地址 (Service)', value: 'service' },
  { label: '保留地址 (Reserved)', value: 'reserved' },
]

const locationOptions = [
  { label: '武汉', value: '武汉' },
  { label: '襄阳', value: '襄阳' },
  { label: '省外', value: '省外' },
]

const statusOptions = [
  { label: '已占用', value: 'used' },
  { label: '可用', value: 'available' },
  { label: '预留', value: 'reserved' },
]

onMounted(() => {
  loadSubnets()
})

async function loadSubnets() {
  loading.value = true
  try {
    const { data } = await api.get('/ipam/subnets')
    subnets.value = data || []
  } catch (e) {
    message.error('加载子网列表失败')
  } finally {
    loading.value = false
  }
}

async function loadAddresses() {
  loading.value = true
  try {
    const params = {}
    if (filterSubnetId.value) params.subnet_id = filterSubnetId.value
    if (filterStatus.value) params.status = filterStatus.value
    if (searchIP.value) params.search = searchIP.value
    const { data } = await api.get('/ipam/addresses', { params })
    addresses.value = data.items || []
  } catch {
    addresses.value = []
  } finally {
    loading.value = false
  }
}

const subnetOptions = computed(() =>
  subnets.value.map((s) => ({
    label: `${s.network} (${s.purpose || '-'})`,
    value: s.id,
  }))
)

import { computed } from 'vue'

function onSubnetSelect(keys) {
  if (keys.length) {
    filterSubnetId.value = keys[0]
    activeTab.value = 'addresses'
    loadAddresses()
  }
}

async function saveSubnet() {
  if (!subnetForm.value.network) {
    message.warning('请输入网段')
    return
  }
  saving.value = true
  try {
    const payload = { ...subnetForm.value }
    if (!payload.vlan_id) delete payload.vlan_id
    await api.post('/ipam/subnets', payload)
    message.success('子网已创建')
    showCreateSubnet.value = false
    subnetForm.value = { network: '', purpose: null, vlan_id: null, vrf: 'default', location: null, description: '' }
    loadSubnets()
  } catch (e) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    saving.value = false
  }
}

const subnetColumns = [
  { title: '网段', key: 'network', width: 140 },
  { title: '用途', key: 'purpose', width: 100 },
  { title: 'VLAN', key: 'vlan_id', width: 70 },
  { title: 'VRF', key: 'vrf', width: 80 },
  { title: '位置', key: 'location', width: 60 },
  {
    title: '使用率',
    key: 'usage',
    width: 120,
    render: (r) => {
      const pct = r.total_count > 0 ? Math.round(r.used_count / r.total_count * 100) : 0
      return h(NSpace, { align: 'center' }, [
        h('span', { style: 'font-size:11px' }, `${r.used_count}/${r.total_count}`),
        h(NTag, { size: 'small', type: pct > 80 ? 'error' : pct > 50 ? 'warning' : 'success' }, `${pct}%`),
      ])
    },
  },
  { title: '描述', key: 'description', width: 150 },
]

const addressColumns = [
  { title: 'IP 地址', key: 'ip_address', width: 130 },
  {
    title: '状态', key: 'status', width: 80,
    render: (r) => h(NTag, {
      size: 'small',
      type: r.status === 'used' ? 'error' : r.status === 'reserved' ? 'warning' : 'success',
    }, r.status === 'used' ? '占用' : r.status === 'reserved' ? '预留' : '可用'),
  },
  { title: '设备', key: 'device_name', width: 100 },
  { title: '接口', key: 'interface', width: 90 },
  { title: '备注', key: 'description', width: 150 },
]
</script>
