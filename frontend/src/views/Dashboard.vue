<template>
  <n-space vertical :size="16">
    <StatCards />
    <n-grid :cols="2" :x-gap="16">
      <n-gi>
        <TopologyView />
      </n-gi>
      <n-gi>
        <n-space vertical :size="16">
          <ConfigStatusTable />
          <n-grid :cols="2" :x-gap="16">
            <n-gi>
              <n-card title="📊 设备健康度" size="small">
                <div v-for="(item,i) in healthData" :key="i" style="display:flex;align-items:center;padding:3px 0;font-size:11px;">
                  <span style="width:55px;font-weight:500;">{{ item.name }}</span>
                  <n-progress type="line" :percentage="item.val" :height="8" :rail-color="'#f0f0f0'"
                    :color="item.val > 80 ? '#ff4d4f' : item.val > 60 ? '#fa8c16' : '#52c41a'" style="flex:1;margin:0 8px;" />
                  <span style="width:30px;text-align:right;font-size:10px;color:#888;">{{ item.val }}%</span>
                </div>
              </n-card>
            </n-gi>
            <n-gi>
              <n-card title="📋 今日任务" size="small">
                <div v-for="(t,i) in taskSummary" :key="i" style="display:flex;justify-content:space-between;padding:4px 0;font-size:11px;border-bottom:1px solid #f8f8f8;">
                  <span>{{ t.name }}</span><span :style="{color:t.color,fontWeight:600}">{{ t.label }}</span>
                </div>
              </n-card>
            </n-gi>
          </n-grid>
          <n-card title="🔄 最近动态" size="small">
            <n-timeline>
              <n-timeline-item v-for="(evt,i) in events" :key="i" :type="evt.type" :time="evt.time" :content="evt.msg" />
            </n-timeline>
          </n-card>
        </n-space>
      </n-gi>
    </n-grid>
  </n-space>
</template>

<script setup>
import { ref } from 'vue'
import StatCards from '../components/StatCards.vue'
import TopologyView from '../components/TopologyView.vue'
import ConfigStatusTable from '../components/ConfigStatusTable.vue'

const healthData = ref([
  { name:'PB-1', val:35 }, { name:'A_MB_1', val:72 }, { name:'A-BRAS', val:88 },
  { name:'B_MB_1', val:22 }, { name:'BB-1', val:55 },
])

const taskSummary = ref([
  { name:'配置备份', label:'2 ✓', color:'#52c41a' },
  { name:'配置下发', label:'1 ●', color:'#722ed1' },
  { name:'合规检查', label:'1', color:'#1890ff' },
  { name:'性能采集', label:'1 ✓', color:'#52c41a' },
  { name:'失败任务', label:'1 ✕', color:'#ff4d4f' },
])

const events = ref([
  { type:'success', time:'14:25', msg:'PB-1 配置备份完成' },
  { type:'success', time:'14:22', msg:'全量性能采集完成（17台）' },
  { type:'info', time:'14:28', msg:'B_MB_1 配置部署中...' },
  { type:'warning', time:'14:20', msg:'A-BRAS 合规检查异常' },
  { type:'error', time:'13:55', msg:'C-1 配置下发失败（SSH超时）' },
])
</script>
