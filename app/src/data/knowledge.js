export const brands = [
  {
    id: 'yonex',
    name: 'YONEX',
    nameCn: '尤尼克斯',
    country: '日本',
    founded: 1946,
    color: '#0a3a7a',
    logo: '/assets/brands/yonex-native.png',
    slogan: '职业赛场标杆，参数体系完整',
    desc: '覆盖球拍、球线、羽毛球与球鞋的头部品牌，适合用作高端产品对比基准。',
    tags: ['高端', '职业', '参数完整'],
  },
  {
    id: 'lining',
    name: 'LI-NING',
    nameCn: '李宁',
    country: '中国',
    founded: 1990,
    color: '#e60012',
    logo: '/assets/brands/lining-native.png',
    slogan: '国羽体系，产品线完整',
    desc: '球拍系列分工清晰，球鞋缓震与包裹表现突出，适合进阶与比赛人群。',
    tags: ['国羽', '进阶', '鞋款强'],
  },
  {
    id: 'victor',
    name: 'VICTOR',
    nameCn: '胜利',
    country: '中国台湾',
    founded: 1968,
    color: '#c8102e',
    logo: '/assets/brands/victor-native.png',
    slogan: '速度与性价比兼顾',
    desc: '神速、突击、驭等系列覆盖速度、进攻与稳定打法，双打玩家关注度高。',
    tags: ['双打', '速度', '性价比'],
  },
  {
    id: 'kawasaki',
    name: 'KAWASAKI',
    nameCn: '川崎',
    country: '日本 / 中国',
    founded: 1915,
    color: '#d4001a',
    logo: '/assets/brands/kawasaki.svg',
    slogan: '入门友好，预算压力小',
    desc: '入门到进阶款丰富，适合作为新手第一套装备的预算对比项。',
    tags: ['入门', '亲民', '耐用'],
  },
  {
    id: 'kumpoo',
    name: 'KUMPOO',
    nameCn: '薰风',
    country: '日本',
    founded: 2001,
    color: '#6f42c1',
    logo: '/assets/brands/kumpoo-native.png',
    slogan: '轻量速度，小众灵活',
    desc: '轻量球拍与球鞋有鲜明特色，适合喜欢灵活手感和差异化选择的用户。',
    tags: ['小众', '轻量', '灵活'],
  },
  {
    id: 'kason',
    name: 'KASON',
    nameCn: '凯胜',
    country: '中国',
    founded: 1991,
    color: '#005bac',
    logo: '/assets/brands/kason-native.png',
    slogan: '稳定耐用，训练实用',
    desc: '训练和入门装备性价比高，适合预算明确、追求稳定耐用的用户。',
    tags: ['训练', '稳定', '耐用'],
  },
]

export const categories = [
  { id: 'racket', name: '球拍', icon: '🏸', desc: '按重量、平衡点、中杆硬度和打法选择。' },
  { id: 'string', name: '球线', icon: '〰️', desc: '按线径、弹性、耐打和磅数建议对比。' },
  { id: 'shuttle', name: '羽毛球', icon: '🪶', desc: '按球速、耐打、稳定性和使用场景选择。' },
  { id: 'shoes', name: '球鞋', icon: '👟', desc: '按缓震、包裹、防滑、脚型和体重选择。' },
]

