<template>
  <n-card title="📄 配置脚本状态" size="small">
    <n-data-table :columns="columns" :data="data" :bordered="false" :single-line="false" size="small" />
  </n-card>
</template>

<script setup>
import { h } from 'vue'

const columns = [
  { title: '网元', key: 'name', width: 80, render: (r) => h('strong', r.name) },
  { title: 'IP', key: 'ip', width: 120 },
  { title: '操作', key: 'op', width: 80 },
  {
    title: '状态', key: 'status', width: 80,
    render: (r) => h('span', {
      style: {
        display:'inline-block', padding:'1px 10px', borderRadius:'10px',
        fontSize:'10px', fontWeight:500,
        background: r.status === '成功' ? '#f6ffed' : r.status === '失败' ? '#fff2f0' : r.status === '部署中' ? '#e6f7ff' : '#fffbe6',
        color: r.status === '成功' ? '#52c41a' : r.status === '失败' ? '#ff4d4f' : r.status === '部署中' ? '#1890ff' : '#faad14',
        border: r.status === '成功' ? '1px solid #b7eb8f' : r.status === '失败' ? '1px solid #ffccc7' : r.status === '部署中' ? '1px solid #91d5ff' : '1px solid #ffe58f',
      }
    }, r.statusChar + ' ' + r.status),
  },
  { title: '时间', key: 'time', width: 70 },
  { title: '', key: 'action', width: 60, render: () => h('a', { style:'color:#1890ff;cursor:pointer;font-size:10px;' }, '详情') },
]

const data = [
  { name:'PB-1', ip:'192.168.100.6', op:'配置备份', status:'成功', statusChar:'✓', time:'14:25' },
  { name:'PB-2', ip:'192.168.100.7', op:'配置备份', status:'成功', statusChar:'✓', time:'14:25' },
  { name:'A_MB_1', ip:'192.168.100.10', op:'配置备份', status:'成功', statusChar:'✓', time:'14:24' },
  { name:'B_MB_1', ip:'192.168.100.13', op:'配置下发', status:'部署中', statusChar:'●', time:'14:28' },
  { name:'A-BRAS', ip:'192.168.100.12', op:'合规检查', status:'异常', statusChar:'!', time:'14:20' },
  { name:'C-1', ip:'192.168.100.2', op:'配置下发', status:'失败', statusChar:'✕', time:'13:55' },
]
</script>
