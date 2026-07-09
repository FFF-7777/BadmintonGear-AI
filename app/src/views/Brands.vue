<template>
  <div class="page">
    <div class="page-head fade-up">
      <div class="head-copy">
        <span>Equipment Library</span>
        <h1>羽毛球装备品类库</h1>
        <p>按品牌和四个固定品类筛选热门装备。参考价只用于 AI 选品对比，帮助判断预算区间。</p>
      </div>

      <form class="gear-search" :class="{ active: keyword }" @submit.prevent>
        <span>⌕</span>
        <input v-model.trim="keyword" placeholder="搜索装备、品牌、参数" />
        <button v-if="keyword" type="button" aria-label="清空搜索" @click="keyword = ''">×</button>
      </form>
    </div>

    <div class="filters card">
      <div class="filter-row">
        <span class="filter-key">品牌</span>
        <div class="chip-wrap">
          <button class="chip" :class="{ on: !selBrand }" @click="selBrand = ''">全部</button>
          <button
            v-for="b in brands"
            :key="b.id"
            class="chip"
            :class="{ on: selBrand === b.id }"
            :style="selBrand === b.id ? { background: b.color, borderColor: b.color, color: '#fff' } : {}"
            @click="selBrand = b.id"
          >
            {{ b.nameCn }}
          </button>
        </div>
      </div>
      <div class="filter-row">
        <span class="filter-key">品类</span>
        <div class="chip-wrap">
          <button class="chip" :class="{ on: !selCat }" @click="selCat = ''">全部</button>
          <button
            v-for="c in categories"
            :key="c.id"
            class="chip"
            :class="{ on: selCat === c.id }"
            @click="selCat = c.id"
          >
            {{ c.icon }} {{ c.name }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="curBrand" class="brand-banner fade-up" :style="{ '--bc': curBrand.color }" @click="openBrand">
      <div class="bb-logo">
        <img :src="curBrand.logo" :alt="`${curBrand.name} logo`" />
      </div>
      <div class="bb-info">
        <div class="bb-name">{{ curBrand.nameCn }} <span>{{ curBrand.name }}</span></div>
        <div class="bb-sub">{{ curBrand.country }} · 创立于 {{ curBrand.founded }}</div>
        <div class="bb-desc">{{ curBrand.desc }}</div>
      </div>
      <span class="bb-arrow">品牌详情 ›</span>
    </div>

    <div class="result-head">
      <span>{{ resultText }}</span>
      <button v-if="selBrand || selCat || keyword" @click="reset">重置筛选</button>
    </div>

    <div v-if="pagedResults.length" class="kb-grid">
      <div v-for="(a, i) in pagedResults" :key="a.id" class="fade-up" :style="{ animationDelay: i * 40 + 'ms' }">
        <KnowledgeCard :article="a" />
      </div>
    </div>
    <div v-else class="empty-tip card">没有找到匹配装备，换个关键词或筛选条件试试。</div>

    <div v-if="totalPages > 1" class="pager">
      <button class="pg-btn" :disabled="currentPage === 1" @click="currentPage--">‹ 上一页</button>
      <span class="pg-info">第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ results.length }} 条</span>
      <button class="pg-btn" :disabled="currentPage === totalPages" @click="currentPage++">下一页 ›</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { brands, categories, getBrand } from '@/data/knowledge'
import { fetchProducts } from '@/api/product'
import KnowledgeCard from '@/components/KnowledgeCard.vue'

defineOptions({ name: 'Brands' })

const route = useRoute()
const router = useRouter()
const selBrand = ref('')
const selCat = ref('')
const keyword = ref('')
const products = ref([])

watchEffect(() => {
  const category = String(route.query.category || '')
  if (category && categories.some((c) => c.id === category)) selCat.value = category
})

const curBrand = computed(() => (selBrand.value ? getBrand(selBrand.value) : null))

const results = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return products.value.filter((item) => {
    if (selBrand.value && item.brandId !== selBrand.value) return false
    if (selCat.value && item.category !== selCat.value) return false
    if (kw && !searchPool(item).includes(kw)) return false
    return true
  })
})

// 客户端分页：每页 100 条
const pageSize = 100
const currentPage = ref(1)
const totalPages = computed(() => Math.max(1, Math.ceil(results.value.length / pageSize)))
const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return results.value.slice(start, start + pageSize)
})