export const articles = [
  {
    id: 'racket-astrox-77',
    brandId: 'yonex',
    category: 'racket',
    title: 'YONEX 天斧 77 Pro',
    image: '/assets/products/racket-astrox-77.svg',
    summary: '偏进攻但不极端，适合想增强后场下压的进阶玩家。',
    priceRange: '¥900-1300',
    level: '进阶 / 比赛',
    bestFor: '单打、后场进攻、力量中等以上',
    specs: ['4U / 3U', '中杆偏硬', '平衡点偏头重'],
    tags: ['球拍', '进攻', '进阶', 'YONEX'],
    readMin: 3,
    updated: '2026-07',
    content: `## 适合谁
天斧 77 Pro 更适合已经能主动发力、希望提升后场下压质量的用户。它比极端进攻拍更容易上手，连续进攻压力也更小。

## 对比重点
- **价格**：仅作为预算对比，不代表平台售卖。
- **打法**：偏进攻，但保留一定防守和连贯。
- **风险**：力量不足的新手可能觉得挥速慢。

## AI 选品建议
如果用户说“想杀球更重，但不想太难打”，可以把它和李宁雷霆、胜利突击系列一起比较。`,
  },
  {
    id: 'racket-halbertec-6000',
    brandId: 'lining',
    category: 'racket',
    title: '李宁 战戟 6000',
    image: '/assets/products/racket-halbertec-6000.svg',
    summary: '均衡型球拍，容错和控制较好，适合从入门迈向进阶。',
    priceRange: '¥500-850',
    level: '入门进阶',
    bestFor: '双打、攻守均衡、第一支进阶拍',
    specs: ['4U', '中杆适中', '平衡点居中'],
    tags: ['球拍', '均衡', '李宁', '新手友好'],
    readMin: 3,
    updated: '2026-07',
    content: `## 适合谁
战戟 6000 的重点不是某一项极限参数，而是稳定、顺手、覆盖面广。适合还没有明确打法的用户。

## 对比重点
- 比头重进攻拍更轻松。
- 比超轻速度拍更稳。
- 价格区间适合预算中等的新手进阶。`,
  },
  {
    id: 'racket-js12',
    brandId: 'victor',
    category: 'racket',
    title: 'VICTOR 极速 JS-12',
    image: '/assets/products/racket-js12.svg',
    summary: '速度型经典思路，平抽挡和防守转换更轻快。',
    priceRange: '¥650-1000',
    level: '进阶',
    bestFor: '双打、平抽挡、网前封网',
    specs: ['4U', '中杆适中', '偏速度'],
    tags: ['球拍', '速度', '双打', '胜利'],
    readMin: 3,
    updated: '2026-07',
    content: `## 适合谁
适合常打双打、需要更快挥速和更顺畅防守转换的用户。

## 对比重点
如果用户在意杀球绝对威力，它不是第一选择；如果用户在意连贯、接杀、平抽挡，优先级很高。`,
  },
  {
    id: 'racket-kawasaki-entry',
    brandId: 'kawasaki',
    category: 'racket',
    title: '川崎 入门均衡拍',
    image: '/assets/products/racket-kawasaki-entry.svg',
    summary: '预算友好，适合新手建立动作和基础手感。',
    priceRange: '¥150-350',
    level: '入门',
    bestFor: '新手、校园、休闲训练',
    specs: ['4U / 5U', '中杆偏软', '容错高'],
    tags: ['球拍', '入门', '预算', '川崎'],
    readMin: 2,
    updated: '2026-07',
    content: `## 适合谁
适合第一次买拍、预算有限、不确定自己是否长期打球的用户。

## 对比重点
这类产品的核心不是高级材料，而是好上手、耐用、预算压力小。`,
  },
  {
    id: 'string-bg80',
    brandId: 'yonex',
    category: 'string',
    title: 'YONEX BG80',
    image: '/assets/products/string-bg80.svg',
    summary: '0.68mm 经典进攻线，出球直接，控制和弹性平衡。',
    priceRange: '¥45-70 / 条',
    level: '进阶',
    bestFor: '进攻、控制、常规比赛',
    specs: ['0.68mm', '硬弹手感', '耐打中等'],
    tags: ['球线', 'BG80', '进攻', '控制'],
    readMin: 2,
    updated: '2026-07',
    content: `## 适合谁
BG80 适合已经有一定发力基础、希望出球更脆、更直接的用户。

## 磅数建议
新手可从 22-24 磅开始，进阶玩家常见在 25-27 磅区间。具体仍应结合球拍标称磅数和个人发力。`,
  },
  {
    id: 'string-bg65',
    brandId: 'yonex',
    category: 'string',
    title: 'YONEX BG65',
    image: '/assets/products/string-bg65.svg',
    summary: '耐打代表，适合训练量大或经常断线的用户。',
    priceRange: '¥35-55 / 条',
    level: '入门 / 训练',
    bestFor: '耐用、训练、新手',
    specs: ['0.70mm', '耐打强', '手感偏稳'],
    tags: ['球线', '耐打', '新手', '训练'],
    readMin: 2,
    updated: '2026-07',
    content: `## 适合谁
BG65 的优势是耐用和成本可控。它不是最弹、最脆的线，但很适合训练和入门阶段。

## AI 选品建议
当用户说“老断线”“学生预算有限”“训练用”，优先推荐耐打线而不是极致手感线。`,
  },
  {
    id: 'string-no1',
    brandId: 'lining',
    category: 'string',
    title: '李宁 1号线',
    image: '/assets/products/string-no1.svg',
    summary: '弹性和声音表现突出，适合追求清脆击球反馈。',
    priceRange: '¥40-65 / 条',
    level: '进阶',
    bestFor: '弹性、清脆手感、进攻连贯',
    specs: ['0.65mm', '高弹', '耐打偏弱'],
    tags: ['球线', '高弹', '李宁', '手感'],
    readMin: 2,
    updated: '2026-07',
    content: `## 适合谁
适合喜欢清脆击球声、追求弹性反馈的用户。

## 对比重点
细线通常弹性好，但耐久压力更大。训练量大或经常打偏框的用户应谨慎。`,
  },
  {
    id: 'shuttle-as05',
    brandId: 'yonex',
    category: 'shuttle',
    title: 'YONEX AS-05',
    image: '/assets/products/shuttle-as05.svg',
    summary: '训练和日常对抗常见选择，稳定性和价格较均衡。',
    priceRange: '¥80-120 / 筒',
    level: '训练 / 日常',
    bestFor: '俱乐部训练、日常对抗',
    specs: ['鹅毛/鸭毛视版本', '飞行稳定', '耐打中等'],
    tags: ['羽毛球', '训练', '稳定', 'YONEX'],
    readMin: 2,
    updated: '2026-07',
    content: `## 适合谁
适合日常训练和普通对抗。羽毛球的选择要看场地温湿度、球速号和预算。

## 对比重点
价格只作为预算参考，实际选择更应关注球速、飞行稳定和耐打程度。`,
  },
  {
    id: 'shuttle-lining-a6',
    brandId: 'lining',
    category: 'shuttle',
    title: '李宁 A+ 系列训练球',
    image: '/assets/products/shuttle-lining-a6.svg',
    summary: '适合训练消耗，兼顾耐打和稳定。',
    priceRange: '¥65-100 / 筒',
    level: '训练',
    bestFor: '多球训练、社群活动',
    specs: ['耐打优先', '飞行稳定', '成本可控'],
    tags: ['羽毛球', '训练', '李宁', '耐打'],
    readMin: 2,
    updated: '2026-07',
    content: `## 适合谁
适合训练量大、希望控制耗材成本的用户或社群。

## AI 选品建议
如果用户强调“耐打”和“预算”，训练球比比赛球更合适。`,
  },
  {
    id: 'shoes-65z',
    brandId: 'yonex',
    category: 'shoes',
    title: 'YONEX 65Z',
    image: '/assets/products/shoes-65z.svg',
    summary: '经典比赛鞋，缓震、包裹和启动表现均衡。',
    priceRange: '¥650-1000',
    level: '进阶 / 比赛',
    bestFor: '综合场景、脚踝保护、比赛',
    specs: ['缓震强', '包裹稳定', '防滑优秀'],
    tags: ['球鞋', '缓震', '比赛', 'YONEX'],
    readMin: 3,
    updated: '2026-07',
    content: `## 适合谁
适合需要稳定保护、比赛强度较高的用户。球鞋是保护属性最强的装备之一，不建议只看价格。

## 对比重点
宽脚用户需要注意鞋楦；体重大或膝盖敏感用户应优先看缓震。`,
  },
  {
    id: 'shoes-lining-ayzr',
    brandId: 'lining',
    category: 'shoes',
    title: '李宁 雷霆 / 鹘鹰系球鞋',
    image: '/assets/products/shoes-lining-ayzr.svg',
    summary: '缓震和支撑表现突出，适合高强度移动。',
    priceRange: '¥450-850',
    level: '进阶',
    bestFor: '强移动、缓震需求、宽脚用户试穿对比',
    specs: ['支撑强', '缓震好', '部分款鞋楦友好'],
    tags: ['球鞋', '缓震', '李宁', '支撑'],
    readMin: 3,
    updated: '2026-07',
    content: `## 适合谁
适合移动强度大、需要缓震和支撑的用户。李宁部分鞋款对宽脚更友好，但仍建议试穿。

## AI 选品建议
当用户提到膝盖压力、落地震感、脚宽，可以优先把球鞋推荐权重提高。`,
  },
  {
    id: 'shoes-victor-p9200',
    brandId: 'victor',
    category: 'shoes',
    title: 'VICTOR P9200 系列',
    image: '/assets/products/shoes-victor-p9200.svg',
    summary: '稳定和保护取向，适合双打多启动场景。',
    priceRange: '¥450-750',
    level: '进阶',
    bestFor: '双打、防滑、侧向支撑',
    specs: ['稳定支撑', '防滑', '保护感强'],
    tags: ['球鞋', '胜利', '稳定', '双打'],
    readMin: 3,
    updated: '2026-07',
    content: `## 适合谁
适合双打多、横向移动频繁、希望鞋身更稳的用户。

## 对比重点
球鞋对脚型很敏感。AI 回答时应提醒用户结合脚宽、足弓和试穿反馈。`,
  },
]

