/*
SQLyog Community v13.2.0 (64 bit)
MySQL - 8.1.0 : Database - db_ai_shop
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40011 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`db_ai_shop` /*!80016 DEFAULT ENCRYPTION='N' */;

USE `db_ai_shop`;

/*Table structure for table `t_address` */

DROP TABLE IF EXISTS `t_address`;

CREATE TABLE `t_address` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '地址ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `name` varchar(50) NOT NULL COMMENT '收货人',
  `phone` varchar(20) NOT NULL COMMENT '联系电话',
  `address` varchar(255) NOT NULL COMMENT '详细地址',
  `is_default` tinyint DEFAULT '0' COMMENT '是否默认:1是0否',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收货地址表';

/*Data for the table `t_address` */

insert  into `t_address`(`id`,`user_id`,`name`,`phone`,`address`,`is_default`,`create_time`,`update_time`) values 
(1,1,'张三','14412512412','江苏省南京市xxxx路羽毛球馆旁',1,'2026-06-29 08:52:22','2026-06-29 08:52:22'),
(2,1,'李四','14412412411','测试地址',0,'2026-06-29 08:52:44','2026-06-29 08:52:44');

/*Table structure for table `t_admin` */

DROP TABLE IF EXISTS `t_admin`;

CREATE TABLE `t_admin` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '管理员ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(64) NOT NULL COMMENT '密码(MD5)',
  `nickname` varchar(50) DEFAULT NULL COMMENT '昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像',
  `status` tinyint DEFAULT '1' COMMENT '状态:1正常0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员表';

/*Data for the table `t_admin` */

insert  into `t_admin`(`id`,`username`,`password`,`nickname`,`avatar`,`status`,`create_time`,`update_time`) values 
(1,'admin','21232f297a57a5a743894a0e4a801fc3','超级管理员','/uploads/avatar/35cccdc8e6a744a5927e31e160c696f0.png',1,'2026-06-28 20:35:11','2026-06-29 08:32:38');

/*Table structure for table `t_banner` */

DROP TABLE IF EXISTS `t_banner`;

CREATE TABLE `t_banner` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '轮播图ID',
  `title` varchar(100) DEFAULT NULL COMMENT '标题',
  `image` varchar(255) NOT NULL COMMENT '图片地址',
  `link_type` tinyint DEFAULT '0' COMMENT '链接类型:0无1装备2分类',
  `link_id` int DEFAULT '0' COMMENT '链接ID',
  `sort` int DEFAULT '0' COMMENT '排序',
  `status` tinyint DEFAULT '1' COMMENT '状态:1启用0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='轮播图表';

/*Data for the table `t_banner` */

insert  into `t_banner`(`id`,`title`,`image`,`link_type`,`link_id`,`sort`,`status`,`create_time`,`update_time`) values 
(1,'新拍上市','/uploads/banner/1cf442462b9e451e9f66c419b274da33.png',1,1,1,1,'2026-06-28 20:35:11','2026-06-29 07:56:40'),
(2,'球鞋特惠','/uploads/banner/fdaa3bb830314faf9e5e559660428534.png',1,6,2,1,'2026-06-28 20:35:11','2026-06-29 07:58:08');

/*Table structure for table `t_cart` */

DROP TABLE IF EXISTS `t_cart`;

CREATE TABLE `t_cart` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '购物车ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `product_id` int NOT NULL COMMENT '装备ID',
  `quantity` int DEFAULT '1' COMMENT '数量',
  `checked` tinyint DEFAULT '1' COMMENT '是否选中:1是0否',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='购物车表';

/*Data for the table `t_cart` */

insert  into `t_cart`(`id`,`user_id`,`product_id`,`quantity`,`checked`,`create_time`,`update_time`) values 
(1,1,1,2,1,'2026-06-28 20:35:11','2026-06-29 08:46:42'),
(2,1,3,1,1,'2026-06-28 20:35:11','2026-06-28 20:35:11'),
(3,2,6,3,1,'2026-06-28 20:35:11','2026-06-28 20:35:11'),
(4,1,15,1,1,'2026-06-29 08:46:23','2026-06-29 08:46:23'),
(5,1,17,2,1,'2026-06-29 08:46:31','2026-06-29 08:46:39');

/*Table structure for table `t_category` */

DROP TABLE IF EXISTS `t_category`;

