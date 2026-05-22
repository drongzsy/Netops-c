<template>
  <n-message-provider>
    <n-layout position="absolute">
      <n-layout-header style="height:52px;background:#001529;display:flex;align-items:center;padding:0 24px;">
        <div style="color:#fff;font-size:18px;font-weight:700;margin-right:40px;">
          <span style="color:#1890ff">◆</span> NetOps
        </div>
        <n-menu mode="horizontal" :value="route.path" :options="menuOptions" @update:value="onMenuChange"
          style="background:transparent;flex:1" />
        <div v-if="auth.user" style="display:flex;align-items:center;gap:12px;">
          <n-tag :bordered="false" size="small" style="background:rgba(255,255,255,0.1);color:#ccc;border:none;">
            <n-icon size="14" style="vertical-align:-2px;margin-right:4px;"><component :is="DesktopOutlined" /></n-icon>
            {{ auth.user.username }}
          </n-tag>
          <n-button quaternary size="tiny" style="color:rgba(255,255,255,0.65);" @click="handleLogout">退出</n-button>
        </div>
      </n-layout-header>
      <n-layout-content style="background:#f0f2f5;padding:16px 24px;height:calc(100vh - 52px);overflow:auto;">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-message-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { h } from 'vue'
import { NIcon } from 'naive-ui'
import { DashboardOutlined, DesktopOutlined, FileTextOutlined, OrderedListOutlined, AreaChartOutlined, KeyOutlined, ClusterOutlined } from '@vicons/antd'
import { auth } from './stores/auth'

const router = useRouter()
const route = useRoute()

const menuOptions = [
  { label: '仪表盘', key: '/', icon: () => h(NIcon, null, { default: () => h(DashboardOutlined) }) },
  { label: '设备', key: '/devices', icon: () => h(NIcon, null, { default: () => h(DesktopOutlined) }) },
  { label: '链路', key: '/links', icon: () => h(NIcon, null, { default: () => h(ClusterOutlined) }) },
  { label: 'IP 地址', key: '/ipam', icon: () => h(NIcon, null, { default: () => h(ClusterOutlined) }) },
  { label: '配置', key: '/config', icon: () => h(NIcon, null, { default: () => h(FileTextOutlined) }) },
  { label: '监控', key: '/monitor', icon: () => h(NIcon, null, { default: () => h(AreaChartOutlined) }) },
  { label: '告警', key: '/alerts', icon: () => h(NIcon, null, { default: () => h(AreaChartOutlined) }) },
  { label: '凭据', key: '/credentials', icon: () => h(NIcon, null, { default: () => h(KeyOutlined) }) },
  { label: '任务', key: '/tasks', icon: () => h(NIcon, null, { default: () => h(OrderedListOutlined) }) },
]

function onMenuChange(key) {
  router.push(key)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => {
  auth.loadUser()
})
</script>
