CREATE DATABASE IF NOT EXISTS `db_ai_shop` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `db_ai_shop`;

DROP TABLE IF EXISTS `t_chat_message`;
DROP TABLE IF EXISTS `t_knowledge_file`;
DROP TABLE IF EXISTS `t_banner`;
DROP TABLE IF EXISTS `t_product`;
DROP TABLE IF EXISTS `t_category`;
DROP TABLE IF EXISTS `t_user`;
DROP TABLE IF EXISTS `t_admin`;

CREATE TABLE `t_admin` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '管理员ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(64) NOT NULL COMMENT '密码(MD5)',
  `nickname` varchar(50) DEFAULT NULL COMMENT '昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像',
  `status` int DEFAULT 1 COMMENT '状态:1正常0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_admin_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

CREATE TABLE `t_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(64) NOT NULL COMMENT '密码(MD5)',
  `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `nickname` varchar(50) DEFAULT NULL COMMENT '昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像',
  `status` int DEFAULT 1 COMMENT '状态:1正常0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE `t_category` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` varchar(50) NOT NULL COMMENT '分类名称',
  `sort` int DEFAULT 0 COMMENT '排序',
  `status` int DEFAULT 1 COMMENT '状态:1启用0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='装备分类表';

CREATE TABLE `t_product` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '装备ID',
  `category_id` int NOT NULL COMMENT '分类ID',
  `name` varchar(100) NOT NULL COMMENT '装备名称',
  `brand` varchar(50) DEFAULT NULL COMMENT '品牌',
  `series` varchar(100) DEFAULT NULL COMMENT '系列',
  `model_aliases` json DEFAULT NULL COMMENT '型号别名(JSON数组)',
  `description` text COMMENT '装备描述',
  `specs` json DEFAULT NULL COMMENT '结构化规格(JSON)',
  `price` decimal(10,2) NOT NULL COMMENT '参考价，仅用于预算对比',
  `image` varchar(255) DEFAULT NULL COMMENT '装备主图',
  `images` text COMMENT '装备图片(JSON数组)',
  `source_url` varchar(500) DEFAULT NULL COMMENT '来源链接',
  `source_note` varchar(255) DEFAULT NULL COMMENT '来源备注',
  `tags` json DEFAULT NULL COMMENT '系统标签(JSON数组)',
  `manual_tags` json DEFAULT NULL COMMENT '人工标签(JSON数组)',
  `status` int DEFAULT 1 COMMENT '状态:1启用0停用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_product_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='装备品类库';

CREATE TABLE `t_banner` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '内容位ID',
  `title` varchar(100) DEFAULT NULL COMMENT '标题',
  `image` varchar(255) NOT NULL COMMENT '图片地址',
  `link_type` int DEFAULT 0 COMMENT '链接类型:0无1装备2分类',
  `link_id` int DEFAULT 0 COMMENT '链接ID',
  `sort` int DEFAULT 0 COMMENT '排序',
  `status` int DEFAULT 1 COMMENT '状态:1启用0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容位表';

CREATE TABLE `t_knowledge_file` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '知识库文件ID',
  `file_name` varchar(255) NOT NULL COMMENT '文件名',
  `file_type` varchar(20) NOT NULL COMMENT '文件类型',
  `file_path` varchar(500) NOT NULL COMMENT '文件路径',
  `file_size` int DEFAULT 0 COMMENT '文件大小(字节)',
  `chunk_count` int DEFAULT 0 COMMENT '分块数量',
  `status` int DEFAULT 0 COMMENT '状态:0待处理1已向量化2失败',
  `error_msg` varchar(500) DEFAULT NULL COMMENT '错误信息',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文件表';

CREATE TABLE `t_chat_message` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `session_id` varchar(64) NOT NULL COMMENT '会话ID',
  `role` varchar(20) NOT NULL COMMENT '角色:user/assistant',
  `content` text NOT NULL COMMENT '消息内容',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_chat_user_session` (`user_id`, `session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI聊天消息表';

INSERT INTO `t_admin` (`id`, `username`, `password`, `nickname`, `status`) VALUES
(1, 'admin', '0192023a7bbd73250516f069df18b500', '管理员', 1);

INSERT INTO `t_category` (`id`, `name`, `sort`, `status`) VALUES
(1, '球拍', 1, 1),
(2, '球线', 2, 1),
(3, '羽毛球', 3, 1),
(4, '球鞋', 4, 1);

INSERT INTO `t_product` (`id`, `category_id`, `name`, `brand`, `series`, `model_aliases`, `description`, `specs`, `price`, `tags`, `status`) VALUES
(1, 1, 'YONEX ASTROX 77 Tour', 'YONEX', 'ASTROX', JSON_ARRAY('AX77TOUR','ASTROX 77 TOUR','天斧77TOUR'), '偏进攻但不极端的进阶球拍，适合后场下压与单双打兼顾。', JSON_OBJECT('weight_class','4U','balance','head-heavy','shaft_flex','medium','suitable_level',JSON_ARRAY('intermediate','advanced'),'suitable_style',JSON_ARRAY('attack','balanced')), 899.00, JSON_ARRAY('进攻','进阶'), 1),
(2, 1, 'VICTOR JETSPEED S 12 II', 'VICTOR', 'JETSPEED', JSON_ARRAY('JS12II','JETSPEED S 12 II','极速12II'), '速度型球拍，适合双打平抽挡和连贯防守。', JSON_OBJECT('weight_class','4U','balance','head-light','shaft_flex','medium','suitable_level',JSON_ARRAY('intermediate','advanced'),'suitable_style',JSON_ARRAY('defense','control')), 1080.00, JSON_ARRAY('速度','双打'), 1),
(3, 2, 'YONEX BG80', 'YONEX', NULL, JSON_ARRAY('BG80'), '击球反馈清晰，适合喜欢硬朗手感和进攻反馈的用户。', JSON_OBJECT('gauge','0.68','feel','hard','durability','high','suitable_style',JSON_ARRAY('attack','control')), 68.00, JSON_ARRAY('高弹','耐打'), 1),
(4, 2, '李宁 No.1', 'LI-NING', NULL, JSON_ARRAY('NO1','NO.1','1号线'), '弹性较好，适合追求出球速度和清脆声音的用户。', JSON_OBJECT('gauge','0.65','feel','medium','durability','medium','suitable_style',JSON_ARRAY('attack','balanced')), 55.00, JSON_ARRAY('高弹','手感'), 1),
(5, 3, '亚狮龙 7 号', 'RSL', '7号', JSON_ARRAY('7号','RSL7'), '训练和俱乐部常用羽毛球，飞行稳定，耐打均衡。', JSON_OBJECT('material','goose_feather','speed','77','durability','high'), 118.00, JSON_ARRAY('训练','稳定'), 1),
(6, 4, 'YONEX 65Z3', 'YONEX', '65Z', JSON_ARRAY('65Z3','POWER CUSHION 65Z3'), '缓震和包裹兼顾，适合高频移动和膝盖敏感用户优先试穿。', JSON_OBJECT('cushion_score',9.2,'support_score',8.8,'ankle_support','medium','suitable_level',JSON_ARRAY('intermediate','advanced')), 799.00, JSON_ARRAY('高缓震','比赛'), 1);
