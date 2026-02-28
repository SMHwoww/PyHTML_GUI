# pyHTML 项目规范说明书

## 1. 项目概述

**项目名称：** pyHTML - 报纸组件化HTML生成器
**目标：** 通过Python生成HTML页面和CloudFlare兼容的JS文件，提供图形化界面，支持组件化开发和实时预览

## 2. 需求分析

### 2.1 核心需求
1. **组件化开发**：将报纸内容拆分为可复用组件
2. **图形化界面**：提供GUI界面进行内容编辑和预览
3. **实时预览**：快速查看HTML渲染效果
4. **HTML/JS生成**：生成可部署到CloudFlare的静态文件
5. **第三方扩展**：支持加载自定义组件
6. **零依赖启动**：所有库可选择安装，提供依赖名单

### 2.2 非功能需求
- **易用性**：GUI操作简单直观
- **可扩展性**：清晰的组件开发规范
- **跨平台**：在Windows/Linux/macOS上可运行

## 3. 系统架构设计

### 3.1 技术栈选择

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| GUI框架 | PyQt5/PySide6 | 功能强大，跨平台，上限高 |
| 模板引擎 | Jinja2 | 灵活的HTML模板渲染 |
| 实时预览 | http.server + 浏览器 | Python内置HTTP服务器 |
| 文件格式 | JSON/YAML | 组件配置和项目存储 |

### 3.2 依赖名单（可选安装）

```
PyQt5>=5.15.0
Jinja2>=3.0.0
PyYAML>=6.0
```

### 3.3 目录结构

```
pyHTML/
├── src/
│   ├── __init__.py
│   ├── main.py              # 入口文件
│   ├── gui/                 # GUI模块
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── component_editor.py
│   │   └── preview_panel.py
│   ├── core/                # 核心逻辑
│   │   ├── __init__.py
│   │   ├── component.py     # 组件基类
│   │   ├── generator.py     # HTML生成器
│   │   ├── project.py       # 项目管理
│   │   └── preview_server.py
│   ├── components/          # 内置组件
│   │   ├── __init__.py
│   │   ├── marquee/
│   │   ├── headline/
│   │   ├── article/
│   │   └── image/
│   └── utils/
│       ├── __init__.py
│       └── template_loader.py
├── tests/
├── docs/
│   └── 组件开发规范.md
├── examples/
├── requirements.txt
└── README.md
```

## 4. 功能规格说明

### 4.1 组件系统

#### 组件结构
每个组件包含：
- `template.html` - HTML模板（Jinja2格式）
- `style.css` - 样式文件（可选）
- `script.js` - JavaScript（可选）
- `config.json` - 组件配置定义

#### 配置文件示例
```json
{
  "name": "marquee",
  "display_name": "走马灯",
  "version": "1.0.0",
  "fields": [
    {
      "name": "text",
      "type": "string",
      "label": "滚动文本",
      "default": "这是一段滚动文字"
    },
    {
      "name": "speed",
      "type": "number",
      "label": "滚动速度",
      "default": 5,
      "min": 1,
      "max": 20
    }
  ]
}
```

#### 模板示例
```html
<div class="marquee-component">
  <marquee scrollamount="{{ speed }}">{{ text }}</marquee>
</div>
```

### 4.2 GUI功能

| 功能模块 | 功能说明 |
|----------|----------|
| 项目管理 | 新建/打开/保存项目 |
| 组件库面板 | 显示可用组件，支持拖拽添加 |
| 页面编辑器 | 可视化排列组件顺序 |
| 属性编辑 | 编辑选中组件的配置参数 |
| 预览面板 | 实时显示HTML渲染效果 |
| 导出功能 | 导出HTML和JS文件 |

### 4.3 实时预览机制
- Python内置HTTP服务器运行在随机端口
- 文件变更时自动刷新预览
- 支持热重载

## 5. 第三方开发规范

### 5.1 组件开发步骤
1. 创建组件文件夹
2. 编写 `config.json` 配置文件
3. 编写 `template.html` 模板
4. 可选：添加CSS和JS
5. 放入 `components/` 目录或通过GUI加载

### 5.2 组件命名规范
- 使用小写字母和下划线
- 具有描述性，如 `weather_widget`
- 避免与内置组件重名

## 6. 验收标准

### 6.1 功能验收
- [ ] GUI可以正常启动和运行
- [ ] 可以添加、编辑、删除组件
- [ ] 实时预览功能正常工作
- [ ] 可以导出HTML和JS文件
- [ ] 支持加载第三方组件

### 6.2 代码质量
- [ ] 代码结构清晰，模块划分合理
- [ ] 遵循PEP 8规范
- [ ] 提供基础注释说明

## 7. 里程碑计划

| 阶段 | 交付内容 |
|------|----------|
| 阶段1 | 项目框架搭建，基础GUI |
| 阶段2 | 组件系统实现，内置组件 |
| 阶段3 | 预览和导出功能 |
| 阶段4 | 第三方组件支持和文档 |
