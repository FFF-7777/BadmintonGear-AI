<template>
  <div class="page-container">
    <div class="search-bar">
      <el-input v-model="query.keyword" placeholder="搜索订单号" clearable style="width:200px" @clear="loadData" />
      <el-select v-model="query.status" placeholder="订单状态" clearable style="width:150px" @change="loadData">
        <el-option v-for="(label, val) in orderStatusMap" :key="val" :label="label" :value="Number(val)" />
      </el-select>
      <el-button type="primary" @click="loadData">搜索</el-button>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" border stripe style="width:100%">
        <el-table-column prop="order_no" label="订单号" min-width="160" />
        <el-table-column prop="username" label="用户" min-width="100" />
        <el-table-column prop="pay_amount" label="实付金额" min-width="100">
          <template #default="{ row }">¥{{ row.pay_amount }}</template>
        </el-table-column>
        <el-table-column prop="status" label="订单状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="orderStatusTagType[row.status]" effect="light" round>
              {{ orderStatusMap[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="receiver_name" label="收货人" min-width="80" />
        <el-table-column prop="receiver_phone" label="电话" min-width="120" />
        <el-table-column prop="receiver_address" label="地址" min-width="180" show-overflow-tooltip />
        <el-table-column prop="create_time" label="下单时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="240" fixed="right">
          <template #default="{ row }">
            <div v-if="getStatusActions(row.status).length" class="action-btns">
              <el-button
                v-for="action in getStatusActions(row.status)"
                :key="action.status"
                :type="action.type"
                size="small"
                @click="handleStatus(row, action.status)"
              >{{ action.label }}</el-button>
            </div>
            <span v-else class="no-action">—</span>
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
/** 订单管理页面 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getOrderList, updateOrderStatus } from '@/api/order'
import { formatDateTime, orderStatusMap } from '@/utils/date'

const orderStatusTagType = {
  0: 'warning',
  1: 'primary',
  2: 'info',
  3: 'success',
  4: 'danger',
}

const statusActionsMap = {
  0: [
    { status: 1, label: '确认支付', type: 'success' },
    { status: 4, label: '取消订单', type: 'danger' },
  ],
  1: [
    { status: 2, label: '发货', type: 'primary' },
    { status: 4, label: '取消订单', type: 'danger' },
  ],
  2: [{ status: 3, label: '完成', type: 'success' }],
  3: [],
  4: [],
}

function getStatusActions(status) {
  return statusActionsMap[status] || []
}

const tableData = ref([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '', status: null })

async function loadData() {
  const res = await getOrderList(query)
  tableData.value = res.data.list
  total.value = res.data.total
}

async function handleStatus(row, status) {
  await updateOrderStatus(row.id, status)
  ElMessage.success('状态更新成功')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.action-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}

.no-action {
  color: #c0c4cc;
}
</style>
