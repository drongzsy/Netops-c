<template>
  <n-space vertical :size="16">
    <n-card title="配置管理">
      <n-space style="margin-bottom:12px">
        <n-select v-model:value="deviceId" :options="deviceOptions" placeholder="选择网元" clearable filterable style="width:200px" @update:value="loadConfigs" />
        <n-button type="primary" ghost @click="triggerBackup">配置备份</n-button>
        <n-button type="warning" ghost @click="showPushModal = true">配置下发</n-button>
        <n-button type="info" ghost @click="showComplianceModal = true">合规检查</n-button>
      </n-space>

      <n-data-table v-if="deviceId" :columns="configColumns" :data="configList" :bordered="false" :single-line="false" size="small" :loading="loading" />
      <n-empty v-else description="请选择网元查看配置版本" />
    </n-card>

    <!-- Config Detail Modal -->
    <n-modal v-model:show="showDetail" preset="card" title="配置内容" style="width:900px" :bordered="false" :segmented="{ content: true }">
      <template #header-extra>
        <n-tag :bordered="false">{{ selectedVersion }}</n-tag>
      </template>
      <n-tabs v-model:value="detailTab" type="line">
        <n-tab-pane name="content" tab="原始内容">
          <pre style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:6px;max-height:500px;overflow:auto;font-size:12px;line-height:1.6;white-space:pre-wrap;word-break:break-all;">{{ selectedConfigContent }}</pre>
        </n-tab-pane>
        <n-tab-pane name="diff" tab="对比版本">
          <n-space vertical>
            <n-space>
              <n-select v-model:value="diffFrom" :options="versionOptions" placeholder="旧版本" style="width:200px" />
              <n-select v-model:value="diffTo" :options="versionOptions" placeholder="新版本" style="width:200px" />
              <n-button type="primary" size="small" @click="loadDiff" :loading="diffLoading">对比</n-button>
            </n-space>
            <pre v-if="diffContent" style="background:#fff;padding:12px;border:1px solid #d9d9d9;border-radius:4px;max-height:400px;overflow:auto;font-size:12px;white-space:pre-wrap;word-break:break-all;">{{ diffContent }}</pre>
            <n-alert v-if="diffError" type="error" closable>{{ diffError }}</n-alert>
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-modal>

    <!-- Push Config Modal -->
    <n-modal v-model:show="showPushModal" preset="card" title="配置下发" style="width:600px" :bordered="false">
      <n-space vertical>
        <n-select v-model:value="pushDevice" :options="deviceOptions" placeholder="选择目标网元" filterable />
        <n-input v-model:value="pushContent" type="textarea" rows="10" placeholder="粘贴配置命令&#10;例如:&#10;interface GigabitEthernet0/0/1&#10;description Uplink-To-Core&#10;commit" />
        <n-alert v-if="pushResult" :title="pushResult.status === 'success' ? '下发任务已提交' : '提交失败'" :type="pushResult.status === 'success' ? 'success' : 'error'" closable @close="pushResult = null">
          {{ pushResult.message }}
        </n-alert>
      </n-space>
      <template #footer>
        <n-button type="primary" @click="executePush" :loading="pushLoading" :disabled="!pushDevice || !pushContent.trim()">执行下发</n-button>
      </template>
    </n-modal>

    <!-- Compliance Check Modal -->
    <n-modal v-model:show="showComplianceModal" preset="card" title="合规检查" style="width:700px" :bordered="false">
      <n-space vertical>
        <n-select v-model:value="complianceDevice" :options="deviceOptions" placeholder="选择目标网元" filterable />
        <n-checkbox-group v-model:value="checkItems">
          <n-space>
            <n-checkbox value="bgp">BGP 配置</n-checkbox>
            <n-checkbox value="snmp">SNMP 配置</n-checkbox>
            <n-checkbox value="acl">ACL 规则</n-checkbox>
            <n-checkbox value="ntp">NTP 配置</n-checkbox>
          </n-space>
        </n-checkbox-group>
        <n-alert v-if="complianceStatus" :type="complianceStatus.type" closable @close="complianceStatus = null">
          {{ complianceStatus.message }}
        </n-alert>
        <n-data-table v-if="complianceResult.length" :columns="complianceColumns" :data="complianceResult" size="small" :bordered="false" />
      </n-space>
      <template #footer>
        <n-button type="primary" @click="executeCompliance" :loading="complianceLoading" :disabled="!complianceDevice">开始检查</n-button>
      </template>
    </n-modal>
  </n-space>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue'
import { NButton, NTag, NSpace, useMessage } from 'naive-ui'
import { deviceApi, configApi, taskApi } from '../api'

const message = useMessage()

const deviceId = ref(null)
const deviceOptions = ref([])
const configList = ref([])
const loading = ref(false)

const showDetail = ref(false)
const detailTab = ref('content')
const selectedVersion = ref('')
const selectedConfigContent = ref('')
const diffFrom = ref(null)
const diffTo = ref(null)
const diffContent = ref('')
const diffLoading = ref(false)
const diffError = ref('')

