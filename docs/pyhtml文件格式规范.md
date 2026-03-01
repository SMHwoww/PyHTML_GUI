# .pyhtml 文件格式规范

## 概述

.pyhtml 文件是 PyHTML 项目的项目文件，用于保存和加载完整的网页项目。它是一个 JSON 格式的文件，包含项目的基本信息、页面配置和组件列表。

## 文件结构

.pyhtml 文件采用 JSON 格式，包含以下主要字段：

```json
{
  "name": "项目名称",
  "title": "页面标题",
  "head_config": {
    "lang": "语言代码",
    "meta_tags": [
      {
        "name": "标签名称",
        "content": "标签内容"
      }
    ],
    "links": [
      {
        "rel": "关系类型",
        "href": "链接地址"
      }
    ],
    "scripts": [
      {
        "src": "脚本地址",
        "type": "脚本类型"
      }
    ]
  },
  "components": [
    {
      "component_name": "组件唯一标识",
      "values": {
        "字段名称": "字段值"
      }
    }
  ]
}
```

## 字段说明

### 1. 基本信息

- **name** (字符串，必需)：项目的唯一标识符，用于在文件系统中识别项目。
- **title** (字符串，必需)：页面的标题，将显示在浏览器标签页上。

### 2. 头部配置 (head_config)

包含 HTML `<head>` 部分的配置信息：

- **lang** (字符串，可选)：页面的语言代码，默认为 "zh-CN"。
- **meta_tags** (数组，可选)：Meta 标签列表，每个标签包含 `name` 和 `content` 字段。
- **links** (数组，可选)：外部资源链接列表，如 CSS 文件、图标等。
- **scripts** (数组，可选)：外部脚本链接列表，如 JavaScript 文件。

### 3. 组件列表 (components)

包含页面中所有组件的配置信息，每个组件是一个对象，包含：

- **component_name** (字符串，必需)：组件的唯一标识符，对应组件目录中的 `name` 字段。
- **values** (对象，必需)：组件的配置值，键为字段名，值为字段值。

## 示例

以下是一个完整的 .pyhtml 文件示例：

```json
{
  "name": "my-website",
  "title": "我的个人网站",
  "head_config": {
    "lang": "zh-CN",
    "meta_tags": [
      {
        "name": "charset",
        "content": "UTF-8"
      },
      {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1.0"
      },
      {
        "name": "description",
        "content": "这是我的个人网站"
      }
    ],
    "links": [
      {
        "rel": "icon",
        "href": "favicon.ico"
      }
    ],
    "scripts": []
  },
  "components": [
    {
      "component_name": "navigation",
      "values": {
        "bg_color": "#333333",
        "text_color": "#ffffff",
        "font": "Arial",
        "items": [
          {"text": "首页", "link": "#"},
          {"text": "关于我", "link": "#about"},
          {"text": "联系方式", "link": "#contact"}
        ],
        "hover_color": "#555555",
        "active_color": "#007bff"
      }
    },
    {
      "component_name": "headline",
      "values": {
        "text": "欢迎来到我的个人网站",
        "level": "h1",
        "align": "center",
        "color": "#333333",
        "font_family": "SimHei"
      }
    },
    {
      "component_name": "article",
      "values": {
        "title": "关于我",
        "content": "我是一名网页开发者，热爱创造美观实用的网站。",
        "author": "张三",
        "date": "2023-01-01",
        "text_color": "#333333",
        "bg_color": "#ffffff",
        "font_family": "SimSun"
      }
    }
  ]
}
```

## 最佳实践

1. **保持简洁**：只包含必要的字段，避免冗余信息。
2. **使用有意义的名称**：项目名称和组件名称应该具有描述性。
3. **保持一致性**：组件名称必须与组件目录中的 `name` 字段一致。
4. **验证格式**：确保文件是有效的 JSON 格式。
5. **备份文件**：定期备份 .pyhtml 文件，以防止意外丢失。

## 注意事项

- .pyhtml 文件不包含 `component_dir` 字段，只使用 `component_name` 作为组件的唯一标识符。
- 组件的实际目录路径由应用程序根据 `component_name` 自动查找。
- 当加载项目时，应用程序会使用 `component_name` 从组件库中加载相应的组件。

## 版本兼容性

- 此格式适用于 PyHTML v1.0 及以上版本。
- 旧版本的 .pyhtml 文件可能包含 `component_dir` 字段，应用程序会自动忽略这些字段并使用 `component_name` 加载组件。
