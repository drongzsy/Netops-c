<template>
  <n-space vertical :size="16">
    <n-card title="Syslog 日志">
      <n-space style="margin-bottom:12px">
        <n-input v-model:value="search" placeholder="搜索关键字" clearable style="width:200px" @keyup.enter="loadEntries" />
        <n-select v-model:value="sevFilter" :options="sevOptions" placeholder="级别" clearable style="width:120px" @update:value="loadEntries" />
        <n-select v-model:value="hostFilter" :options="hostOptions" placeholder="主机" clearable filterable style="width:160px" @update:value="loadEntries" />
        <n-select v-model:value="hoursFilter" :options="[{label:'1h',value:1},{label:'6h',value:6},{label:'24h',value:24},{label:'7d',value:168}]" placeholder="时间范围" style="width:100px" @update:value="loadEntries" />
        <n-button type="primary" @click="loadEntries">刷新</n-button>
        <n-tag v-if="summary.total > 0" :bordered="false">{{ summary.total }} 条日志</n-tag>
      </n-space>

      <n-grid v-if="summary.total > 0" :cols="4" :x-gap="12" style="margin-bottom:12px">
        <n-gi v-for="s in summary.by_severity" :key="s.severity">
          <n-card size="small" :style="{ borderTop: '2px solid ' + sevColor(s.severity) }">
            <n-h1 prefix="bar" style="margin:0;font-size:18px" :type="sevType(s.severity)">{{ s.count }}</n-h1>
            <small>{{ sevLabel(s.severity) }}</small>
          </n-card>
        </n-gi>
      </n-grid>

      <n-data-table :columns="columns" :data="entries" :bordered="false" :loading="loading" size="small"
        :pagination="{ pageSize: 25 }" :single-line="false" />
    </n-card>
  </n-space>
</template>

<script setup>
import { ref, h, onMounted, computed } from 'vue'
import { NTag } from 'naive-ui'
import { api } from '../api'

const loading = ref(false)
const search = ref('')
const sevFilter = ref(null)
const hostFilter = ref(null)
const hoursFilter = ref(24)
const entries = ref([])
const summary = ref({ total: 0, by_severity: [], by_hostname: [] })

const sevOptions = [
  { label: '紧急', value: 'emergency' }, { label: '严重', value: 'critical' },
  { label: '错误', value: 'error' }, { label: '警告', value: 'warning' },
  { label: '通知', value: 'notice' }, { label: '信息', value: 'info' },
  { label: '调试', value: 'debug' },
]

const hostOptions = computed(() => summary.value.by_hostname?.map(h => ({ label: `${h.hostname} (${h.count})`, value: h.hostname })) || [])

function sevColor(s) {
  const m = { emergency: '#ff4d4f', alert: '#ff4d4f', critical: '#ff4d4f', error: '#fa8c16', warning: '#faad14', notice: '#1890ff', info: '#52c41a', debug: '#8c8c8c' }
  return m[s] || '#8c8c8c'
}
function sevType(s) {
  const m = { emergency: 'error', alert: 'error', critical: 'error', error: 'warning', warning: 'warning' }
  return m[s] || 'default'
}
function sevLabel(s) { const m = { emergency: '紧急', alert: '告警', critical: '严重', error: '错误', warning: '警告', notice: '通知', info: '信息', debug: '调试' }; return m[s] || s }

onMounted(() => { loadSummary(); loadEntries() })

async function loadEntries() {
  loading.value = true
  try {
    const params = { hours: hoursFilter.value }
    if (search.value) params.search = search.value
    if (sevFilter.value) params.severity = sevFilter.value
    if (hostFilter.value) params.hostname = hostFilter.value
    const { data } = await api.get('/syslog/entries', { params })
    entries.value = data.items || []
  } catch { entries.value = [] }
  finally { loading.value = false }
}

async function loadSummary() {
  try {
    const { data } = await api.get('/syslog/summary', { params: { hours: hoursFilter.value } })
    summary.value = data || { total: 0, by_severity: [], by_hostname: [] }
  } catch { /* ignore */ }
}

const columns = [
  { title: '时间', key: 'received_at', width: 160, render: (r) => r.received_at ? new Date(r.received_at).toLocaleString() : '-' },
  { title: '主机', key: 'hostname', width: 100 },
  { title: '级别', key: 'severity', width: 80, render: (r) => h(NTag, { size: 'small', type: sevType(r.severity), bordered: false }, sevLabel(r.severity)) },
  { title: '设施', key: 'facility', width: 70 },
  { title: '内容', key: 'message', ellipsis: { tooltip: true } },
]
</script>
