<p align="center">
	<img alt="logo" src="https://github.com/luojiaaoo/DashGo/blob/main/logo.png">
</p>
<h1 align="center" style="margin: 30px 0 30px; font-weight: bold;">DashGo</h1>

<p align="center">
简体中文 | <a href="docs/README_en.md">English</a>
</p>

## 简介
DashGo谐音<u>**大西瓜**</u>，这是一个开箱即用的低代码WEB框架，基于Plotly Dash框架和[Fac](https://fac.feffery.tech/getting-started)开源组件库开发，只需要Python语句实现全栈的后台管理系统开发


### 功能:
1. 多页面管理
2. 组件和函数级别的细粒度权限管理
3. 自带用户、角色和团队的权限的管理
5. i18n国际化组件
6. 密码和OTP登录

### 特点:

1. 极易使用
2. 只需要一个Python文件，就可以将应用嵌入系统，无需额外操作
3. 基于Ant的现代UI设计

------

## 项目结构

```
├─assets                # 静态资源目录
│  ├─imgs                  # 图片资源
│  └─js                    # js文件资源（dash框架预加载js文件、浏览器回调js等）
├─common                # Python共享功能库
│  └─utilities          # Python工具类
├─config                # 项目配置目录
├─dash_callback         # Dash回调库
│  ├─application
│  │  ├─access_
│  │  ├─dashboard_
│  │  └─person_
│  └─pages
├─dash_components       # Dash自定义组件
├─dash_view             # Dash视图
│  ├─application           # 应用视图，以“_”结尾的为内置应用
│  │  ├─access_
│  │  ├─dashboard_
│  │  ├─example_app        # 应用例子
│  │  └─person_
│  ├─framework
│  └─pages
├─database              # 数据库
│  └─sql_db             # 关系型数据库配置
│      ├─dao               # 数据库orm抽象
│      └─entity            # 数据库表实体
└─translations          # 国际化
    └─topic_locales
```



## 截图

|![](screenshots/login.png)|![](screenshots/workbench.png)|
| ---- | ---- |
|![](screenshots/moniter.png)|![](screenshots/moniter-en.png)|
|![](screenshots/role.png)|![](screenshots/person.png)|
|![](screenshots/user.png)|![](screenshots/group.png)|



