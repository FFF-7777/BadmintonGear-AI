<template>
  <div class="page-container">
    <div class="search-bar">
      <el-input v-model="query.keyword" placeholder="搜索用户名/手机号" clearable style="width:200px" @clear="loadData" />
      <el-button type="primary" @click="loadData">搜索</el-button>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" border stripe style="width:100%">
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="phone" label="手机号" min-width="130" />
        <el-table-column prop="nickname" label="昵称" min-width="100" />
        <el-table-column prop="status" label="状态" min-width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 1" type="danger" link @click="toggleStatus(row, 0)">禁用</el-button>
            <el-button v-else type="success" link @click="toggleStatus(row, 1)">启用</el-button>
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
/** 用户管理页面 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getUserList, updateUserStatus } from '@/api/user'
import { formatDateTime } from '@/utils/date'

const tableData = ref([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '' })

async function loadData() {
  const res = await getUserList(query)
  tableData.value = res.data.list
  total.value = res.data.total
}

async function toggleStatus(row, status) {
  await updateUserStatus(row.id, status)
  ElMessage.success('操作成功')
  loadData()
}

onMounted(loadData)
</script>
