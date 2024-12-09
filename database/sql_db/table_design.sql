/*
 Navicat Premium Dump SQL

 Source Server         : app
 Source Server Type    : MySQL
 Source Server Version : 50744 (5.7.44)
 Source Host           : localhost:3306
 Source Schema         : app

 Target Server Type    : MySQL
 Target Server Version : 50744 (5.7.44)
 File Encoding         : 65001

 Date: 24/11/2024 22:22:35
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for sys_group
-- ----------------------------
DROP TABLE IF EXISTS `sys_group`;
CREATE TABLE `sys_group`  (
  `group_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '团队名称',
  `group_status` tinyint(4) NOT NULL COMMENT '团队状态（0：停用，1：启用）',
  `update_datetime` datetime NOT NULL COMMENT '更新时间',
  `update_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁更新',
  `create_datetime` datetime NOT NULL COMMENT '创建时间',
  `create_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁创建',
  `group_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '团队描述',
  PRIMARY KEY (`group_name`) USING BTREE,
  UNIQUE INDEX `uniq_group_name`(`group_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_group
-- ----------------------------

-- ----------------------------
-- Table structure for sys_group_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_group_role`;
CREATE TABLE `sys_group_role`  (
  `group_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `role_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  UNIQUE INDEX `uniq_group_name_role_name`(`group_name`, `role_name`) USING BTREE,
  INDEX `fk_role_name_tb_group_role`(`role_name`) USING BTREE,
  CONSTRAINT `fk_group_name_tb_group_role` FOREIGN KEY (`group_name`) REFERENCES `sys_group` (`group_name`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_role_name_tb_group_role` FOREIGN KEY (`role_name`) REFERENCES `sys_role` (`role_name`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_group_role
-- ----------------------------

-- ----------------------------
-- Table structure for sys_group_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_group_user`;
CREATE TABLE `sys_group_user`  (
  `group_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `user_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `is_admin` tinyint(4) NOT NULL,
  UNIQUE INDEX `uniq_group_name_user_name`(`group_name`, `user_name`) USING BTREE,
  INDEX `fk_user_name_tb_group_user`(`user_name`) USING BTREE,
  CONSTRAINT `fk_group_name_tb_group_user` FOREIGN KEY (`group_name`) REFERENCES `sys_group` (`group_name`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_user_name_tb_group_user` FOREIGN KEY (`user_name`) REFERENCES `sys_user` (`user_name`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_group_user
-- ----------------------------

-- ----------------------------
-- Table structure for sys_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role`  (
  `role_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色名',
  `role_status` tinyint(4) NOT NULL COMMENT '角色状态（0：停用，1：启用）',
  `update_datetime` datetime NOT NULL COMMENT '更新时间',
  `update_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁更新',
  `create_datetime` datetime NOT NULL COMMENT '创建时间',
  `create_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁创建',
  `role_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色描述',
  PRIMARY KEY (`role_name`) USING BTREE,
  INDEX `uniq_role_name`(`role_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_role
-- ----------------------------
INSERT INTO `sys_role` VALUES ('admin', 1, '2024-11-24 22:21:35', 'admin', '2024-11-24 22:21:56', 'admin', '超级管理员');

-- ----------------------------
-- Table structure for sys_role_access_meta
-- ----------------------------
DROP TABLE IF EXISTS `sys_role_access_meta`;
CREATE TABLE `sys_role_access_meta`  (
  `role_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `access_meta` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  UNIQUE INDEX `uniq_role_name_access_meta`(`role_name`, `access_meta`) USING BTREE,
  CONSTRAINT `fk_role_name_tb_role_access_meta` FOREIGN KEY (`role_name`) REFERENCES `sys_role` (`role_name`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_role_access_meta
-- ----------------------------

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user`  (
  `user_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '用户名',
  `user_full_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '全名',
  `user_status` tinyint(4) NULL DEFAULT NULL COMMENT '用户状态（0：停用，1：启用）',
  `password_sha256` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码SHA256值',
  `user_sex` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '性别',
  `user_email` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '电子邮箱',
  `phone_number` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '电话号码',
  `update_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁更新',
  `update_datetime` datetime NOT NULL COMMENT '更新时间',
  `create_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '被谁创建',
  `create_datetime` datetime NOT NULL COMMENT '创建时间',
  `user_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户描述',
  `otp_secret` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT 'OTP密钥',
  PRIMARY KEY (`user_name`) USING BTREE,
  UNIQUE INDEX `uniq_name`(`user_name`) USING BTREE,
  UNIQUE INDEX `uniq_full_name`(`user_full_name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_user
-- ----------------------------
INSERT INTO `sys_user` VALUES ('admin', '超级管理员', 1, '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', '未知', '66666677@163.com', '1333333333', 'admin', now(), 'admin', now(), '初始超级管理员');

-- ----------------------------
-- Table structure for sys_user_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_user_role`;
CREATE TABLE `sys_user_role`  (
  `user_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `role_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  UNIQUE INDEX `uniq_user_name_user_role`(`user_name`, `role_name`) USING BTREE,
  INDEX `fk_role_name_tb_user_role`(`role_name`) USING BTREE,
  CONSTRAINT `fk_role_name_tb_user_role` FOREIGN KEY (`role_name`) REFERENCES `sys_role` (`role_name`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_user_role
-- ----------------------------
INSERT INTO `sys_user_role` VALUES ('admin', 'admin');

SET FOREIGN_KEY_CHECKS = 1;
