<template>
  <div class="page" v-if="brand">
    <section class="brand-hero fade-up" :style="{ '--bc': brand.color }">
      <div class="bh-inner">
        <div class="bh-logo">
          <img :src="brand.logo" :alt="`${brand.name} logo`" />
        </div>
        <div class="bh-meta">
          <span>Brand Profile</span>
          <h1>{{ brand.nameCn }} <em>{{ brand.name }}</em></h1>
          <p>{{ brand.slogan }}</p>
          <div class="bh-tags">
            <span v-for="t in brand.tags" :key="t">{{ t }}</span>
          </div>
        </div>
        <button class="btn-primary bh-ask" @click="goQa">问 AI 对比 {{ brand.nameCn }}</button>
      </div>
    </section>

    <div class="bh-desc card">
      <b>{{ brand.country }} · 创立于 {{ brand.founded }}</b>
      <p>{{ brand.desc }}</p>
    </div>

    <div class="section-head">
      <h2>{{ brand.nameCn }} 相关装备</h2>
      <span class="sub">{{ list.length }} 个条目 · 参考价仅用于对比</span>
    </div>

    <div v-if="list.length" class="kb-grid">
      <div v-for="(a, i) in list" :key="a.id" class="fade-up" :style="{ animationDelay: i * 45 + 'ms' }">
        <KnowledgeCard :article="a" />
      </div>
    </div>
    <div v-else class="empty-tip card">该品牌暂无装备条目，管理员可在后台继续维护知识库。</div>
  </div>
  <div v-else class="empty-tip">未找到该品牌</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBrand } from '@/data/knowledge'
import { fetchProducts } from '@/api/product'
import KnowledgeCard from '@/components/KnowledgeCard.vue'

const route = useRoute()
const router = useRouter()
const products = ref([])

const brand = computed(() => getBrand(route.params.id))
const list = computed(() => (brand.value ? products.value.filter((item) => item.brandId === brand.value.id) : []))

function goQa() {
  if (brand.value) router.push(`/chat?brand=${brand.value.id}`)
}

onMounted(async () => {
  const res = await fetchProducts()
  products.value = res.list
})
</script>

<style scoped>
.brand-hero {
  position: relative;
  overflow: hidden;
  padding: 38px 42px;
  color: #fff;
  border-radius: 32px;
  background:
    radial-gradient(circle at 82% 18%, rgba(255, 255, 255, 0.24), transparent 24%),
    linear-gradient(135deg, var(--bc, #0f172a), #0f172a);
  box-shadow: var(--shadow-lg);
}

.bh-inner {
  display: flex;
  align-items: center;
  gap: 24px;
}

.bh-logo {
  width: 190px;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 14px;
  overflow: visible;
  background: rgba(255, 255, 255, 0.12);
}

.bh-logo img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

.bh-meta {
  flex: 1;
  min-width: 0;
}

.bh-meta span {
  color: rgba(255, 255, 255, 0.66);
  font-size: 12px;
  font-weight: 900;
}

.bh-meta h1 {
  margin: 5px 0 8px;
  font-size: 34px;
  line-height: 1.15;
}

.bh-meta em {
  color: rgba(255, 255, 255, 0.72);
  font-style: normal;
  font-size: 16px;
}

.bh-meta p {
  margin: 0;
  color: rgba(255, 255, 255, 0.78);
}

.bh-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.bh-tags span {
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 12px;
}

.bh-ask {
  flex: 0 0 auto;
}

.bh-desc {
  margin-top: 18px;
  padding: 20px 22px;
}

.bh-desc b {
  display: block;
  margin-bottom: 8px;
}

.bh-desc p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 1000px) {
  .kb-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 760px) {
  .bh-inner {
    align-items: flex-start;
    flex-direction: column;
  }

  .kb-grid {
    grid-template-columns: 1fr;
  }
}
</style>