CREATE TABLE `t_category` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` varchar(50) NOT NULL COMMENT '分类名称',
  `sort` int DEFAULT '0' COMMENT '排序',
  `status` tinyint DEFAULT '1' COMMENT '状态:1启用0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='装备分类表';

/*Data for the table `t_category` */

insert  into `t_category`(`id`,`name`,`sort`,`status`,`create_time`,`update_time`) values 
(1,'球拍',1,1,'2026-06-28 20:35:11','2026-06-28 20:35:11'),
(2,'球线',2,1,'2026-06-28 20:35:11','2026-06-28 20:35:11'),
(3,'羽毛球',3,1,'2026-06-28 20:35:11','2026-06-28 20:35:11'),
(4,'球鞋',4,1,'2026-06-28 20:35:11','2026-06-28 20:35:11');

/*Table structure for table `t_chat_message` */

DROP TABLE IF EXISTS `t_chat_message`;

CREATE TABLE `t_chat_message` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `session_id` varchar(64) NOT NULL COMMENT '会话ID',
  `role` varchar(20) NOT NULL COMMENT '角色:user/assistant',
  `content` text NOT NULL COMMENT '消息内容',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_session` (`user_id`,`session_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI聊天消息表';

/*Data for the table `t_chat_message` */

insert  into `t_chat_message`(`id`,`user_id`,`session_id`,`role`,`content`,`create_time`) values 
(1,1,'session_001','user','请问新手应该怎么选羽毛球拍？','2026-06-10 09:00:00'),
(2,1,'session_001','assistant','新手建议选攻守平衡的4U或5U全碳素球拍，重量轻、挥速快、容易上手；预算有限可选碳铝入门拍。核心看三个参数：重量(U数)、平衡点(头重进攻/头轻防守)、中杆软硬。建议先到店试握再决定。[资料1｜常见球拍选购问题]','2026-06-10 09:00:05'),
(3,1,'session_001','user','拍线磅数一般拉多少合适？','2026-06-10 09:01:00'),
(4,1,'session_001','assistant','新手建议拉22-24磅，甜区大、容错高、对手腕友好；进阶球友可拉25-27磅提升控球与出球速度，但对力量要求更高。断线后请尽快剪断卸力，避免拍框受力变形。[资料2｜常见穿线与售后问题]','2026-06-10 09:01:05'),
(5,1,'session_ddf85aa1be7f','user','你好，我的拍线断了怎么处理？','2026-06-29 08:25:39'),
(6,1,'session_ddf85aa1be7f','assistant','您好！球线断裂请先用剪线钳从拍面中心向四周剪断，及时释放拍框张力防止变形。您可在小程序「我的」提交穿线服务：质保期内免费重穿，过保仅收穿线费；运费说明见物流政策。如需协助请告诉我您的拍型。[资料2｜常见穿线与售后问题]','2026-06-29 08:25:59'),
(7,1,'session_ce51cbfc0a30','user','买的运动袜磨脚怎么办','2026-06-29 09:00:22'),
(8,1,'session_ce51cbfc0a30','assistant','亲，非常抱歉给您带来不好的体验！我们的羽毛球专用运动袜为毛巾底加厚设计，若仍磨脚多为尺码偏差。您可申请换码或退货退款，来回运费由我们承担，并额外赠送一双同款作为补偿。您看可以吗？[资料2｜常见穿线与售后问题]','2026-06-29 09:00:38'),
(9,1,'session_ce51cbfc0a30','user','比赛用球选鹅毛还是鸭毛？','2026-06-29 09:01:26'),
(10,1,'session_ce51cbfc0a30','assistant','比赛推荐用鹅毛球，飞行更稳定、耐打性更好，适合赛事与高强度对抗；日常训练用鸭毛球性价比更高。我们「比赛级鹅毛羽毛球(12只)」与「训练鸭毛羽毛球(12只)」均有售，可按场景搭配。[资料4｜装备保养与其他问题]','2026-06-29 09:01:39');

/*Table structure for table `t_knowledge_file` */

DROP TABLE IF EXISTS `t_knowledge_file`;

CREATE TABLE `t_knowledge_file` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '知识库文件ID',
  `file_name` varchar(255) NOT NULL COMMENT '文件名',
  `file_type` varchar(20) NOT NULL COMMENT '文件类型:txt/doc/pdf/markdown',
  `file_path` varchar(500) NOT NULL COMMENT '文件路径',
  `file_size` int DEFAULT '0' COMMENT '文件大小(字节)',
  `chunk_count` int DEFAULT '0' COMMENT '分块数量',
  `status` tinyint DEFAULT '0' COMMENT '状态:0待处理1已向量化2失败',
  `error_msg` varchar(500) DEFAULT NULL COMMENT '错误信息',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文件表';

/*Data for the table `t_knowledge_file` */

insert  into `t_knowledge_file`(`id`,`file_name`,`file_type`,`file_path`,`file_size`,`chunk_count`,`status`,`error_msg`,`create_time`,`update_time`) values 
(4,'常见球拍选购问题.md','markdown','D:/uploads14/knowledge/5d2c51896a424d25879b91569cb467f0.md',4520,6,1,NULL,'2026-06-29 08:27:00','2026-06-29 08:27:01'),
(5,'常见穿线与售后问题.docx','doc','D:/uploads14/knowledge/0f2caba5851948d4ab9c929f788bead2.docx',15340,7,1,NULL,'2026-06-29 08:27:22','2026-06-29 08:27:22'),
(6,'常见物流配送问题.txt','txt','D:/uploads14/knowledge/3d6d8bd179824740914928ae72d85434.txt',3290,4,1,NULL,'2026-06-29 08:27:26','2026-06-29 08:27:27'),
(7,'装备保养与其他问题.md','markdown','D:/uploads14/knowledge/d9b6195096ca41338190be2333104105.md',3980,5,1,NULL,'2026-06-29 08:27:30','2026-06-29 08:27:30');

/*Table structure for table `t_order` */

DROP TABLE IF EXISTS `t_order`;

CREATE TABLE `t_order` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `order_no` varchar(32) NOT NULL COMMENT '订单编号',
  `user_id` int NOT NULL COMMENT '用户ID',
  `total_amount` decimal(10,2) NOT NULL COMMENT '订单总金额',
  `pay_amount` decimal(10,2) NOT NULL COMMENT '实付金额',
  `status` tinyint DEFAULT '0' COMMENT '状态:0待支付1已支付2已发货3已完成4已取消',
  `receiver_name` varchar(50) DEFAULT NULL COMMENT '收货人',
  `receiver_phone` varchar(20) DEFAULT NULL COMMENT '收货电话',
  `receiver_address` varchar(255) DEFAULT NULL COMMENT '收货地址',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `pay_time` datetime DEFAULT NULL COMMENT '支付时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

/*Data for the table `t_order` */

insert  into `t_order`(`id`,`order_no`,`user_id`,`total_amount`,`pay_amount`,`status`,`receiver_name`,`receiver_phone`,`receiver_address`,`remark`,`pay_time`,`create_time`,`update_time`) values 
(1,'202606010001',1,727.00,727.00,3,'张三','13800000001','北京市朝阳区建国路88号',NULL,'2026-06-23 10:30:00','2026-06-23 10:25:17','2026-06-29 08:21:16'),
(2,'202606020001',1,499.00,499.00,1,'张三','13800000001','北京市朝阳区建国路88号',NULL,'2026-06-24 14:20:00','2026-06-24 14:15:30','2026-06-29 08:21:16'),
(3,'202606030001',2,699.00,699.00,3,'李四','13800000002','上海市浦东新区陆家嘴100号',NULL,'2026-06-25 09:10:00','2026-06-25 09:05:22','2026-06-29 08:21:16'),
(4,'202606040001',3,459.00,459.00,2,'王五','13800000003','广州市天河区体育西路200号',NULL,'2026-06-27 16:45:00','2026-06-27 16:40:11','2026-06-29 08:21:16'),
(5,'202606050001',1,0.00,0.00,0,'张三','13800000001','北京市朝阳区建国路88号',NULL,NULL,'2026-06-29 11:20:00','2026-06-29 08:21:16'),
(6,'TREND001',2,0.00,0.00,1,'李四','13800000002','上海市浦东新区陆家嘴100号',NULL,'2026-06-26 11:30:00','2026-06-26 11:25:17','2026-06-29 08:21:16'),
(7,'TREND002',3,299.00,299.00,1,'王五','13800000003','广州市天河区体育西路200号',NULL,'2026-06-27 09:15:00','2026-06-27 09:10:22','2026-06-29 08:21:16'),
(8,'TREND003',1,359.00,359.00,3,'张三','13800000001','北京市朝阳区建国路88号',NULL,'2026-06-28 15:40:00','2026-06-28 15:35:17','2026-06-29 08:21:16'),
(9,'TREND004',2,68.00,68.00,3,'李四','13800000002','上海市浦东新区陆家嘴100号',NULL,'2026-06-29 08:20:00','2026-06-29 08:15:30','2026-06-29 08:21:16'),
(10,'TREND005',3,199.00,199.00,3,'王五','13800000003','广州市天河区体育西路200号',NULL,'2026-06-25 18:10:00','2026-06-25 18:05:11','2026-06-29 08:21:16'),
(11,'202606290853019607',1,1389.00,1389.00,3,'李四','14412412411','测试地址','放门卫','2026-06-29 08:53:02','2026-06-29 08:53:01','2026-06-29 08:59:23');

/*Table structure for table `t_order_item` */

DROP TABLE IF EXISTS `t_order_item`;

CREATE TABLE `t_order_item` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '订单明细ID',
  `order_id` int NOT NULL COMMENT '订单ID',
  `product_id` int NOT NULL COMMENT '装备ID',
  `product_name` varchar(100) NOT NULL COMMENT '装备名称',
  `product_image` varchar(255) DEFAULT NULL COMMENT '装备图片',
  `price` decimal(10,2) NOT NULL COMMENT '单价',
  `quantity` int NOT NULL COMMENT '数量',
  `total_price` decimal(10,2) NOT NULL COMMENT '小计',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_order_id` (`order_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单明细表';

/*Data for the table `t_order_item` */

insert  into `t_order_item`(`id`,`order_id`,`product_id`,`product_name`,`product_image`,`price`,`quantity`,`total_price`,`create_time`) values 
(1,1,1,'进攻型全碳素羽毛球拍','/uploads/product/4cf50c521f2848f7887e07189c69f952.png',599.00,1,599.00,'2026-06-28 20:35:11'),
(2,1,15,'比赛级鹅毛羽毛球(12只)','/uploads/product/84ad08a275d0482b9b4f5a054c25a979.png',128.00,1,128.00,'2026-06-28 20:35:11'),
(3,2,6,'专业比赛羽毛球鞋','/uploads/product/998a79f9fd134f4db09ebe6161d3d7cb.png',499.00,1,499.00,'2026-06-28 20:35:11'),
(4,3,3,'双打速度羽毛球拍(5U)','/uploads/product/6155dcbf97144586ad4d5a6e36375125.png',699.00,1,699.00,'2026-06-28 20:35:11'),
(6,4,2,'攻守平衡羽毛球拍(4U)','/uploads/product/5d26b0899fe7414da89f830f2b21e6e9.png',459.00,1,459.00,'2026-06-28 20:35:11'),
(9,7,7,'轻量训练羽毛球鞋','/uploads/product/75430aa7ea5a417ca75337efa9afebba.png',299.00,1,299.00,'2026-06-29 08:21:16'),
(10,8,8,'室内运动羽毛球鞋','/uploads/product/c0e38e80895c4a21afe4579edf5da151.png',359.00,1,359.00,'2026-06-29 08:21:16'),
(11,9,16,'训练鸭毛羽毛球(12只)','/uploads/product/6d10a54ba2b14e5795094531e576ce8e.png',68.00,1,68.00,'2026-06-29 08:21:16'),
(13,10,4,'入门训练羽毛球拍(碳铝)','/uploads/product/377ebba773c34e7aaecbcf416cee8695.png',199.00,1,199.00,'2026-06-25 18:05:11'),
(15,11,5,'高端比赛羽毛球拍(4U)','/uploads/product/a21fa5c85e934dee807ef5166c493de5.png',1299.00,1,1299.00,'2026-06-29 08:53:02'),
(16,11,17,'高性能羽毛球线(条)','/uploads/product/89d99e55c6e94dc492590a46b7dd2117.png',45.00,2,90.00,'2026-06-29 08:53:02');

/*Table structure for table `t_product` */

DROP TABLE IF EXISTS `t_product`;

CREATE TABLE `t_product` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '装备ID',
  `category_id` int NOT NULL COMMENT '分类ID',
  `name` varchar(100) NOT NULL COMMENT '装备名称',
  `description` text COMMENT '装备描述',
  `specs` json DEFAULT NULL COMMENT '结构化规格(JSON):球拍/球线/羽毛球/球鞋各自参数',
  `price` decimal(10,2) NOT NULL COMMENT '价格',
  `stock` int DEFAULT '0' COMMENT '库存',
  `image` varchar(255) DEFAULT NULL COMMENT '主图',
  `images` text COMMENT '图片(JSON数组)',
  `sales` int DEFAULT '0' COMMENT '销量',
  `status` tinyint DEFAULT '1' COMMENT '状态:1上架0下架',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_category_id` (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='装备表';

/*Data for the table `t_product` */

insert  into `t_product`(`id`,`category_id`,`name`,`description`,`specs`,`price`,`stock`,`image`,`images`,`sales`,`status`,`create_time`,`update_time`) values 
(1,1,'进攻型全碳素羽毛球拍','3U全碳素一体成型，头重设计，适合后场重杀','{"weight_class":"3U","balance":"head-heavy","shaft_flex":"stiff","max_tension":"28 lbs","material":"carbon fiber","suitable_level":["intermediate","advanced"],"suitable_style":["attack"],"suitable_scene":["singles","doubles"],"difficulty":"medium"}',599.00,200,'/uploads/product/4cf50c521f2848f7887e07189c69f952.png',NULL,122,1,'2026-06-28 20:35:11','2026-06-29 08:53:02'),
(2,1,'攻守平衡羽毛球拍','4U全碳素，均衡手感，适合进阶球友全面打法','{"weight_class":"4U","balance":"even-balanced","shaft_flex":"medium","max_tension":"27 lbs","material":"carbon fiber","suitable_level":["beginner","intermediate"],"suitable_style":["balanced","attack","defense"],"suitable_scene":["singles","doubles"],"difficulty":"low"}',459.00,260,'/uploads/product/5d26b0899fe7414da89f830f2b21e6e9.png',NULL,85,1,'2026-06-28 20:35:11','2026-06-29 07:50:12'),
(3,1,'双打速度羽毛球拍','5U超轻挥速快，网前封网与平抽利器','{"weight_class":"5U","balance":"head-light","shaft_flex":"medium","max_tension":"27 lbs","material":"carbon fiber","suitable_level":["intermediate","advanced"],"suitable_style":["defense","balanced"],"suitable_scene":["doubles","mixed"],"difficulty":"medium"}',699.00,150,'/uploads/product/6155dcbf97144586ad4d5a6e36375125.png',NULL,231,1,'2026-06-28 20:35:11','2026-06-29 08:53:02'),
(4,1,'入门训练羽毛球拍','碳铝材质耐打实惠，新手入门首选','{"weight_class":"5U","balance":"even-balanced","shaft_flex":"flexible","max_tension":"24 lbs","material":"carbon aluminum","suitable_level":["beginner"],"suitable_style":["balanced"],"suitable_scene":["singles","doubles"],"difficulty":"low"}',199.00,500,'/uploads/product/377ebba773c34e7aaecbcf416cee8695.png',NULL,401,1,'2026-06-28 20:35:11','2026-06-29 08:53:02'),
(5,1,'高端比赛羽毛球拍','4U国家队同款科技，精准控球与稳定手感','{"weight_class":"4U","balance":"even-balanced","shaft_flex":"extra-stiff","max_tension":"30 lbs","material":"carbon fiber","suitable_level":["advanced","competitive"],"suitable_style":["control","balanced"],"suitable_scene":["singles"],"difficulty":"high"}',1299.00,80,'/uploads/product/a21fa5c85e934dee807ef5166c493de5.png',NULL,38,1,'2026-06-28 20:35:11','2026-06-29 07:50:12'),
(6,4,'专业比赛羽毛球鞋','侧向支撑强、防滑耐磨，保护脚踝与膝盖','{"cushion_score":9.0,"support_score":9.0,"grip_score":9.0,"weight":"medium","foot_type":"normal","ankle_support":"high","suitable_scene":["match","high_frequency"],"suitable_user":["intermediate","advanced","knee_sensitive"]}',499.00,220,'/uploads/product/998a79f9fd134f4db09ebe6161d3d7cb.png',NULL,180,1,'2026-06-28 20:35:11','2026-06-29 07:48:31'),
(7,4,'轻量训练羽毛球鞋','透气网面，日常训练与业余对抗舒适之选','{"cushion_score":7.5,"support_score":7.5,"grip_score":8.0,"weight":"light","foot_type":"normal","ankle_support":"medium","suitable_scene":["training"],"suitable_user":["beginner","intermediate"]}',299.00,300,'/uploads/product/75430aa7ea5a417ca75337efa9afebba.png',NULL,210,1,'2026-06-28 20:35:11','2026-06-29 07:48:09'),
(8,4,'室内运动羽毛球鞋','牛筋底止滑，缓震回弹，室内场地专用','{"cushion_score":8.0,"support_score":8.0,"grip_score":8.5,"weight":"medium","foot_type":"normal","ankle_support":"medium","suitable_scene":["training","match"],"suitable_user":["beginner","intermediate"]}',359.00,180,'/uploads/product/c0e38e80895c4a21afe4579edf5da151.png',NULL,95,1,'2026-06-28 20:35:11','2026-06-29 07:47:44'),
(9,4,'透气减震羽毛球鞋','EVA中底回弹，长时间对抗不累脚','{"cushion_score":9.5,"support_score":8.0,"grip_score":8.5,"weight":"light","foot_type":"normal","ankle_support":"medium","suitable_scene":["training","high_frequency"],"suitable_user":["beginner","intermediate","knee_sensitive"]}',269.00,400,'/uploads/product/3d86497565f84b408f7eccf3ba48e329.png',NULL,320,1,'2026-06-28 20:35:11','2026-06-29 07:46:59'),
(15,3,'比赛级鹅毛羽毛球(12只)','稳定耐打，赛事与高强度对抗用球','{"material":"goose_feather","speed":"77","durability_score":8.0,"flight_stability_score":9.0,"feel_score":8.5,"suitable_scene":["club_match","competition"],"balls_per_tube":12,"price_per_tube":128}',128.00,300,'/uploads/product/84ad08a275d0482b9b4f5a054c25a979.png',NULL,134,1,'2026-06-28 20:35:11','2026-06-29 07:44:29'),
(16,3,'训练鸭毛羽毛球(12只)','性价比高，日常训练常用','{"material":"duck_feather","speed":"76","durability_score":7.0,"flight_stability_score":7.5,"feel_score":7.0,"suitable_scene":["training"],"balls_per_tube":12,"price_per_tube":68}',68.00,600,'/uploads/product/8ee3ab23766247038189984e2c5d967f.png',NULL,56,1,'2026-06-28 20:35:11','2026-06-29 07:44:20'),
(17,2,'高性能羽毛球线(条)','高弹耐打，手感清晰出球干脆','{"gauge":"0.68mm","repulsion_score":9.0,"control_score":8.0,"durability_score":6.5,"sound_score":9.5,"recommended_tension":{"beginner":"22-24 lbs","intermediate":"24-26 lbs","advanced":"26-28 lbs"},"suitable_style":["attack","control"]}',45.00,500,'/uploads/product/89d99e55c6e94dc492590a46b7dd2117.png',NULL,410,1,'2026-06-28 20:35:11','2026-06-29 07:44:13');

/*Table structure for table `t_user` */

DROP TABLE IF EXISTS `t_user`;

CREATE TABLE `t_user` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(64) NOT NULL COMMENT '密码(MD5)',
  `phone` varchar(20) DEFAULT NULL COMMENT '手机号',
  `nickname` varchar(50) DEFAULT NULL COMMENT '昵称',
  `avatar` varchar(255) DEFAULT NULL COMMENT '头像',
  `status` tinyint DEFAULT '1' COMMENT '状态:1正常0禁用',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';

/*Data for the table `t_user` */

insert  into `t_user`(`id`,`username`,`password`,`phone`,`nickname`,`avatar`,`status`,`create_time`,`update_time`) values 
(1,'user001','e10adc3949ba59abbe56e057f20f883e','13800000001','张三','/uploads/avatar/33737e5abb584c928f6a8cefe96b5a63.jpg',1,'2026-06-28 20:35:11','2026-06-29 08:43:38'),
(2,'user002','e10adc3949ba59abbe56e057f20f883e','13800000002','李四',NULL,1,'2026-06-28 20:35:11','2026-06-28 20:35:11'),
(3,'user003','e10adc3949ba59abbe56e057f20f883e','13800000003','王五',NULL,1,'2026-06-28 20:35:11','2026-06-28 20:35:11'),
(4,'cc','e10adc3949ba59abbe56e057f20f883e',NULL,'cc',NULL,1,'2026-06-29 08:32:58','2026-06-29 08:32:58'),
(5,'jack','25d55ad283aa400af464c76d713c07ad','15541214122','杰克2','/uploads/avatar/ea6f59026ceb43e1a6147d87eee0d9b0.jpg',1,'2026-06-29 08:39:00','2026-06-29 08:42:49');

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40011 SET SQL_NOTES=@OLD_SQL_NOTES */;
