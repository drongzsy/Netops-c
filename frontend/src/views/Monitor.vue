<template>
  <n-space vertical :size="16">
    <n-card title="性能监控">
      <n-space style="margin-bottom:12px">
        <n-select v-model:value="deviceId" :options="deviceOptions" placeholder="选择网元" clearable filterable style="width:200px" @update:value="loadLatest" />
        <n-button-group>
          <n-button :type="metricType === 'cpu' ? 'primary' : 'default'" size="small" @click="switchMetric('cpu')">CPU</n-button>
          <n-button :type="metricType === 'memory' ? 'primary' : 'default'" size="small" @click="switchMetric('memory')">内存</n-button>
          <n-button :type="metricType === 'temperature' ? 'primary' : 'default'" size="small" @click="switchMetric('temperature')">温度</n-button>
        </n-button-group>
        <n-button-group>
          <n-button :type="hours === 1 ? 'primary' : 'default'" size="small" @click="switchHours(1)">1h</n-button>
          <n-button :type="hours === 6 ? 'primary' : 'default'" size="small" @click="switchHours(6)">6h</n-button>
          <n-button :type="hours === 24 ? 'primary' : 'default'" size="small" @click="switchHours(24)">24h</n-button>
        </n-button-group>
        <n-alert v-if="errorMsg" type="warning" closable @close="errorMsg = ''">{{ errorMsg }}</n-alert>
      </n-space>

      <n-empty v-if="!deviceId" description="请选择网元查看性能数据" />
    </n-card>

    <n-grid v-if="deviceId && latestMetrics.length" :cols="3" :x-gap="12">
      <n-gi v-for="m in latestMetrics" :key="m.metric_type">
        <n-card size="small" :title="metricLabel(m.metric_type)">
          <n-h1 prefix="bar" style="margin:0;font-size:24px;" :type="m.metric_type === 'cpu' ? 'error' : 'success'">
            {{ m.value }}<small style="font-size:12px;color:#999"> {{ m.unit || '' }}</small>
          </n-h1>
          <small style="color:#999">采集于 {{ new Date(m.collected_at).toLocaleTimeString() }}</small>
        </n-card>
      </n-gi>
    </n-grid>

    <n-card v-if="deviceId" size="small">
      <template #header>
        {{ metricLabel(metricType) }} 趋势（最近 {{ hours }}h）
      </template>
      <div v-if="chartData.length" ref="chartRef" style="width:100%;height:360px"></div>
      <n-empty v-else description="暂无数据" />
    </n-card>

    <n-card v-if="deviceId" size="small" title="接口流量">
      <n-empty description="接口流量数据 — 需 Ansible 采集后展示" />
    </n-card>
  </n-space>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { deviceApi, monitorApi } from '../api'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer])

const deviceId = ref(null)
const deviceOptions = ref([])
const metricType = ref('cpu')
const hours = ref(1)
const latestMetrics = ref([])
const chartData = ref([])
const chartRef = ref(null)
const errorMsg = ref('')
let chartInstance = null

onMounted(async () => {
  try {
    const { data } = await deviceApi.list({ limit: 100 })
    deviceOptions.value = (data.items || []).map((d) => ({
      label: `${d.name} (${d.ip_address})`,
      value: d.id,
    }))
  } catch (e) {
    errorMsg.value = '加载设备列表失败'
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

watch(metricType, () => { if (deviceId.value) loadChart() })
watch(hours, () => { if (deviceId.value) loadChart() })

function metricLabel(type) {
  const map = { cpu: 'CPU 使用率', memory: '内存使用率', temperature: '温度' }
  return map[type] || type
}

function switchMetric(type) {
  metricType.value = type
}

function switchHours(h) {
  hours.value = h
}

async function loadLatest() {
  if (!deviceId.value) return
  errorMsg.value = ''
  chartData.value = []
  try {
    const { data } = await monitorApi.latest(deviceId.value)
    latestMetrics.value = data || []
  } catch {
    latestMetrics.value = []
    errorMsg.value = '加载最新指标失败'
  }
  loadChart()
}

async function loadChart() {
  if (!deviceId.value) return

  errorMsg.value = ''
  try {
    const { data: resp } = await monitorApi.metrics(deviceId.value, metricType.value, hours.value)
    chartData.value = resp.data || []
    await nextTick()
    renderChart()
  } catch {
    chartData.value = []
    errorMsg.value = '加载趋势数据失败'
  }
}

function renderChart() {
  if (!chartRef.value || !chartData.value.length) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: {
      type: 'time',
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 11 },
    },
    dataZoom: [{ type: 'inside', start: 0, end: 100 }],
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.15 },
        data: chartData.value.map((d) => [new Date(d.time).getTime(), d.value]),
      },
    ],
  }

  chartInstance.setOption(option, true)
  chartInstance.resize()
}
</script>
