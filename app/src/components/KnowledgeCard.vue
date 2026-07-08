<template>
  <article class="kb-card" @click="open">
    <div class="kb-cover">
      <img v-if="article.image" :src="article.image" :alt="article.title" loading="lazy" />
      <div v-else class="kb-fallback">{{ catIcon }}</div>
      <div class="kb-sheen"></div>
    </div>

    <div class="kb-content">
      <div class="kb-card-top">
        <span class="kb-cat">{{ catIcon }} {{ catName }}</span>
        <span v-if="brandLabel" class="kb-brand">
          {{ brandLabel }}
        </span>
      </div>

      <div class="kb-title">{{ article.title }}</div>
      <div class="kb-summary">{{ article.summary }}</div>

      <div v-if="article.specs?.length" class="spec-list">
        <span v-for="s in article.specs.slice(0, 3)" :key="s">{{ s }}</span>
      </div>

      <div v-if="article.tags?.length" class="tag-list">
        <span v-for="tag in article.tags.slice(0, 3)" :key="tag">#{{ tag }}</span>
      </div>

      <div class="kb-foot">
        <span class="kb-price">参考价 {{ article.priceRange }}</span>
        <span class="kb-arrow">查看详情</span>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { getBrand, getCategory } from '@/data/knowledge'

const props = defineProps({
  article: { type: Object, required: true },
})

const router = useRouter()

const cat = computed(() => getCategory(props.article.category))
const catIcon = computed(() => (cat.value ? cat.value.icon : '🏸'))
const catName = computed(() => (cat.value ? cat.value.name : '装备'))
const brand = computed(() => (props.article.brandId ? getBrand(props.article.brandId) : null))
const brandLabel = computed(() => brand.value?.nameCn || props.article.brand || '')

function open() {
  router.push(`/article/${props.article.id}`)
}
</script>

<style scoped>
.kb-card {
  height: 100%;
  display: grid;
  grid-template-rows: 210px 1fr;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.78);
  border-radius: 30px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 251, 255, 0.76)),
    linear-gradient(135deg, rgba(214, 255, 127, 0.18), rgba(110, 231, 249, 0.10), rgba(255, 176, 199, 0.14));
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.10);
  backdrop-filter: blur(22px) saturate(1.12);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.kb-card:hover {
  transform: translateY(-4px);
  border-color: rgba(110, 231, 249, 0.64);
  box-shadow: 0 30px 74px rgba(15, 23, 42, 0.14);
}

.kb-cover {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 22% 18%, rgba(255, 255, 255, 0.76), transparent 28%),
    linear-gradient(135deg, rgba(8, 18, 34, 0.9), rgba(17, 38, 60, 0.78));
}

.kb-cover img,
.kb-fallback {
  width: 100%;
  height: 100%;
}

.kb-cover img {
  display: block;
  object-fit: cover;
}

.kb-fallback {
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.92);
  font-size: 42px;
}

.kb-sheen {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, transparent 46%, rgba(8, 18, 34, 0.12)),
    radial-gradient(circle at 84% 20%, rgba(110, 231, 249, 0.22), transparent 26%);
  pointer-events: none;
}

.kb-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 18px 20px;
}

.kb-card-top,
.kb-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.kb-cat,
.kb-brand,
.spec-list span,
.tag-list span {
  border-radius: 999px;
  font-weight: 850;
}

.kb-cat {
  padding: 6px 10px;
  color: #0f766e;
  background: rgba(204, 251, 241, 0.9);
  font-size: 11px;
}

.kb-brand {
  padding: 6px 10px;
  color: #334155;
  background: rgba(241, 245, 249, 0.9);
  font-size: 11px;
}

.kb-title {
  color: #08111f;
  font-size: 19px;
  line-height: 1.35;
  font-weight: 950;
}

.kb-summary {
  flex: 1;
  color: #55657a;
  font-size: 14px;
  line-height: 1.74;
}

.spec-list,
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spec-list span {
  padding: 6px 10px;
  color: #0f172a;
  background: rgba(236, 253, 245, 0.92);
  font-size: 12px;
}

.tag-list span {
  padding: 5px 9px;
  color: #0f698a;
  background: rgba(224, 242, 254, 0.92);
  font-size: 11px;
}

.kb-price {
  color: #be123c;
  font-size: 14px;
  font-weight: 950;
}

.kb-arrow {
  color: #0f698a;
  font-size: 12px;
  font-weight: 900;
}
</style>
