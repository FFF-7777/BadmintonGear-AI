<template>
  <div class="page-container">
    <div class="search-bar">
      <el-upload :show-file-list="false" :http-request="handleUpload" accept=".txt,.docx,.pdf,.md,.markdown">
        <el-button type="primary">上传知识库文件</el-button>
      </el-upload>
      <span style="color:#909399;font-size:13px">支持 txt / docx / pdf / markdown 格式，最大10MB</span>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" border stripe style="width:100%">
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="file_name" label="文件名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="file_type" label="类型" min-width="80" />
        <el-table-column prop="file_size" label="大小" min-width="100">
          <template #default="{ row }">{{ (row.file_size / 1024).toFixed(1) }} KB</template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块数" min-width="80" />
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : row.status === 2 ? 'danger' : 'info'">
              {{ knowledgeStatusMap[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error_msg" label="错误信息" min-width="150" show-overflow-tooltip />
        <el-table-column prop="create_time" label="上传时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="warning" link @click="handleVectorize(row)">重新向量化</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-bar">
      <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
        :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
    </div>
  </div>
</template>

<script setup>
/**
 * 知识库管理页面
 * 支持上传txt/docx/pdf/markdown文件并向量化到Chroma
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getKnowledgeList, uploadKnowledge, vectorizeKnowledge, deleteKnowledge } from '@/api/knowledge'
import { formatDateTime, knowledgeStatusMap } from '@/utils/date'

const tableData = ref([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10 })

async function loadData() {
  const res = await getKnowledgeList(query)
  tableData.value = res.data.list
  total.value = res.data.total
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