export const faqs = [
  {
    q: '新手第一套装备怎么选',
    keywords: ['新手', '第一套', '入门', '刚开始', '装备怎么选'],
    a: '新手优先顺序建议是：合脚防滑的球鞋 > 好上手的 4U 均衡拍 > 耐打球线 > 训练球。价格只用于预算对比，不代表平台售卖。预算有限时，先保证球鞋保护和球拍顺手。',
    refIds: ['racket-kawasaki-entry', 'racket-halbertec-6000', 'string-bg65', 'shoes-lining-ayzr'],
  },
  {
    q: '球拍怎么按打法选',
    keywords: ['球拍', '打法', '进攻', '速度', '均衡', '双打', '单打'],
    a: '进攻型看头重和中杆硬度，速度型看挥速和头轻，均衡型适合打法未定或双打多位置。新手不要直接追极端职业参数。',
    refIds: ['racket-astrox-77', 'racket-halbertec-6000', 'racket-js12'],
  },
  {
    q: '球线和磅数怎么选',
    keywords: ['球线', '磅数', '拉线', '耐打', '高弹'],
    a: '新手建议 22-24 磅，从耐打线开始；进阶后再按高弹、控制、击球声音选择。细线更弹但更容易断，粗线更耐打但手感偏稳。',
    refIds: ['string-bg65', 'string-bg80', 'string-no1'],
  },
  {
    q: '羽毛球怎么选',
    keywords: ['羽毛球', '球速', '训练球', '比赛球', '耐打'],
    a: '羽毛球重点看球速、耐打、飞行稳定和使用场景。训练优先成本与耐打，比赛优先飞行稳定。不同地区温湿度会影响球速选择。',
    refIds: ['shuttle-as05', 'shuttle-lining-a6'],
  },
  {
    q: '球鞋怎么选',
    keywords: ['球鞋', '鞋', '缓震', '防滑', '宽脚', '保护'],
    a: '球鞋不是装饰项，优先看防滑、包裹、侧向支撑和缓震。脚宽、体重、膝盖压力都会影响选择，能试穿就不要只看参数。',
    refIds: ['shoes-65z', 'shoes-lining-ayzr', 'shoes-victor-p9200'],
  },
]