const showPushModal = ref(false)
const pushDevice = ref(null)
const pushContent = ref('')
const pushLoading = ref(false)
const pushResult = ref(null)

const showComplianceModal = ref(false)
const complianceDevice = ref(null)
const checkItems = ref(['bgp', 'snmp'])
const complianceLoading = ref(false)
const complianceResult = ref([])
const complianceStatus = ref(null)

onMounted(async () => {
  try {
    const { data } = await deviceApi.list({ limit: 100 })
    deviceOptions.value = (data.items || []).map((d) => ({
      label: `${d.name} (${d.ip_address})`,
      value: d.id,
    }))
  } catch (e) {
    message.error('加载设备列表失败')
  }
})

async function loadConfigs() {
  if (!deviceId.value) return
  loading.value = true
  try {
    const { data } = await configApi.list(deviceId.value)
    configList.value = data || []
  } catch {
    message.error('加载配置版本失败')
    configList.value = []
  } finally {
    loading.value = false
  }
}

const versionOptions = computed(() =>
  configList.value.map((c) => ({
    label: `${c.version} — ${new Date(c.collected_at).toLocaleString()}`,
    value: c.version,
  }))
)

function viewConfig(row) {
  selectedVersion.value = row.version
  selectedConfigContent.value = row.content
  showDetail.value = true
}

async function loadDiff() {
  if (!diffFrom.value || !diffTo.value) return
  diffLoading.value = true
  diffError.value = ''
  try {
    const { data } = await configApi.diff(deviceId.value, diffFrom.value, diffTo.value)
    diffContent.value = data.diff || '无差异'
  } catch {
    diffError.value = '加载版本差异失败'
    diffContent.value = ''
  } finally {
    diffLoading.value = false
  }
}

async function triggerBackup() {
  if (!deviceId.value) {
    message.warning('请先选择网元')
    return
  }
  try {
    const { data } = await taskApi.create({
      task_type: 'backup',
      device_ids: [deviceId.value],
    })
    message.success(`备份任务已提交 (ID: ${data.id})`)
    // Refresh config list after a delay
    setTimeout(loadConfigs, 3000)
  } catch (e) {
    message.error('提交失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function executePush() {
  if (!pushDevice.value || !pushContent.value.trim()) return
  pushLoading.value = true
  pushResult.value = null
  try {
    const configLines = pushContent.value
      .split('\n')
      .map(l => l.trim())
      .filter(l => l && !l.startsWith('#'))
    const { data } = await taskApi.create({
      task_type: 'push',
      device_ids: [pushDevice.value],
      extra_vars: { config_lines: configLines },
    })
    pushResult.value = { status: 'success', message: `下发任务已提交 (ID: ${data.id})，请在任务中心查看结果` }
    pushContent.value = ''
  } catch (e) {
    pushResult.value = { status: 'error', message: e.response?.data?.detail || e.message }
  } finally {
    pushLoading.value = false
  }
}

async function executeCompliance() {
  if (!complianceDevice.value) return
  complianceLoading.value = true
  complianceResult.value = []
  complianceStatus.value = null
  try {
    const { data } = await taskApi.create({
      task_type: 'compliance',
      device_ids: [complianceDevice.value],
      extra_vars: { check_items: checkItems.value },
    })
    complianceStatus.value = { type: 'info', message: `合规检查任务已提交 (ID: ${data.id})，正在检测...` }

    // Poll for result
    const poll = setInterval(async () => {
      try {
        const { data: taskData } = await taskApi.get(data.id)
        if (taskData.status === 'success' || taskData.status === 'failed' || taskData.status === 'partial') {
          clearInterval(poll)
          complianceLoading.value = false
          const compliance = taskData.result?.compliance || {}
          const deviceChecks = compliance[String(complianceDevice.value)] || []
          if (deviceChecks.length) {
            complianceResult.value = deviceChecks
            complianceStatus.value = { type: 'success', message: '合规检查完成' }
          } else {
            complianceStatus.value = { type: 'warning', message: '未获取到检查结果，设备可能不可达' }
          }
        }
      } catch {
        clearInterval(poll)
        complianceLoading.value = false
        complianceStatus.value = { type: 'error', message: '查询任务结果失败' }
      }
    }, 2000)
  } catch (e) {
    complianceLoading.value = false
    complianceStatus.value = { type: 'error', message: '提交失败: ' + (e.response?.data?.detail || e.message) }
  }
}

const configColumns = [
  { title: '版本', key: 'version', width: 120 },
  { title: '采集时间', key: 'collected_at', width: 180, render: (r) => new Date(r.collected_at).toLocaleString() },
  { title: '操作', width: 120, render: (r) => h(NButton, { size: 'tiny', quaternary: true, onClick: () => viewConfig(r) }, '查看') },
]

const complianceColumns = [
  { title: '检查项', key: 'item', width: 120 },
  { title: '状态', key: 'status', width: 80, render: (r) => h(NTag, { type: r.status === 'pass' ? 'success' : 'error', size: 'small' }, r.status === 'pass' ? '通过' : '未通过') },
  { title: '详情', key: 'detail' },
]
</script>
