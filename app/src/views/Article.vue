<template>
  <div class="page article-page" v-if="article">
    <div class="crumb">
      <span @click="go('/brands')">装备库</span>
      <span>/</span>
      <span @click="go(brand ? `/brand/${brand.id}` : '/brands')">{{ brand ? brand.nameCn : '通用' }}</span>
      <span>/</span>
      <b>{{ article.title }}</b>
    </div>

    <section class="product-hero">
      <div class="product-media">
        <img v-if="article.image" :src="article.image" :alt="article.title" />
        <div class="media-shine"></div>
      </div>

      <div class="product-panel">
        <div class="eyebrow">
          <span>{{ catIcon }} {{ catName }}</span>
          <span v-if="brand" class="brand-pill" :style="{ color: brand.color }">{{ brand.nameCn }}</span>
        </div>
        <h1>{{ article.title }}</h1>
        <p>{{ article.summary }}</p>

        <div class="metric-grid">
          <div>
            <span>参考价</span>
            <b>{{ article.priceRange }}</b>
          </div>
          <div>
            <span>适合阶段</span>
            <b>{{ article.level }}</b>
          </div>
          <div>
            <span>适合场景</span>
            <b>{{ article.bestFor }}</b>
          </div>
        </div>

        <div class="art-meta">
          <span>{{ article.updated || '最近' }} 更新</span>
          <span>价格仅用于选品对比</span>
        </div>
      </div>
    </section>

    <section class="detail-grid">
      <div class="glass-card spec-card">
        <div class="block-head">
          <span>Specs</span>
          <h2>关键参数</h2>
        </div>
        <div class="spec-list">
          <span v-for="s in article.specs" :key="s">{{ s }}</span>
        </div>
      </div>

    </section>

    <div class="art-tags">
      <span v-for="t in article.tags" :key="t" class="ios-badge ios-badge--primary">#{{ t }}</span>
    </div>

    <div class="section-head">
      <h2>相关对比</h2>
      <span class="sub">同品牌或同品类装备</span>
    </div>
    <div v-if="related.length" class="kb-grid">
      <div v-for="a in related" :key="a.id">
        <KnowledgeCard :article="a" />
      </div>
    </div>
    <div v-else class="empty-tip">暂无相关装备</div>
  </div>
  <div v-else class="empty-tip">未找到该装备条目</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBrand, getCategory } from '@/data/knowledge'
import { fetchProductDetail, fetchProducts } from '@/api/product'
import KnowledgeCard from '@/components/KnowledgeCard.vue'

const route = useRoute()
const router = useRouter()
const article = ref(null)
const products = ref([])

const cat = computed(() => (article.value ? getCategory(article.value.category) : null))
const catIcon = computed(() => (cat.value ? cat.value.icon : '🏸'))
const catName = computed(() => (cat.value ? cat.value.name : '装备'))
const brand = computed(() => (article.value && article.value.brandId ? getBrand(article.value.brandId) : null))

const related = computed(() => {
  if (!article.value) return []
  return products.value
    .filter((a) => a.id !== article.value.id && (a.category === article.value.category || a.brandId === article.value.brandId))
    .slice(0, 3)
})

function go(p) {
  router.push(p)
}

onMounted(async () => {
  article.value = await fetchProductDetail(route.params.id)
  const res = await fetchProducts()
  products.value = res.list
})
</script>

<style scoped>
.article-page {
  max-width: 1120px;
}

.crumb {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.crumb span {
  cursor: pointer;
}

.crumb span:hover {
  color: var(--primary-2);
}

.crumb b {
  color: var(--text-secondary);
  font-weight: 800;
}

.product-hero {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(0, 1.1fr);
  gap: 18px;
  padding: 18px;
  border: 1px solid rgba(255, 255, 255, 0.76);
  border-radius: 34px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.88), rgba(236, 254, 255, 0.68)),
    linear-gradient(120deg, rgba(217, 249, 157, 0.3), rgba(103, 232, 249, 0.18), rgba(253, 164, 175, 0.2));
  box-shadow: var(--shadow-lg);
}

.product-media {
  position: relative;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7);
}

.product-media img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

.media-shine {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 18%, rgba(255, 255, 255, 0.42), transparent 28%),
    linear-gradient(180deg, transparent 45%, rgba(15, 23, 42, 0.08));
  pointer-events: none;
}

.product-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 28px;
}

.eyebrow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.eyebrow span {
  padding: 7px 11px;
  color: #0f766e;
  border-radius: 999px;
  background: rgba(204, 251, 241, 0.88);
  font-size: 12px;
  font-weight: 950;
}

.eyebrow .brand-pill {
  background: rgba(255, 255, 255, 0.76);
}

.product-panel h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 44px;
  line-height: 1.08;
  font-weight: 950;
  letter-spacing: 0;
}

.product-panel p {
  max-width: 620px;
  margin: 14px 0 24px;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.8;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.metric-grid div {
  min-height: 92px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.66);
  box-shadow: var(--shadow-sm);
}

.metric-grid span,
.metric-grid b {
  display: block;
}

.metric-grid span {
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 850;
}

.metric-grid b {
  margin-top: 8px;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 950;
}

.art-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
  color: var(--text-tertiary);
  font-size: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr;
  gap: 18px;
  margin-top: 18px;
}

.glass-card {
  border: 1px solid rgba(255, 255, 255, 0.76);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(18px);
}

.spec-card,
.art-body {
  padding: 24px;
}

.block-head span {
  color: var(--primary-2);
  font-size: 12px;
  font-weight: 950;
}

.block-head h2 {
  margin: 4px 0 16px;
  font-size: 22px;
  line-height: 1.2;
  font-weight: 950;
}

.spec-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.spec-list span {
  padding: 8px 12px;
  color: #0f766e;
  border-radius: 999px;
  background: #ccfbf1;
  font-weight: 850;
}

.art-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 18px 0 4px;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

@media (max-width: 980px) {
  .product-hero,
  .detail-grid,
  .metric-grid,
  .kb-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .product-hero {
    padding: 12px;
    border-radius: 26px;
  }

  .product-panel {
    padding: 18px 8px 10px;
  }

  .product-panel h1 {
    font-size: 30px;
  }

  .product-media {
    border-radius: 22px;
  }
}
</style>
