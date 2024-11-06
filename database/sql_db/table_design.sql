/*
 Navicat Premium Dump SQL

 Source Server         : dashMelon
 Source Server Type    : MySQL
 Source Server Version : 50744 (5.7.44)
 Source Host           : localhost:3306
 Source Schema         : app

 Target Server Type    : MySQL
 Target Server Version : 50744 (5.7.44)
 File Encoding         : 65001

 Date: 06/11/2024 14:02:14
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for sys_group
-- ----------------------------
DROP TABLE IF EXISTS `sys_group`;
CREATE TABLE `sys_group`  (
  `group_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '团队名称',
  `group_status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '团队状态（0：停用，1：启用）',
  `group_roles` json NOT NULL COMMENT '团队拥有的角色分配权限',
  `group_users` json NOT NULL COMMENT '被授权人',
  `group_admin_users` json NOT NULL COMMENT '授权人',
  `update_datetime` datetime NOT NULL COMMENT '更新时间',
  `update_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁更新',
  `create_datetime` datetime NOT NULL COMMENT '创建时间',
  `create_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁创建',
  `group_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '团队描述'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_group
-- ----------------------------

-- ----------------------------
-- Table structure for sys_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role`  (
  `role_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色名',
  `access_metas` json NOT NULL COMMENT '角色拥有的权限',
  `role_status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '正常/停用',
  `update_datetime` datetime NOT NULL COMMENT '更新时间',
  `update_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁更新',
  `create_datetime` datetime NOT NULL COMMENT '创建时间',
  `create_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁创建',
  `role_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色描述',
  INDEX `uniq_role_name`(`role_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_role
-- ----------------------------
INSERT INTO `sys_role` VALUES ('admin', '[]', '启用', '2024-11-04 22:07:05', 'admin', '2024-11-03 14:19:44', 'admin', '超级管理员角色');
INSERT INTO `sys_role` VALUES ('支付余额查看', '[\"支付页-可用余额\"]', '启用', '2024-11-06 13:58:11', 'admin', '2024-11-06 13:58:11', 'admin', '支付余额查看');
INSERT INTO `sys_role` VALUES ('今年支付额查看', '[\"支付页-今年支付额\"]', '启用', '2024-11-06 13:58:32', 'admin', '2024-11-06 13:58:32', 'admin', '今年支付额查看');
INSERT INTO `sys_role` VALUES ('购买权限', '[\"购买页-页面\", \"购买页-已买商品\", \"购买页-购物车\"]', '启用', '2024-11-06 13:58:54', 'admin', '2024-11-06 13:58:49', 'admin', '\n购买权限');

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user`  (
  `user_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '用户名',
  `user_full_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '全名',
  `password_sha256` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码SHA256值',
  `user_status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '正常/停用',
  `user_sex` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '性别',
  `user_roles` json NOT NULL COMMENT '角色',
  `user_email` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '电子邮箱',
  `phone_number` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '电话号码',
  `update_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁更新',
  `update_datetime` datetime NOT NULL COMMENT '更新时间',
  `create_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁创建',
  `create_datetime` datetime NOT NULL COMMENT '创建时间',
  `user_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户描述',
  UNIQUE INDEX `uniq_name`(`user_name`) USING BTREE,
  UNIQUE INDEX `uniq_full_name`(`user_full_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_user
-- ----------------------------
INSERT INTO `sys_user` VALUES ('admin', '超级管理员', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', '启用', '未知', '[\"admin\"]', '666666@163.com', '13333333333', 'admin', '2024-11-02 23:36:37', 'admin', '2024-11-02 23:36:53', '初始超级管理员');
INSERT INTO `sys_user` VALUES ('xiaoHong', '小红', '278c5625a81c83ffcb888a63c907b8559543f3c1f2666bcccb1ce285f692be57', '启用', '男', '[\"购买权限\"]', '', '', 'admin', '2024-11-06 14:01:40', 'admin', '2024-11-06 14:01:40', '消费者');
INSERT INTO `sys_user` VALUES ('xiaoMing', '小明', 'e10582e36a7f03a6e84db0aea05276e34a4ef26f4ac77a320c78d3a13f110482', '启用', '男', '[\"支付余额查看\"]', 'xiaoMing@163.com', '13929721112', 'admin', '2024-11-06 14:00:44', 'admin', '2024-11-06 14:00:44', '查看余额');

SET FOREIGN_KEY_CHECKS = 1;
