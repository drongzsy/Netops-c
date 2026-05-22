<template>
  <n-card title="📍 CMNET 承载网拓扑 — 设备互联" size="small">
    <div class="topo-wrap">
      <svg :viewBox="`0 0 ${SVG_W} ${SVG_H}`" class="topo-svg">
        <!-- ===== 链路 (先绘制在底层) ===== -->
        <g v-for="(link, i) in links" :key="'l'+i">
          <line :x1="link.x1" :y1="link.y1" :x2="link.x2" :y2="link.y2"
                :stroke="link.color" stroke-width="2" stroke-dasharray="4,3" opacity="0.5" />
          <circle :cx="(link.x1+link.x2)/2" :cy="(link.y1+link.y2)/2" r="2" :fill="link.color" opacity="0.6" />
        </g>

        <!-- ===== 设备节点 ===== -->
        <g v-for="(d, i) in allDevices" :key="'d'+i">
          <!-- 主圆 -->
          <circle :cx="d.x" :cy="d.y" :r="d.r" :fill="d.fill" :stroke="d.stroke" stroke-width="2.5" />
          <!-- 标签 -->
          <text :x="d.x" :y="d.y + (d.isSmall ? 1 : 0)" text-anchor="middle" dominant-baseline="central"
                :font-size="d.fontSize" font-weight="700" :fill="d.textColor"
                style="pointer-events:none;user-select:none;">{{ d.name }}</text>
          <!-- 类型角标 -->
          <text :x="d.x" :y="d.y + d.r + 10" text-anchor="middle" font-size="8" fill="#999">{{ d.typeLabel }}</text>
        </g>

        <!-- ===== 层级标签（左侧） ===== -->
        <g v-for="(l, i) in layerLabels" :key="'ll'+i">
          <text :x="l.x" :y="l.y" font-size="10" font-weight="600" :fill="l.color" text-anchor="end">{{ l.text }}</text>
        </g>

        <!-- ===== 图例 ===== -->
        <g transform="translate(10, 10)">
          <rect x="0" y="0" width="130" :height="22 + legendItems.length * 16" rx="4" fill="white" stroke="#e8e8e8" stroke-width="1" opacity="0.9" />
          <text x="8" y="14" font-size="9" font-weight="600" fill="#333">图例</text>
          <g v-for="(item, i) in legendItems" :key="'leg'+i">
            <line :x1="8" :y1="30 + i*16" :x2="28" :y2="30 + i*16" :stroke="item.color" stroke-width="2" stroke-dasharray="4,3" />
            <text x="32" y="34 + i*16" font-size="8" fill="#666">{{ item.label }}</text>
          </g>
        </g>
      </svg>
    </div>
  </n-card>
</template>

<script setup>
// ─── CMNET 标准承载网拓扑 ───────────────────────────────────
// 层次: BB → PB+RR → MB → BRAS → PE/PC, 管理平面 SW 统管
// 每层 Y 坐标, 设备间距 55px
const COL = {
  BB:    { bg: '#f6ffed',  bd: '#52c41a',  txt: '#135200' },
  PB:    { bg: '#fffbe6',  bd: '#fa8c16',  txt: '#873800' },
  RR:    { bg: '#fff0f6',  bd: '#eb2f96',  txt: '#9c0030' },
  MB:    { bg: '#f9f0ff',  bd: '#722ed1',  txt: '#391063' },
  BRAS:  { bg: '#fff7e6',  bd: '#d48806',  txt: '#874d00' },
  PE:    { bg: '#fff1f0',  bd: '#f5222d',  txt: '#820014' },
  PC:    { bg: '#e6f7ff',  bd: '#1890ff',  txt: '#003a8c' },
  SW:    { bg: '#fafafa',  bd: '#8c8c8c',  txt: '#262626' },
}

function pos(name, type, x, y, isSmall = false) {
  const c = COL[type]
  const r = isSmall ? 16 : 20
  return {
    name, x, y, r, isSmall,
    typeLabel: type,
    fill: c.bg, stroke: c.bd, textColor: c.txt,
    fontSize: isSmall ? 6.5 : 7.5,
  }
}

// Y 坐标层级
const Y = { BB:55, PB:130, RR:130, MB:215, BRAS:275, PE:340, SW:400 }
const X0 = 200  // 中心参考点

// 所有设备
const allDevices = [
  // BB 层
  pos('BB-1','BB', X0-35, Y.BB), pos('BB-2','BB', X0+35, Y.BB),
  // PB 层
  pos('PB-1','PB', X0-55, Y.PB), pos('PB-2','PB', X0+55, Y.PB),
  // RR 层 (同行)
  pos('VPN_RR-1','RR', X0-130, Y.RR), pos('VPN_RR-2','RR', X0+130, Y.RR),
  // MB 层 - 武汉左, 襄阳右
  pos('A_MB_1','MB', X0-90, Y.MB), pos('A_MB_2','MB', X0-30, Y.MB),
  pos('B_MB_1','MB', X0+30, Y.MB), pos('B_MB_2','MB', X0+90, Y.MB),
  // BRAS 层
  pos('A-BRAS','BRAS', X0-60, Y.BRAS), pos('B-BRAS','BRAS', X0+60, Y.BRAS),
  // PE 层
  pos('C-1','PE', X0-90, Y.PE), pos('C-2','PE', X0+90, Y.PE),
  // PC 层 (同行 PE)
  pos('PC-1','PC', X0-25, Y.PE), pos('PC-2','PC', X0+25, Y.PE),
  // SW 层 (小圆)
  pos('S-1','SW',  X0-115, Y.SW, true), pos('S-3','SW',  X0-60, Y.SW, true),
  pos('S-5','SW',  X0-5, Y.SW, true),  pos('S-11','SW', X0+50, Y.SW, true),
  pos('S-12','SW', X0+105, Y.SW, true),
]