// 筛选条件变化时回到第 1 页
watch([selBrand, selCat, keyword], () => {
  currentPage.value = 1
})

const resultText = computed(() => {
  const b = curBrand.value ? curBrand.value.nameCn : '全部品牌'
  const c = selCat.value ? categories.find((x) => x.id === selCat.value)?.name : '全部品类'
  const q = keyword.value ? ` · 搜索“${keyword.value}”` : ''
  return `${b} · ${c}${q} · ${results.value.length} 个装备条目`
})

function openBrand() {
  if (curBrand.value) router.push(`/brand/${curBrand.value.id}`)
}

function reset() {
  selBrand.value = ''
  selCat.value = ''
  keyword.value = ''
  router.replace('/brands')
}

function searchPool(item) {
  return [
    item.title,
    item.summary,
    item.priceRange,
    item.level,
    item.bestFor,
    item.category,
    item.tags?.join(' '),
    item.specs?.join(' '),
    item.raw?.category_name,
    item.raw?.description,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

onMounted(async () => {
  const res = await fetchProducts()
  products.value = res.list
})
</script>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
}

.page-head span {
  color: var(--primary-2);
  font-size: 12px;
  font-weight: 900;
}

.page-head h1 {
  margin: 4px 0 8px;
  font-size: 36px;
  line-height: 1.15;
  font-weight: 950;
}

.page-head p {
  max-width: 680px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.75;
}

.gear-search {
  width: min(360px, 36vw);
  height: 48px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto;
  margin-top: 18px;
  padding: 0 12px 0 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(18px);
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
}

.gear-search:focus-within,
.gear-search.active {
  transform: translateY(-1px);
  border-color: rgba(34, 211, 238, 0.62);
  box-shadow: 0 0 0 5px rgba(34, 211, 238, 0.11), var(--shadow-md);
}

.gear-search span {
  color: var(--text-tertiary);
  font-size: 18px;
  font-weight: 900;
}

.gear-search input {
  flex: 1;
  min-width: 0;
  color: var(--text-primary);
  border: 0;
  outline: 0;
  background: transparent;
}

.gear-search button {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  color: var(--text-tertiary);
  border: 0;
  border-radius: 50%;
  background: rgba(226, 232, 240, 0.72);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 20px;
}

.filter-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.filter-key {
  flex: 0 0 44px;
  padding-top: 9px;
  color: var(--text-secondary);
  font-weight: 850;
}

.chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.brand-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 18px;
  padding: 18px 20px;
  cursor: pointer;
  border: 1px solid var(--border-color);
  border-left: 5px solid var(--bc, var(--primary-2));
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.bb-logo {
  width: 150px;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  overflow: visible;
  background: transparent;
}

.bb-logo img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

.bb-info {
  flex: 1;
  min-width: 0;
}

.bb-name {
  font-size: 18px;
  font-weight: 900;
}

.bb-name span,
.bb-sub,
.bb-desc {
  color: var(--text-secondary);
}

.bb-name span {
  font-size: 13px;
  font-weight: 700;
}

.bb-sub {
  margin: 3px 0 6px;
  font-size: 12px;
}

.bb-desc {
  line-height: 1.65;
}

.bb-arrow {
  color: var(--primary-2);
  font-weight: 900;
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 24px 2px 14px;
}

.result-head span {
  font-weight: 900;
}

.result-head button {
  color: var(--text-tertiary);
  border: 0;
  background: transparent;
  cursor: pointer;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 26px 0 8px;
}

.pg-btn {
  height: 40px;
  padding: 0 20px;
  color: var(--text-primary);
  font-weight: 850;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease, opacity 0.16s ease;
}

.pg-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(34, 211, 238, 0.62);
  box-shadow: 0 0 0 5px rgba(34, 211, 238, 0.11), var(--shadow-md);
}

.pg-btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.pg-info {
  color: var(--text-secondary);
  font-weight: 850;
  white-space: nowrap;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 1100px) {
  .kb-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 760px) {
  .page-head {
    flex-direction: column;
  }

  .gear-search {
    width: 100%;
    margin-top: 0;
  }

  .filter-row {
    flex-direction: column;
    gap: 8px;
  }

  .kb-grid {
    grid-template-columns: 1fr;
  }
}
</style>
