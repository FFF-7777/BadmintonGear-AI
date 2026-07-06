<template>
  <div class="page-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom:20px">
      <el-col :span="8">
        <el-card shadow="hover"><div class="stat-card"><div class="stat-value">{{ stats.user_count || 0 }}</div><div class="stat-label">用户总数</div></div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover"><div class="stat-card"><div class="stat-value">{{ stats.order_count || 0 }}</div><div class="stat-label">订单总数</div></div></el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover"><div class="stat-card"><div class="stat-value">¥{{ (stats.total_sales || 0).toFixed(2) }}</div><div class="stat-label">总销售额</div></div></el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>近7日订单趋势</template>
          <div ref="orderChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>近7日销售额趋势</template>
          <div ref="salesChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>装备分类占比</template>
          <div ref="categoryChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>订单状态分布</template>
          <div ref="statusChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>热销装备Top5</template>
          <div ref="hotChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * 数据看板页面 - ECharts统计图表
 */
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { getDashboardStats } from '@/api/dashboard'

const stats = ref({})
const orderChartRef = ref(null)
const salesChartRef = ref(null)
const categoryChartRef = ref(null)
const statusChartRef = ref(null)
const hotChartRef = ref(null)
let charts = []

/** 初始化图表 */
function initCharts(data) {
  // 近7日订单趋势
  const orderChart = echarts.init(orderChartRef.value)
  orderChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.trend_dates },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: '订单数', type: 'line', data: data.trend_orders, smooth: true, areaStyle: { opacity: 0.3 } }],
  })
  charts.push(orderChart)

  // 近7日销售额
  const salesChart = echarts.init(salesChartRef.value)
  salesChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.trend_dates },
    yAxis: { type: 'value' },
    series: [{ name: '销售额', type: 'bar', data: data.trend_sales, itemStyle: { color: '#67c23a' } }],
  })
  charts.push(salesChart)

  // 分类占比
  const categoryChart = echarts.init(categoryChartRef.value)
  categoryChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: ['40%', '70%'], data: data.category_stats, label: { formatter: '{b}: {c}' } }],
  })
  charts.push(categoryChart)

  // 订单状态
  const statusChart = echarts.init(statusChartRef.value)
  statusChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '60%', data: data.status_stats }],
  })
  charts.push(statusChart)

  // 热销装备
  const hotChart = echarts.init(hotChartRef.value)
  hotChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.hot_products.map(p => p.name), axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{ name: '销量', type: 'bar', data: data.hot_products.map(p => p.sales), itemStyle: { color: '#e6a23c' } }],
  })
  charts.push(hotChart)
}

/** 加载统计数据 */
async function loadStats() {
  const res = await getDashboardStats()
  stats.value = res.data
  initCharts(res.data)
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', () => charts.forEach(c => c.resize()))
})

onUnmounted(() => {
  charts.forEach(c => c.dispose())
})
</script>