const BRAND_ALIASES = [
  { id: 'yonex', alias: ['yonex', '尤尼克斯', '尤尼', 'yy'] },
  { id: 'lining', alias: ['李宁', 'lining', 'ln'] },
  { id: 'victor', alias: ['victor', '胜利', '维克多'] },
  { id: 'kawasaki', alias: ['川崎', 'kawasaki'] },
  { id: 'kumpoo', alias: ['薰风', 'kumpoo'] },
  { id: 'kason', alias: ['凯胜', 'kason'] },
]

const CATEGORY_ALIASES = [
  { id: 'racket', alias: ['球拍', '拍子', '羽毛球拍', '进攻拍', '速度拍'] },
  { id: 'string', alias: ['球线', '线', '拉线', '磅数', '穿线'] },
  { id: 'shuttle', alias: ['羽毛球', '训练球', '比赛球', '球速'] },
  { id: 'shoes', alias: ['球鞋', '鞋', '羽毛球鞋', '缓震', '防滑'] },
]

export function getBrand(id) {
  return brands.find((b) => b.id === id) || null
}

export function getCategory(id) {
  return categories.find((c) => c.id === id) || null
}

export function getArticle(id) {
  return articles.find((a) => a.id === id) || null
}

export function articlesByBrand(brandId) {
  return articles.filter((a) => a.brandId === brandId)
}

