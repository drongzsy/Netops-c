<template>
  <n-space vertical :size="16">
    <n-card title="告警管理">
      <n-tabs v-model:value="activeTab" type="line">
        <n-tab-pane name="rules" tab="告警规则">
          <n-space style="margin-bottom:12px">
            <n-button type="primary" @click="showCreateRule = true">+ 新增规则</n-button>
            <n-button @click="loadRules">刷新</n-button>
          </n-space>
          <n-data-table :columns="ruleColumns" :data="rules" :bordered="false" :loading="loading" :pagination="{ pageSize: 10 }" />
        </n-tab-pane>
        <n-tab-pane name="history" tab="告警历史">
          <n-space style="margin-bottom:12px">
            <n-select v-model:value="filterStatus" :options="[{label:'全部',value:null},{label:'活跃',value:'active'},{label:'已解决',value:'resolved'}]" placeholder="状态" clearable style="width:120px" @update:value="loadHistory" />
            <n-button @click="loadHistory">刷新</n-button>
          </n-space>
          <n-data-table :columns="historyColumns" :data="history" :bordered="false" size="small" :loading="loading" :pagination="{ pageSize: 15 }" />
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <n-modal v-model:show="showCreateRule" preset="card" title="新增告警规则" style="width:500px" :bordered="false">
      <n-form :model="ruleForm" label-placement="left" label-width="100">
        <n-form-item label="规则名称" required>
          <n-input v-model:value="ruleForm.name" placeholder="例如: CPU 过高告警" />
        </n-form-item>
        <n-form-item label="指标类型" required>
          <n-select v-model:value="ruleForm.metric_type" :options="metricOptions" />
        </n-form-item>
        <n-form-item label="运算符" required>
          <n-select v-model:value="ruleForm.operator" :options="opOptions" />
        </n-form-item>
        <n-form-item label="阈值" required>
          <n-input-number v-model:value="ruleForm.threshold" :min="0" :max="100" style="width:100%" />
        </n-form-item>
        <n-form-item label="严重级别">
          <n-select v-model:value="ruleForm.severity" :options="severityOptions" />
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="ruleForm.enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateRule = false">取消</n-button>
          <n-button type="primary" @click="saveRule" :loading="saving">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NButton, NTag, NSpace, NSwitch, useMessage } from 'naive-ui'
import { api } from '../api'

const message = useMessage()
const activeTab = ref('rules')
const loading = ref(false)
const saving = ref(false)
const rules = ref([])
const history = ref([])
const showCreateRule = ref(false)
const filterStatus = ref(null)

const ruleForm = ref({
  name: '', metric_type: 'cpu', operator: 'gt', threshold: 80, severity: 'warning', enabled: true,
})

const metricOptions = [
  { label: 'CPU 使用率', value: 'cpu' },
  { label: '内存使用率', value: 'memory' },
  { label: '接口 Down', value: 'interface_down' },
]

const opOptions = [
  { label: '> (大于)', value: 'gt' },
  { label: '>= (大于等于)', value: 'gte' },
  { label: '< (小于)', value: 'lt' },
  { label: '<= (小于等于)', value: 'lte' },
]

const severityOptions = [
  { label: '警告', value: 'warning' },
  { label: '严重', value: 'critical' },
  { label: '信息', value: 'info' },
]

onMounted(() => { loadRules(); loadHistory() })

async function loadRules() {
  loading.value = true
  try { const { data } = await api.get('/alerts/rules'); rules.value = data || [] }
  catch { message.error('加载规则失败') }
  finally { loading.value = false }
}

async function loadHistory() {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    const { data } = await api.get('/alerts/history', { params })
    history.value = data.items || []
  } catch { history.value = [] }
  finally { loading.value = false }
}

async function saveRule() {
  saving.value = true
  try {
    await api.post('/alerts/rules', ruleForm.value)
    message.success('规则已创建')
    showCreateRule.value = false
    ruleForm.value = { name: '', metric_type: 'cpu', operator: 'gt', threshold: 80, severity: 'warning', enabled: true }
    loadRules()
  } catch (e) { message.error(e.response?.data?.detail || '创建失败') }
  finally { saving.value = false }
}

async function toggleRule(rule) {
  try { await api.put(`/alerts/rules/${rule.id}`, { enabled: rule.enabled }) }
  catch { message.error('更新失败') }
}

async function deleteRule(rule) {
  try { await api.delete(`/alerts/rules/${rule.id}`); message.success('已删除'); loadRules() }
  catch { message.error('删除失败') }
}

const ruleColumns = [
  { title: '名称', key: 'name', width: 140 },
  { title: '指标', key: 'metric_type', width: 80 },
  { title: '条件', key: 'operator', width: 60, render: (r) => ({ gt:'>',gte:'>=',lt:'<',lte:'<=' })[r.operator] || r.operator },
  { title: '阈值', key: 'threshold', width: 70 },
  { title: '级别', key: 'severity', width: 70, render: (r) => h(NTag, { size:'small', type: r.severity==='critical'?'error':'warning' }, r.severity) },
  { title: '启用', key: 'enabled', width: 60, render: (r) => h(NSwitch, { value: r.enabled, onUpdateValue: (v) => { r.enabled = v; toggleRule(r) } }) },
  { title: '操作', width: 80, render: (r) => h(NButton, { size:'tiny', quaternary:true, type:'error', onClick:() => deleteRule(r) }, '删除') },
]

const historyColumns = [
  { title: '时间', key: 'created_at', width: 160, render: (r) => r.created_at ? new Date(r.created_at).toLocaleString() : '-' },
  { title: '规则', key: 'rule_name', width: 120 },
  { title: '设备', key: 'device_id', width: 70 },
  { title: '指标', key: 'metric_type', width: 70 },
  { title: '值', key: 'metric_value', width: 70 },
  { title: '阈值', key: 'threshold', width: 70 },
  { title: '级别', key: 'severity', width: 70, render: (r) => h(NTag, { size:'small', type: r.severity==='critical'?'error':'warning' }, r.severity) },
  { title: '状态', key: 'status', width: 70, render: (r) => h(NTag, { size:'small', type: r.status==='active'?'error':'success' }, r.status==='active'?'活跃':'已解决') },
]
</script>
