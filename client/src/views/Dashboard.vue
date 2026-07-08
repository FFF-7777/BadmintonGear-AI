<template>
  <div class="page-container">
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ stats.product_count || 0 }}</div>
            <div class="stat-label">装备条目</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ stats.category_count || 0 }}</div>
            <div class="stat-label">启用品类</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ stats.vectorized_knowledge_count || 0 }}/{{ stats.knowledge_count || 0 }}</div>
            <div class="stat-label">知识库向量化</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-value">{{ stats.chat_session_count || 0 }}</div>
            <div class="stat-label">AI 会话</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>品类装备分布</template>
          <div ref="categoryChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>知识库状态</template>
          <div ref="knowledgeChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>最新装备参考价</template>
          <div ref="productChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>AI 使用概览</template>
          <div class="metric-grid">
            <div>
              <strong>{{ stats.user_count || 0 }}</strong>
              <span>注册用户</span>
            </div>
            <div>
              <strong>{{ stats.active_product_count || 0 }}</strong>
              <span>启用装备</span>
            </div>
            <div>
              <strong>{{ stats.chat_message_count || 0 }}</strong>
              <span>问答消息</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import { getDashboardStats } from '@/api/dashboard'

const stats = ref({})
const categoryChartRef = ref(null)
const knowledgeChartRef = ref(null)
const productChartRef = ref(null)
let charts = []

function disposeCharts() {
  charts.forEach((chart) => chart.dispose())
  charts = []
}

function initCharts(data) {
  disposeCharts()

  const categoryChart = echarts.init(categoryChartRef.value)
  categoryChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: ['42%', '72%'], data: data.category_stats || [] }],
  })
  charts.push(categoryChart)

  const knowledgeChart = echarts.init(knowledgeChartRef.value)
  knowledgeChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '68%', data: data.knowledge_status_stats || [] }],
  })
  charts.push(knowledgeChart)

  const latestProducts = data.latest_products || []
  const productChart = echarts.init(productChartRef.value)
  productChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: latestProducts.map((item) => item.name), axisLabel: { rotate: 25, fontSize: 10 } },
    yAxis: { type: 'value' },
    series: [{ name: '参考价', type: 'bar', data: latestProducts.map((item) => item.price), itemStyle: { color: '#22d3ee' } }],
  })
  charts.push(productChart)
}

async function loadStats() {
  const res = await getDashboardStats()
  stats.value = res.data
  await nextTick()
  initCharts(res.data)
}

function resizeCharts() {
  charts.forEach((chart) => chart.resize())
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})
</script>

<style scoped>
.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.metric-grid div {
  min-height: 130px;
  display: grid;
  align-content: center;
  gap: 8px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.metric-grid strong {
  color: #0f172a;
  font-size: 30px;
}

.metric-grid span {
  color: #64748b;
  font-weight: 700;
}
</style>
