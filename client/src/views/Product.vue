<template>
  <div class="page-container">
    <div class="search-bar">
      <el-input v-model="query.keyword" placeholder="搜索装备名称" clearable style="width:200px" @clear="loadData" />
      <el-select v-model="query.category_id" placeholder="分类" clearable style="width:150px" @change="loadData">
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button type="primary" @click="loadData">搜索</el-button>
      <el-button type="success" @click="openDialog()">新增装备</el-button>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" border stripe style="width:100%">
        <el-table-column prop="id" label="ID" min-width="60" />
        <el-table-column prop="image" label="图片" min-width="80">
          <template #default="{ row }">
            <el-image v-if="row.image" :src="row.image" style="width:50px;height:50px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="装备名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" min-width="100" />
        <el-table-column prop="price" label="价格" min-width="80">
          <template #default="{ row }">¥{{ row.price }}</template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" min-width="70" />
        <el-table-column prop="sales" label="销量" min-width="70" />
        <el-table-column prop="status" label="状态" min-width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '上架' : '下架' }}</el-tag>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑装备' : '新增装备'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category_id" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="价格"><el-input-number v-model="form.price" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="库存"><el-input-number v-model="form.stock" :min="0" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="图片">
          <el-input v-model="form.image" placeholder="图片URL" />
          <el-upload :show-file-list="false" :http-request="handleUpload" accept="image/*" style="margin-top:8px">
            <el-button size="small">上传图片</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="上架" inactive-text="下架" />
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
/**
 * 装备管理页面
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProductList, createProduct, updateProduct, deleteProduct, uploadImage } from '@/api/product'
import { getAllCategories } from '@/api/category'
import { formatDateTime } from '@/utils/date'

const tableData = ref([])
const total = ref(0)
const categories = ref([])
const dialogVisible = ref(false)
const editId = ref(null)
const query = reactive({ page: 1, page_size: 10, keyword: '', category_id: null })
const form = reactive({ name: '', category_id: null, price: 0, stock: 0, description: '', image: '', status: 1 })

async function loadData() {
  const res = await getProductList(query)
  tableData.value = res.data.list
  total.value = res.data.total
}

async function loadCategories() {
  const res = await getAllCategories()
  categories.value = res.data
}

function openDialog(row) {
  editId.value = row?.id || null
  if (row) {
    Object.assign(form, { name: row.name, category_id: row.category_id, price: Number(row.price), stock: row.stock, description: row.description, image: row.image, status: row.status })
  } else {
    Object.assign(form, { name: '', category_id: categories.value[0]?.id, price: 0, stock: 0, description: '', image: '', status: 1 })
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (editId.value) {
    await updateProduct(editId.value, form)
  } else {
    await createProduct(form)
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该装备？', '提示', { type: 'warning' })
  await deleteProduct(row.id)
  ElMessage.success('删除成功')
  loadData()
}

async function handleUpload({ file }) {
  const res = await uploadImage(file)
  form.image = res.data.url
  ElMessage.success('上传成功')
}

onMounted(() => { loadCategories(); loadData() })
</script>
