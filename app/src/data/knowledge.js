/**
 * 装备库静态基础数据：品牌与品类。
 *
 * 注意：这里只保留 brands / categories / getBrand / getCategory 四个导出。
 * 原 articles / faqs / ask / searchArticles 等本地降级逻辑已移除——
 * 前端已连接后端真实 AI（WS 流式），不再需要本地知识库兜底。
 */

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

export function getBrand(id) {
  return brands.find((b) => b.id === id) || null
}

export function getCategory(id) {
  return categories.find((c) => c.id === id) || null
}
