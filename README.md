# 声明：本项目超过95%的内容由AI生成！屎山代码警告！

# pyHTML - 组件化HTML生成器

一个用于快速创建HTML页面的工具，支持组件化开发、图形化界面、实时预览和AI生成，同时可以一键通过CloudFlare Worker部署到线上。

## 技术架构

- **GUI 框架**: WPF (Windows Presentation Foundation) - .NET 8.0
- **Python 集成**: Python.NET (pythonnet) 3.0.3
- **架构模式**: MVVM (Model-View-ViewModel)
- **预览引擎**: WebView2

## 功能特点

- **组件化开发**：将报纸内容拆分为可复用组件
- **图形化界面**：基于 WPF 的现代化 GUI
- **实时预览**：使用 WebView2 快速查看HTML渲染效果
- **HTML生成**：生成可直接加载到浏览器的HTML文件
- **第三方扩展**：支持加载自定义组件
- **CloudFlare支持**：支持一键部署至CloudFlare的worker，实现在线预览
- **AI自动生成**：支持使用AI快速生成网页

## 快速开始

### 1. 安装依赖

#### Python 依赖

```bash
pip install -r requirements.txt
```

#### .NET 依赖

需要安装 .NET 8.0 SDK:
<https://dotnet.microsoft.com/download/dotnet/8.0>

### 2. 构建和运行

```bash
# 还原 NuGet 包
dotnet restore

# 构建项目
dotnet build

# 运行程序
dotnet run
```

### 3. 配置 Python 路径

如果 Python.NET 无法自动找到 Python DLL，请设置环境变量：

```powershell
$env:PYTHONNET_PYDLL = "C:\Python311\python311.dll"
```

### 4. 基本使用

#### 手动创建网页

1. 从左侧组件库中拖拽或双击组件到页面
2. 在右侧属性面板中编辑组件属性
3. 点击"预览"按钮查看效果
4. 点击"导出HTML"保存为HTML文件

#### 使用AI生成网页

1. 点击菜单栏 "AI助手" -> "打开AI对话"
2. 在API配置标签页中输入阿里云百炼API Key
3. 选择合适的模型（推荐 qwen3-max 或 qwen3.5-plus）
4. 点击"测试连接"验证API配置
5. 在AI对话标签页中描述您想要的网页
6. AI会自动分析需求并选择合适的组件
7. 生成的项目会自动加载到编辑器中

### 5. 部署到CloudFlare

1. 点击"文件" -> "部署Cloudflare Worker"
2. 选择保存目录
3. 输入Cloudflare API Token（或使用环境变量）
4. 点击"确定"开始部署
5. 部署完成后会自动打开在线地址

## 项目结构

```
PyHTML_GUI/
├── App.xaml                     # WPF 应用程序入口
├── App.xaml.cs
├── MainWindow.xaml              # 主窗口
├── MainWindow.xaml.cs
├── Views/                       # 视图
│   └── PreviewWindow.xaml
├── ViewModels/                  # 视图模型 (MVVM)
│   ├── MainViewModel.cs
│   ├── ComponentViewModel.cs
│   ├── PropertyViewModel.cs
│   └── ViewModelBase.cs
├── Services/                    # 服务
│   └── PythonEngineService.cs
├── Converters/                  # 值转换器
│   └── NullToVisibilityConverter.cs
├── Styles/                      # 样式资源
│   └── DefaultTheme.xaml
├── src/
│   ├── core/                    # Python 业务逻辑
│   │   ├── project.py           # 项目管理
│   │   ├── component.py         # 组件系统
│   │   ├── generator.py         # HTML 生成器
│   │   ├── ai_client.py         # AI 客户端
│   │   ├── cloudflare_worker.py # Cloudflare Worker 部署
│   │   ├── image_manager.py     # 图片管理
│   │   └── preview_server.py    # 预览服务器
│   ├── components/              # 组件定义
│   └── themes/                  # 主题文件
├── PyHTML_GUI_NET.sln           # 解决方案文件
├── PyHTML.WPF.csproj            # 项目文件
└── requirements.txt             # Python 依赖
```

<br />

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

