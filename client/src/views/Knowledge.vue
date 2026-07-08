<template>
  <div class="knowledge-page">
    <section class="knowledge-hero">
      <div class="hero-copy">
        <div class="hero-kicker">
          <el-icon><Lightning /></el-icon>
          RAG SPORTS INTELLIGENCE
        </div>
        <h1>羽毛球装备知识中枢</h1>
        <p>
          上传评测、参数、训练建议与售后资料，让导购 AI 更快理解用户水平、打法和预算。
        </p>
        <div class="hero-actions">
          <el-upload
            :show-file-list="false"
            :http-request="handleUpload"
            accept=".txt,.docx,.pdf,.md,.markdown"
          >
            <el-button type="primary" size="large" class="upload-action">
              <el-icon><UploadFilled /></el-icon>
              上传知识文件
            </el-button>
          </el-upload>
          <span class="upload-tip">支持 txt / docx / pdf / markdown，建议单文件 20MB 内</span>
        </div>
      </div>

      <div class="hero-panel">
        <div class="panel-top">
          <span>向量化进度</span>
          <strong>{{ vectorizedRate }}%</strong>
        </div>
        <div class="progress-track">
          <span :style="{ width: `${vectorizedRate}%` }"></span>
        </div>
        <div class="hero-metrics">
          <div>
            <strong>{{ total }}</strong>
            <span>文件总数</span>
          </div>
          <div>
            <strong>{{ vectorizedCount }}</strong>
            <span>已向量化</span>
          </div>
          <div>
            <strong>{{ totalChunks }}</strong>
            <span>知识分块</span>
          </div>
        </div>
      </div>
    </section>

    <section class="knowledge-shell">
      <div class="section-head">
        <div>
          <span class="section-label">Knowledge Files</span>
          <h2>知识库文件</h2>
        </div>
        <el-button class="refresh-btn" @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <div class="table-wrapper knowledge-table">
        <el-table :data="tableData" style="width:100%" row-key="id">
          <el-table-column prop="file_name" label="文件" min-width="240" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="file-cell">
                <span class="file-icon">
                  <el-icon><Document /></el-icon>
                </span>
                <div>
                  <strong>{{ row.file_name }}</strong>
                  <span>ID {{ row.id }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="file_type" label="类型" min-width="90">
            <template #default="{ row }">
              <el-tag round effect="plain">{{ row.file_type || '文件' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="file_size" label="大小" min-width="110">
            <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="分块" min-width="100">
            <template #default="{ row }">
              <span class="chunk-pill">
                <el-icon><Files /></el-icon>
                {{ row.chunk_count || 0 }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" min-width="120">
            <template #default="{ row }">
              <el-tag :type="statusMeta(row.status).type" round>
                {{ statusMeta(row.status).label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_msg" label="错误信息" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ row.error_msg || '-' }}</template>
          </el-table-column>
          <el-table-column prop="create_time" label="上传时间" min-width="170">
            <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
          </el-table-column>
          <el-table-column label="操作" min-width="180" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="handleVectorize(row)">
                <el-icon><Cpu /></el-icon>
                重新向量化
              </el-button>
              <el-button type="danger" link @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.page_size"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @change="loadData"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteKnowledge, getKnowledgeList, uploadKnowledge, vectorizeKnowledge } from '@/api/knowledge'
import { formatDateTime, knowledgeStatusMap } from '@/utils/date'

const tableData = ref([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10 })

const vectorizedCount = computed(() => tableData.value.filter(item => item.status === 1).length)
const totalChunks = computed(() => tableData.value.reduce((sum, item) => sum + Number(item.chunk_count || 0), 0))
const vectorizedRate = computed(() => {
  if (!tableData.value.length) return 0
  return Math.round((vectorizedCount.value / tableData.value.length) * 100)
})

async function loadData() {
  const res = await getKnowledgeList(query)
  tableData.value = res.data.list
  total.value = res.data.total
}

function statusMeta(status) {
  const map = {
    0: { label: knowledgeStatusMap[0], type: 'info' },
    1: { label: knowledgeStatusMap[1], type: 'success' },
    2: { label: knowledgeStatusMap[2], type: 'danger' },
  }
  return map[status] || { label: '未知', type: 'info' }
}

function formatSize(size) {
  const kb = Number(size || 0) / 1024
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb.toFixed(1)} KB`
}

async function handleUpload({ file }) {
  ElMessage.info('正在上传并向量化，请稍候...')
  try {
    await uploadKnowledge(file)
    ElMessage.success('上传并向量化成功')
  } finally {
    loadData()
  }
}

async function handleVectorize(row) {
  ElMessage.info('正在重新向量化...')
  try {
    await vectorizeKnowledge(row.id)
    ElMessage.success('向量化完成')
  } finally {
    loadData()
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该知识库文件？', '提示', { type: 'warning' })
  await deleteKnowledge(row.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.knowledge-page {
  display: grid;
  gap: 20px;
}

.knowledge-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.6fr);
  gap: 22px;
  min-height: 300px;
  padding: 30px;
  overflow: hidden;
  color: #f9fafb;
  border-radius: 28px;
  background:
    linear-gradient(135deg, rgba(9, 12, 20, 0.96), rgba(17, 24, 39, 0.88)),
    url('@/assets/hero.png') center / cover;
  box-shadow: 0 26px 70px rgba(15, 23, 42, 0.18);
}

.knowledge-hero::after {
  content: '';
  position: absolute;
  inset: auto 24px 22px auto;
  width: 42%;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, #bef264, #22d3ee, #fb7185);
}

.hero-copy {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 720px;
}

.hero-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  margin-bottom: 18px;
  padding: 8px 12px;
  color: #d9f99d;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  border: 1px solid rgba(217, 249, 157, 0.28);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(18px);
}

.hero-copy h1 {
  margin: 0;
  font-size: 46px;
  line-height: 1.08;
  font-weight: 850;
}

.hero-copy p {
  max-width: 560px;
  margin: 16px 0 26px;
  color: rgba(249, 250, 251, 0.76);
  font-size: 16px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
}

.upload-action {
  height: 46px;
  padding: 0 20px;
  border: 0;
  border-radius: 999px;
  color: #08111f;
  font-weight: 800;
  background: linear-gradient(135deg, #d9f99d, #67e8f9);
  box-shadow: 0 16px 34px rgba(34, 211, 238, 0.28);
}

.upload-tip {
  color: rgba(249, 250, 251, 0.64);
  font-size: 13px;
}

.hero-panel {
  position: relative;
  z-index: 1;
  align-self: center;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.11);
  backdrop-filter: blur(22px);
}

.panel-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  color: rgba(249, 250, 251, 0.7);
  font-size: 13px;
}

.panel-top strong {
  color: #fff;
  font-size: 34px;
  line-height: 1;
}

.progress-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
}

.progress-track span {
  display: block;
  height: 100%;
  min-width: 8px;
  border-radius: inherit;
  background: linear-gradient(90deg, #bef264, #22d3ee);
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 18px;
}

.hero-metrics div {
  padding: 14px 10px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.1);
}

.hero-metrics strong,
.hero-metrics span {
  display: block;
}

.hero-metrics strong {
  color: #fff;
  font-size: 22px;
}

.hero-metrics span {
  margin-top: 6px;
  color: rgba(249, 250, 251, 0.58);
  font-size: 12px;
}

.knowledge-shell {
  padding: 22px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 20px 55px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(18px);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
}

.section-head h2 {
  margin: 4px 0 0;
  color: #0f172a;
  font-size: 22px;
}

.refresh-btn {
  border-radius: 999px;
}

.knowledge-table {
  overflow-x: auto;
  overflow-y: hidden;
  border: 1px solid #edf2f7;
  border-radius: 18px;
  background: #fff;
}

.knowledge-table :deep(.el-table) {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: #f5fbff;
}

.knowledge-table :deep(.el-table th.el-table__cell) {
  height: 52px;
  color: #64748b;
  font-weight: 800;
  background: #f8fafc;
}

.knowledge-table :deep(.el-table td.el-table__cell) {
  height: 70px;
  color: #334155;
  border-bottom: 1px solid #eef2f7;
}

.file-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.file-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  color: #0f172a;
  border-radius: 14px;
  background: linear-gradient(135deg, #d9f99d, #67e8f9);
}

.file-cell strong,
.file-cell span {
  display: block;
}

.file-cell strong {
  max-width: 360px;
  overflow: hidden;
  color: #0f172a;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-cell span {
  margin-top: 5px;
  color: #94a3b8;
  font-size: 12px;
}

.chunk-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 54px;
  padding: 7px 10px;
  color: #0f766e;
  font-weight: 700;
  border-radius: 999px;
  background: #ccfbf1;
}

@media (max-width: 980px) {
  .knowledge-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .knowledge-page {
    gap: 14px;
  }

  .knowledge-hero,
  .knowledge-shell {
    border-radius: 20px;
    padding: 18px;
  }

  .hero-copy h1 {
    font-size: 32px;
  }

  .hero-metrics {
    grid-template-columns: 1fr;
  }

  .upload-tip {
    width: 100%;
    line-height: 1.6;
  }

  .section-head {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
