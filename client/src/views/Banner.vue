<template>
  <div class="page-container">
    <div class="search-bar">
      <el-button type="success" @click="openDialog()">新增轮播图</el-button>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" border stripe style="width:100%">
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="title" label="标题" min-width="120" />
        <el-table-column prop="image" label="图片" min-width="120">
          <template #default="{ row }">
            <el-image v-if="row.image" :src="row.image" style="width:80px;height:40px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="sort" label="排序" min-width="70" />
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

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑轮播图' : '新增轮播图'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="图片">
          <el-input v-model="form.image" placeholder="图片URL" />
          <el-upload :show-file-list="false" :http-request="handleUpload" accept="image/*" style="margin-top:8px">
            <el-button size="small">上传图片</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="form.status" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/** 轮播图管理页面 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBannerList, createBanner, updateBanner, deleteBanner } from '@/api/banner'
import { uploadImage } from '@/api/product'
import { formatDateTime } from '@/utils/date'

const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const editId = ref(null)
const query = reactive({ page: 1, page_size: 10 })
const form = reactive({ title: '', image: '', link_type: 0, link_id: 0, sort: 0, status: 1 })

async function loadData() {
  const res = await getBannerList(query)
  tableData.value = res.data.list
  total.value = res.data.total
}

function openDialog(row) {
  editId.value = row?.id || null
  if (row) Object.assign(form, row)
  else Object.assign(form, { title: '', image: '', link_type: 0, link_id: 0, sort: 0, status: 1 })
  dialogVisible.value = true
}

async function handleSave() {
  if (editId.value) await updateBanner(editId.value, form)
  else await createBanner(form)
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await deleteBanner(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleUpload({ file }) {
  const res = await uploadImage(file, 'banner')
  form.image = res.data.url
  ElMessage.success('上传成功')
}

onMounted(loadData)
</script>