// 辅助: 按名称查找坐标
const M = {}
allDevices.forEach(d => { M[d.name] = d })

// 链路定义: [设备A, 设备B, 颜色, 标签]
const RAW_LINKS = [
  // BB ↔ PB
  ['BB-1','PB-1','#52c41a'], ['BB-1','PB-2','#52c41a'],
  ['BB-2','PB-1','#52c41a'], ['BB-2','PB-2','#52c41a'],
  // BB 互联
  ['BB-1','BB-2','#73d13d'],
  // PB ↔ RR (iBGP)
  ['PB-1','VPN_RR-1','#fa8c16'], ['PB-1','VPN_RR-2','#fa8c16'],
  ['PB-2','VPN_RR-1','#fa8c16'], ['PB-2','VPN_RR-2','#fa8c16'],
  // PB 互联
  ['PB-1','PB-2','#fa8c16'],
  // RR 互联
  ['VPN_RR-1','VPN_RR-2','#eb2f96'],
  // PB → 武汉 MB (双归)
  ['PB-1','A_MB_1','#722ed1'], ['PB-1','A_MB_2','#722ed1'],
  ['PB-2','A_MB_1','#722ed1'], ['PB-2','A_MB_2','#722ed1'],
  // PB → 襄阳 MB (双归)
  ['PB-1','B_MB_1','#722ed1'], ['PB-1','B_MB_2','#722ed1'],
  ['PB-2','B_MB_1','#722ed1'], ['PB-2','B_MB_2','#722ed1'],
  // 武汉 MB → BRAS
  ['A_MB_1','A-BRAS','#d48806'], ['A_MB_2','A-BRAS','#d48806'],
  // 襄阳 MB → BRAS
  ['B_MB_1','B-BRAS','#d48806'], ['B_MB_2','B-BRAS','#d48806'],
  // BRAS → PE
  ['A-BRAS','C-1','#f5222d'], ['B-BRAS','C-2','#f5222d'],
  // BRAS → PC
  ['A-BRAS','PC-1','#1890ff'], ['B-BRAS','PC-2','#1890ff'],
  // SW → 所有设备 (管理平面, 取代表性连接)
  ['S-1','PB-1','#8c8c8c'], ['S-5','PB-2','#8c8c8c'],
  ['S-3','A_MB_1','#8c8c8c'], ['S-11','A-BRAS','#8c8c8c'],
  ['S-12','B-BRAS','#8c8c8c'],
]

// 转换为 SVG 坐标
const links = RAW_LINKS.map(([a, b, color]) => {
  const da = M[a], db = M[b]
  if (!da || !db) return null
  // 连线从圆边缘出发, 角度指向目标
  const dx = db.x - da.x, dy = db.y - da.y
  const dist = Math.sqrt(dx*dx + dy*dy) || 1
  return {
    x1: da.x + dx/dist * da.r,
    y1: da.y + dy/dist * da.r,
    x2: db.x - dx/dist * db.r,
    y2: db.y - dy/dist * db.r,
    color,
  }
}).filter(Boolean)

// 层级标签 (左侧)
const layerLabels = [
  { x:30, y:Y.BB+4,   text:'集团骨干 BB',  color:'#52c41a' },
  { x:30, y:Y.PB+4,   text:'核心 PB+RR',   color:'#fa8c16' },
  { x:30, y:Y.MB+4,   text:'城域核心 MB',  color:'#722ed1' },
  { x:30, y:Y.BRAS+4, text:'业务接入 BRAS', color:'#d48806' },
  { x:30, y:Y.PE+4,   text:'客户侧 PE/PC',  color:'#f5222d' },
  { x:30, y:Y.SW+4,   text:'管理 SW',       color:'#8c8c8c' },
]

// 图例
const legendItems = [
  { label:'BB↔PB 骨干上联', color:'#52c41a' },
  { label:'PB↔RR iBGP 反射', color:'#fa8c16' },
  { label:'PB↔MB 城域双归', color:'#722ed1' },
  { label:'MB↔BRAS 业务汇聚', color:'#d48806' },
  { label:'BRAS↔PE/PC 客户接入', color:'#f5222d' },
  { label:'SW 管理平面', color:'#8c8c8c' },
]

const SVG_W = 400
const SVG_H = 440
</script>

<style scoped>
.topo-wrap {
  width: 100%;
  overflow-x: auto;
}
.topo-svg {
  width: 100%;
  min-width: 400px;
  height: auto;
  display: block;
}
</style>
