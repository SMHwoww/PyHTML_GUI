# 声明：本项目超过95%的内容由AI生成！屎山代码警告！

# pyHTML - 组件化HTML生成器

一个用于快速创建报纸风格HTML页面的Python工具，支持组件化开发、图形化界面和实时预览，同时可以一键通过CloudFlare Worker部署到线上。

## 功能特点

- **组件化开发**：将报纸内容拆分为可复用组件
- **图形化界面**：基于PyQt5的直观GUI
- **实时预览**：快速查看HTML渲染效果
- **HTML/JS生成**：生成可直接部署到CloudFlare的静态文件
- **第三方扩展**：支持加载自定义组件

## 项目结构

```
pyHTML/
├── src/                    # 源代码
│   ├── gui/               # GUI模块
│   ├── core/              # 核心逻辑
│   ├── components/        # 内置组件
│   │   ├── marquee/       # 走马灯组件
│   │   └── headline/      # 标题组件
│   └── utils/             # 工具函数
├── docs/                  # 文档
│   └── 组件开发规范.md   # 组件开发指南
├── examples/              # 示例项目
├── tests/                 # 测试
├── requirements.txt       # 依赖列表
├── SPEC.md               # 项目规范说明
└── README.md             # 项目说明
```

## 文档

- [项目规范说明](SPEC.md)
- [组件开发规范](docs/组件开发规范.md)

## 许可证

本项目使用 MIT 许可证。

```
MIT License

Copyright (c) 2026 SMH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
