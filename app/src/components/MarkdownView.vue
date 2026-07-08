<template>
  <div class="md-body" v-html="html"></div>
</template>

<script setup>
import { computed } from 'vue'
import { parseMarkdown } from '@/utils/markdown'

const props = defineProps({
  content: { type: String, default: '' },
})
const html = computed(() => parseMarkdown(props.content))
</script>
