<template>
  <div class="page-container">
    <div class="search-bar">
      <el-input v-model="query.keyword" placeholder="搜索分类名称" clearable style="width:200px" @clear="loadData" />
      <el-button type="primary" @click="loadData">搜索</el-button>
      <el-button type="success" @click="openDialog()">新增分类</el-button>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" border stripe style="width:100%">
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="name" label="分类名称" min-width="150" />
        <el-table-column prop="sort" label="排序" min-width="80" />
        <el-table-column prop="status" label="状态" min-width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-bar">
      <el-pagination v-model:current-page="query.page" v-model:page-size="query.page_size"
        :total="total" layout="total, sizes, prev, pager, next" @change="loadData" />
    </div>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑分类' : '新增分类'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/** 分类管理页面 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCategoryList, createCategory, updateCategory, deleteCategory } from '@/api/category'
import { formatDateTime } from '@/utils/date'

const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const editId = ref(null)
const query = reactive({ page: 1, page_size: 10, keyword: '' })
const form = reactive({ name: '', sort: 0, status: 1 })

async function loadData() {
  const res = await getCategoryList(query)
  tableData.value = res.data.list
  total.value = res.data.total
}

function openDialog(row) {
  editId.value = row?.id || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { name: '', sort: 0, status: 1 })
  dialogVisible.value = true
}

async function handleSave() {
  if (editId.value) await updateCategory(editId.value, form)
  else await createCategory(form)
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await deleteCategory(row.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