export function articlesByCategory(catId) {
  return articles.filter((a) => a.category === catId)
}

export function searchArticles({ keyword = '', brandId = '', category = '' } = {}) {
  const kw = keyword.trim().toLowerCase()
  let list = articles.slice()
  if (brandId) list = list.filter((a) => a.brandId === brandId)
  if (category) list = list.filter((a) => a.category === category)
  if (!kw) return list

  return list
    .map((a) => ({ a, score: scoreItem(a, kw) }))
    .filter((x) => x.score > 0)
    .sort((x, y) => y.score - x.score)
    .map((x) => x.a)
}

function detectFromAliases(text, groups) {
  const lower = text.toLowerCase()
  return groups.find((g) => g.alias.some((a) => lower.includes(a.toLowerCase())))?.id || ''
}

function detectBrand(text) {
  return detectFromAliases(text, BRAND_ALIASES)
}

function detectCategory(text) {
  return detectFromAliases(text, CATEGORY_ALIASES)
}

function scoreItem(item, kw) {
  const brand = getBrand(item.brandId)
  const category = getCategory(item.category)
  const pool = [
    item.title,
    item.summary,
    item.priceRange,
    item.level,
    item.bestFor,
    item.specs.join(' '),
    item.tags.join(' '),
    brand?.name,
    brand?.nameCn,
    category?.name,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

  let score = 0
  if (item.title.toLowerCase().includes(kw)) score += 10
  if (pool.includes(kw)) score += 4

  const cjk = kw.replace(/[^\u4e00-\u9fa5]/g, '')
  for (let i = 0; i < cjk.length - 1; i++) {
    const gram = cjk.slice(i, i + 2)
    if (pool.includes(gram)) score += 1
  }

  for (const token of kw.split(/[\s,，。/]+/).filter((t) => t.length >= 2)) {
    if (pool.includes(token)) score += 1
  }
  return score
}

// 闲聊/问候关键词（与后端 rag_pipeline.is_greeting_or_chitchat 保持一致）
const GREETING_WORDS = /^(你好|您好|hi|hello|hey|嗨|在吗|在不在|哈喽|打招呼|谢谢|感谢|再见|拜拜)[\s！!。.？?~,~]*$/i
const CHITCHAT_PATTERNS = /^(\?|你是谁|你叫什么|你会什么|你能做什么|怎么用|如何使用|无聊吗|闲聊|测试)$/i

function isGreetingOrChitchat(text) {
  const t = (text || '').trim()
  return t.length <= 10 && (GREETING_WORDS.test(t) || CHITCHAT_PATTERNS.test(t))
}

export function ask(question, { brandId = '' } = {}) {
  const q = (question || '').trim()
  if (!q) {
    return {
      answer: '你可以问我：新手第一套装备怎么选？球拍怎么按打法选？球线磅数怎么选？预算 600 元球拍怎么对比？',
      articles: articles.slice(0, 4),
      brandId: brandId || '',
    }
  }

  // 闲聊/问候拦截（防御层：即使前端漏判，这里也不会推荐商品）
  if (isGreetingOrChitchat(q)) {
    return { answer: '你好 👋 告诉我你的预算、水平和打法，我来帮你筛选装备做对比。', articles: [], brandId: '' }
  }

  const effBrand = detectBrand(q) || brandId || ''
  const effCategory = detectCategory(q)
  const lowerQ = q.toLowerCase()

  const faq = faqs.find((f) => f.keywords.some((k) => lowerQ.includes(k.toLowerCase())))
  if (faq) {
    const refs = faq.refIds.map(getArticle).filter(Boolean)
    return {
      answer: `${faq.a}\n\n${formatRefs(refs)}\n\n> 注：本项目是装备品类库与 RAG AI 选品系统，参考价仅用于预算对比。`,
      articles: refs,
      brandId: effBrand,
    }
  }

  // 搜索相关文章（带评分）
  let candidates = searchArticles({ keyword: q, brandId: effBrand, category: effCategory })
  // 只有真正有相关性（score > 0）的才算
  const hasRelevantKeyword = candidates.length > 0

  if (!hasRelevantKeyword) {
    // 没有关键词匹配时，仅按品牌/品类宽泛过滤（不硬塞不相关的）
    candidates = searchArticles({ brandId: effBrand, category: effCategory })
  }

  // 判断查询是否像具体型号（含字母+数字组合，如 AURASPEED 100X、天斧77、JS-12）
  const looksLikeModel = /[a-zA-Z]{3,}[\s\-]*[\d]+[\dXx]*|[\d]+[\s\-]*[uU]|天斧|战戟|极速|弓箭|双刃|NF\d+|AX\d+|JS-\d+|P\d{4}/.test(q)

  // 根据匹配质量决定回复策略
  const hasGoodMatch = candidates.length > 0 && scoreItem(candidates[0], q) >= 4

  if (!candidates.length || (!hasGoodMatch && looksLikeModel)) {
    // 无匹配 或 查了具体型号但库里没有 → 诚实说明，不强推商品
    const brandName = effBrand ? getBrand(effBrand)?.nameCn : ''
    const modelName = looksLikeModel ? q.replace(/[（）()]/g, '').slice(0, 40) : ''
    let answer = ''
    if (modelName) {
      answer = `关于「${modelName}」${brandName ? '（' + brandName + '）' : ''}，我暂时没有收录这款具体型号的详细信息。\n\n`
    }
    answer += `你可以问我以下类型的问题，我能给出更准确的建议：\n\n`
    answer += `- 🏸 **新手入门**：第一套装备怎么选？预算有限怎么搭配？\n`
    answer += `- 🎯 **按需推荐**：进攻型/速度型/均衡型球拍怎么选？球线磅数多少合适？\n`
    answer += `- 👟 **球鞋选择**：宽脚/膝盖敏感/防滑需求怎么满足？\n`
    answer += `- 🪶 **羽毛球**：训练球 vs 比赛球怎么选？\n\n`
    if (effBrand && !looksLikeModel) {
      const brandArticles = articlesByBrand(effBrand).slice(0, 3)
      if (brandArticles.length) {
        answer += `${brandName}的部分热门型号：\n\n${formatRefs(brandArticles)}\n\n`
        return { answer, articles: brandArticles, brandId: effBrand }
      }
    }
    return { answer, articles: [], brandId: effBrand }
  }

  // 有一定匹配度 → 展示结果并引导补充信息
  candidates = candidates.slice(0, 4)
  const brandText = effBrand ? `，并优先参考 ${getBrand(effBrand)?.nameCn}` : ''
  const categoryText = effCategory ? `，品类聚焦 ${getCategory(effCategory)?.name}` : ''
  return {
    answer: `我会把价格当作预算对比参数${brandText}${categoryText}。下面这些装备可作为对比起点：\n\n${formatRefs(candidates)}\n\n建议你再补充：预算、水平、单打/双打、打法偏好、是否宽脚或膝盖敏感，我可以继续缩小范围。`,
    articles: candidates,
    brandId: effBrand,
  }
}

function formatRefs(items) {
  return items
    .map((item) => {
      const brand = getBrand(item.brandId)
      const category = getCategory(item.category)
      return `- **${item.title}**（${brand?.nameCn || '通用'} / ${category?.name || '装备'} / 参考价 ${item.priceRange}）：${item.summary}`
    })
    .join('\n')
}
