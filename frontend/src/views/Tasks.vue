<template>
  <n-space vertical :size="16">
    <n-card title="任务中心">
      <n-space style="margin-bottom:12px">
        <n-select v-model:value="statusFilter" :options="statusOptions" placeholder="任务状态" clearable style="width:160px" @update:value="loadTasks" />
        <n-button type="primary" @click="loadTasks">刷新</n-button>
        <n-button @click="showCreateModal = true">+ 新任务</n-button>
      </n-space>

      <n-data-table
        :columns="taskColumns"
        :data="taskList"
        :bordered="false"
        :single-line="false"
        size="small"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>

    <!-- Create Task Modal -->
    <n-modal v-model:show="showCreateModal" preset="card" title="创建任务" style="width:560px" :bordered="false">
      <n-form :model="taskForm" label-placement="left" label-width="80">
        <n-form-item label="任务类型" required>
          <n-select v-model:value="taskForm.task_type" :options="createTypeOptions" />
        </n-form-item>
        <n-form-item label="目标设备" required>
          <n-select v-model:value="taskForm.device_ids" :options="deviceOptions" multiple filterable placeholder="选择一台或多台设备" />
        </n-form-item>
        <n-form-item v-if="taskForm.task_type === 'push'" label="配置命令">
          <n-input v-model:value="pushCommands" type="textarea" rows="6" placeholder="每行一条命令&#10;例如:&#10;interface GigabitEthernet0/0/1&#10;description To-Core" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="submitNewTask" :loading="submitting" :disabled="!taskForm.task_type || !taskForm.device_ids.length">提交</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Task Detail Modal -->
    <n-modal v-model:show="showDetail" preset="card" title="任务详情" style="width:700px" :bordered="false">
      <n-descriptions v-if="selectedTask" :column="1" bordered size="small">
        <n-descriptions-item label="任务 ID">
          {{ selectedTask.id }}
        </n-descriptions-item>
        <n-descriptions-item label="类型">
          <n-tag :bordered="false">{{ typeLabel(selectedTask.task_type) }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="状态">
          <n-tag :type="statusTagType(selectedTask.status)" :bordered="false">{{ statusLabel(selectedTask.status) }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="目标设备">
          {{ (selectedTask.device_ids || []).join(', ') }}
        </n-descriptions-item>
        <n-descriptions-item label="创建时间">
          {{ new Date(selectedTask.created_at).toLocaleString() }}
        </n-descriptions-item>
        <n-descriptions-item v-if="selectedTask.finished_at" label="完成时间">
          {{ new Date(selectedTask.finished_at).toLocaleString() }}
        </n-descriptions-item>
        <n-descriptions-item label="结果">
          <pre style="max-height:300px;overflow:auto;background:#f6f8fa;padding:8px;border-radius:4px;font-size:11px;">{{ JSON.stringify(selectedTask.result, null, 2) }}</pre>
        </n-descriptions-item>
      </n-descriptions>
    </n-modal>
  </n-space>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { NButton, NTag, useMessage } from 'naive-ui'
import { taskApi, deviceApi } from '../api'

const message = useMessage()

const statusFilter = ref(null)
const taskList = ref([])
const loading = ref(false)
const showDetail = ref(false)
const selectedTask = ref(null)
const pagination = ref({ pageSize: 15 })

const showCreateModal = ref(false)
const submitting = ref(false)
const deviceOptions = ref([])
const pushCommands = ref('')

const taskForm = ref({
  task_type: null,
  device_ids: [],
})

const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '运行中', value: 'running' },
  { label: '成功', value: 'success' },
  { label: '失败', value: 'failed' },
  { label: '部分成功', value: 'partial' },
]

const createTypeOptions = [
  { label: '配置备份', value: 'backup' },
  { label: '配置下发', value: 'push' },
  { label: '性能采集', value: 'collect' },
  { label: '合规检查', value: 'compliance' },
]

onMounted(() => {
  loadTasks()
  loadDevices()
})

async function loadDevices() {
  try {
    const { data } = await deviceApi.list({ limit: 200 })
    deviceOptions.value = (data.items || []).map((d) => ({
      label: `${d.name} (${d.ip_address})`,
      value: d.id,
    }))
  } catch {
    // non-critical
  }
}

async function loadTasks() {
  loading.value = true
  try {
    const params = {}
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await taskApi.list(params)
    taskList.value = data.items || []
  } catch {
    taskList.value = []
  } finally {
    loading.value = false
  }
}

async function submitNewTask() {
  submitting.value = true
  try {
    const payload = {
      task_type: taskForm.value.task_type,
      device_ids: taskForm.value.device_ids,
    }
    if (taskForm.value.task_type === 'push') {
      const lines = pushCommands.value
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('#'))
      payload.extra_vars = { config_lines: lines }
    }
    const { data } = await taskApi.create(payload)
    message.success(`任务已创建 (ID: ${data.id})`)
    showCreateModal.value = false
    taskForm.value = { task_type: null, device_ids: [] }
    pushCommands.value = ''
    loadTasks()
  } catch (e) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

function showTaskDetail(task) {
  selectedTask.value = task
  showDetail.value = true
}

function typeLabel(type) {
  const map = { backup: '配置备份', push: '配置下发', collect: '性能采集', compliance: '合规检查' }
  return map[type] || type
}

function statusLabel(status) {
  const map = { pending: '待处理', running: '运行中', success: '成功', failed: '失败', partial: '部分成功', cancelled: '已取消' }
  return map[status] || status
}

function statusTagType(status) {
  const map = { pending: 'default', running: 'info', success: 'success', failed: 'error', partial: 'warning' }
  return map[status] || 'default'
}

const taskColumns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '类型', key: 'task_type', width: 100, render: (r) => h(NTag, { bordered: false, size: 'small' }, typeLabel(r.task_type)) },
  { title: '目标', key: 'device_ids', width: 160, render: (r) => (r.device_ids || []).join(', ') },
  {
    title: '状态', key: 'status', width: 90,
    render: (r) => h(NTag, { type: statusTagType(r.status), size: 'small', bordered: false }, statusLabel(r.status)),
  },
  { title: '创建时间', key: 'created_at', width: 170, render: (r) => new Date(r.created_at).toLocaleString() },
  { title: '完成时间', key: 'finished_at', width: 170, render: (r) => r.finished_at ? new Date(r.finished_at).toLocaleString() : '-' },
  {
    title: '操作', width: 70,
    render: (r) => h(NButton, { size: 'tiny', quaternary: true, onClick: () => showTaskDetail(r) }, '详情'),
  },
]
</script>
