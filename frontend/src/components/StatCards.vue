<template>
  <n-grid :cols="6" :x-gap="12">
    <n-grid-item v-for="s in stats" :key="s.label">
      <n-card :title="s.label" size="small" :style="{ borderLeft: `3px solid ${s.color}` }">
        <n-h1 prefix="bar" style="margin:0;font-size:22px;" :type="s.type">{{ s.value }}</n-h1>
        <small style="color:#999">{{ s.sub }}</small>
      </n-card>
    </n-grid-item>
  </n-grid>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi } from '../api'

const stats = ref([
  { label: '设备总数', value: '-', sub: '已纳管', color: '#1890ff', type: 'info' },
  { label: '在线设备', value: '-', sub: '在线率 -', color: '#52c41a', type: 'success' },
  { label: '今日任务', value: '-', sub: '0 成功', color: '#fa8c16', type: 'warning' },
  { label: '异常告警', value: '-', sub: '无未处理告警', color: '#ff4d4f', type: 'error' },
  { label: '配置变更', value: '-', sub: '今日+0次变更', color: '#722ed1', type: 'default' },
  { label: '最近巡检', value: '-', sub: '全部通过', color: '#13c2c2', type: 'success' },
])

onMounted(async () => {
  try {
    const { data } = await dashboardApi.stats()
    stats.value[0].value = data.total_devices
    stats.value[1].value = data.online_devices
    stats.value[1].sub = `在线率 ${data.online_rate}%`
    stats.value[2].value = data.today_tasks
  } catch (e) { /* demo mode */ }
})
</script>
