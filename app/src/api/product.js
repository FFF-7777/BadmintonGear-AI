import axios from 'axios'
import { brands, categories } from '@/data/knowledge'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

const brandAliases = {
  yonex: ['YONEX', '尤尼克斯', 'YY'],
  lining: ['LI-NING', '李宁', 'LINING'],
  victor: ['VICTOR', '胜利', '维克多'],
  kawasaki: ['KAWASAKI', '川崎'],
  kumpoo: ['KUMPOO', '薰风'],
  kason: ['KASON', '凯胜'],
}

function unwrap(res) {
  if (res.data?.code !== 200) {
    throw new Error(res.data?.msg || '请求失败')
  }
  return res.data.data
}

export async function fetchProducts(params = {}) {
  const data = unwrap(await http.get('/product/list', { params: { page: 1, page_size: 100, ...params } }))
  return {
    list: (data.list || []).map(normalizeProduct),
    total: data.total || 0,
  }
}

export async function fetchProductDetail(id) {
  const data = unwrap(await http.get(`/product/detail/${id}`))
  return normalizeProduct(data)
}

export function normalizeProduct(product) {
  const specs = product.specs && typeof product.specs === 'object' ? product.specs : {}
  const brandId = detectBrand(product, specs)
  const category = getCategoryKey(product.category_name)
  const specList = buildSpecList(specs)
  const tags = [
    ...(Array.isArray(product.tags) ? product.tags : []),
    ...(Array.isArray(product.manual_tags) ? product.manual_tags : []),
    product.category_name,
    brandName(brandId),
  ].filter(Boolean)

  return {
    id: product.id,
    brandId,
    brand: product.brand || specs.brand || brandName(brandId) || '',
    series: product.series || '',
    category,
    title: product.name,
    summary: product.description || '管理员维护的装备条目，可用于预算、参数和选品对比。',
    priceRange: formatPrice(product.price),
    level: specs.level || specs.stage || specs.usage || '装备对比',
    bestFor: specs.best_for || specs.bestFor || product.category_name || '羽毛球装备选品',
    specs: specList.length ? specList.slice(0, 4) : [product.category_name || '装备', brandName(brandId) || '通用'],
    tags: [...new Set(tags)],
    image: product.image || '',
    updated: product.create_time ? String(product.create_time).slice(0, 10) : '',
    content: product.description || '',
    raw: product,
  }
}

function buildSpecList(specs) {
  return [
    specs.weight_class && `${specs.weight_class} 重量`,
    specs.balance && balanceLabel(specs.balance),
    specs.shaft_flex && shaftLabel(specs.shaft_flex),
    specs.gauge && `线径 ${specs.gauge}`,
    specs.speed && `${specs.speed} 速`,
    specs.cushion_score && `缓震 ${specs.cushion_score}`,
    specs.support_score && `支撑 ${specs.support_score}`,
    specs.width_fit && widthLabel(specs.width_fit),
    specs.usage_scene && String(specs.usage_scene),
    specs.highlight && String(specs.highlight),
  ].filter(Boolean)
}

function detectBrand(product, specs) {
  const pool = [product.name, product.description, product.brand, product.series, specs.brand, specs.Brand, specs.品牌]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

  return Object.entries(brandAliases).find(([, aliases]) =>
    aliases.some((alias) => pool.includes(alias.toLowerCase()))
  )?.[0] || ''
}

function getCategoryKey(name) {
  return categories.find((item) => item.name === name)?.id || 'racket'
}

function brandName(id) {
  return brands.find((item) => item.id === id)?.nameCn || ''
}

function formatPrice(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '¥0'
  return `¥${n.toFixed(n % 1 === 0 ? 0 : 2)}`
}

function balanceLabel(value) {
  const map = {
    'head-heavy': '头重进攻',
    'head-light': '头轻速度',
    'even-balanced': '均衡控制',
  }
  return map[value] || String(value)
}

function shaftLabel(value) {
  const map = {
    flexible: '中软杆',
    medium: '中杆适中',
    stiff: '中硬杆',
    'extra-stiff': '高硬杆',
  }
  return map[value] || String(value)
}

function widthLabel(value) {
  const map = {
    wide: '宽脚友好',
    'wide-friendly': '宽脚友好',
    regular: '标准鞋楦',
  }
  return map[value] || String(value)
}
