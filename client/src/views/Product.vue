<template>
  <div class="page-container">
    <div class="search-bar">
      <el-input v-model="query.keyword" placeholder="搜索装备名称" clearable style="width: 220px" @clear="loadData" />
      <el-select v-model="query.category_id" placeholder="品类" clearable style="width: 160px" @change="loadData">
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button type="primary" @click="loadData">搜索</el-button>
      <el-button type="success" @click="openDialog()">新增装备</el-button>
      <el-select v-model="importCategoryId" placeholder="导入品类" style="width: 160px">
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-button @click="handleDownloadTemplate">下载模板</el-button>
      <el-upload :show-file-list="false" accept=".xlsx,.csv" :http-request="handleImport">
        <el-button type="warning">导入 Excel/CSV</el-button>
      </el-upload>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="id" label="ID" min-width="64" />
        <el-table-column prop="image" label="图片" min-width="86">
          <template #default="{ row }">
            <el-image v-if="row.image" :src="row.image" style="width: 50px; height: 50px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="装备名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="brand" label="品牌" min-width="100" show-overflow-tooltip />
        <el-table-column prop="series" label="系列" min-width="110" show-overflow-tooltip />
        <el-table-column prop="category_name" label="品类" min-width="100" />
        <el-table-column prop="price" label="参考价" min-width="100">
          <template #default="{ row }">¥{{ row.price }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="88">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" min-width="168">
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
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @change="loadData"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑装备' : '新增装备'" width="600px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="品牌"><el-input v-model="form.brand" placeholder="如 YONEX / LI-NING" /></el-form-item>
        <el-form-item label="系列"><el-input v-model="form.series" placeholder="如 天斧 / 战戟 / 65Z" /></el-form-item>
        <el-form-item label="别名"><el-input v-model="form.model_aliases_text" placeholder="逗号分隔，如 AX77PRO, ASTROX 77 PRO" /></el-form-item>
        <el-form-item label="品类">
          <el-select v-model="form.category_id" style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="参考价"><el-input-number v-model="form.price" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="标签"><el-input v-model="form.manual_tags_text" placeholder="逗号分隔，如 进攻,新手友好" /></el-form-item>
        <el-form-item label="来源链接"><el-input v-model="form.source_url" placeholder="可选" /></el-form-item>
        <el-form-item label="来源备注"><el-input v-model="form.source_note" placeholder="如 品牌页 / 实测表" /></el-form-item>
        <el-form-item label="图片">
          <el-input v-model="form.image" placeholder="图片 URL" />
          <el-upload :show-file-list="false" :http-request="handleUpload" accept="image/*" style="margin-top: 8px">
            <el-button size="small">上传图片</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createProduct, deleteProduct, downloadImportTemplate, getProductList, importProducts, updateProduct, uploadImage } from '@/api/product'
import { getAllCategories } from '@/api/category'
import { formatDateTime } from '@/utils/date'

const tableData = ref([])
const total = ref(0)
const categories = ref([])
const dialogVisible = ref(false)
const editId = ref(null)
const importCategoryId = ref(null)
const query = reactive({ page: 1, page_size: 10, keyword: '', category_id: null })
const form = reactive({
  name: '',
  brand: '',
  series: '',
  model_aliases_text: '',
  category_id: null,
  price: 0,
  description: '',
  manual_tags_text: '',
  image: '',
  source_url: '',
  source_note: '',
  status: 1,
})

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
    Object.assign(form, {
      name: row.name,
      brand: row.brand || '',
      series: row.series || '',
      model_aliases_text: (row.model_aliases || []).join(', '),
      category_id: row.category_id,
      price: Number(row.price),
      description: row.description,
      manual_tags_text: (row.manual_tags || []).join(', '),
      image: row.image,
      source_url: row.source_url || '',
      source_note: row.source_note || '',
      status: row.status,
    })
  } else {
    Object.assign(form, {
      name: '',
      brand: '',
      series: '',
      model_aliases_text: '',
      category_id: categories.value[0]?.id,
      price: 0,
      description: '',
      manual_tags_text: '',
      image: '',
      source_url: '',
      source_note: '',
      status: 1,
    })
  }
  dialogVisible.value = true
}

async function handleSave() {
  const payload = {
    ...form,
    model_aliases: splitTextList(form.model_aliases_text),
    manual_tags: splitTextList(form.manual_tags_text),
  }
  delete payload.model_aliases_text
  delete payload.manual_tags_text
  if (editId.value) {
    await updateProduct(editId.value, payload)
  } else {
    await createProduct(payload)
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

async function handleImport({ file }) {
  if (!importCategoryId.value) {
    ElMessage.warning('请先选择导入品类')
    return
  }
  const res = await importProducts(file, importCategoryId.value)
  const data = res.data
  ElMessage.success(`导入完成：成功 ${data.success_count} 条，失败 ${data.error_count} 条`)
  loadData()
}

async function handleDownloadTemplate() {
  if (!importCategoryId.value) {
    ElMessage.warning('请先选择导入品类')
    return
  }
  const response = await downloadImportTemplate(importCategoryId.value)
  const blob = new Blob([response.data], { type: response.headers['content-type'] })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `product-import-template-${importCategoryId.value}.xlsx`
  link.click()
  URL.revokeObjectURL(url)
}

function splitTextList(text) {
  return String(text || '')
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>
