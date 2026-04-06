# PyHTML GUI 界面规格说明书

## 1. 项目概述

为 PyHTML WPF 应用程序的菜单栏所有功能创建 GUI 界面。后端功能已实现，需要创建对应的前端界面。

## 2. 功能模块清单

### 2.1 文件菜单 (已实现)
- ✅ 新建项目 (Ctrl+N)
- ✅ 打开项目 (Ctrl+O)
- ✅ 保存 (Ctrl+S)
- ✅ 另存为... (Ctrl+Shift+S)
- ✅ 导出HTML (Ctrl+E)
- ✅ 退出

### 2.2 编辑菜单 (待实现)
- ⏳ 撤销 (Ctrl+Z) - 需要实现撤销栈
- ⏳ 重做 (Ctrl+Y) - 需要实现重做栈
- ⏳ 剪切 (Ctrl+X) - 组件操作
- ⏳ 复制 (Ctrl+C) - 组件操作
- ⏳ 粘贴 (Ctrl+V) - 组件操作
- ⏳ 删除 (Delete) - 组件操作

### 2.3 视图菜单 (部分实现)
- ✅ 预览面板 - 切换显示/隐藏
- ⏳ 刷新预览 (F5) - 强制刷新预览

### 2.4 AI助手菜单 (待实现 GUI)
- ⏳ 打开AI对话 - AI聊天对话框
- ⏳ AI配置 - API配置窗口
- ⏳ 生成网页 - 根据描述生成网页
- ⏳ 优化当前组件 - AI优化选中组件

### 2.5 图片菜单 (待实现 GUI)
- ⏳ 图片设置 - 图床API配置
- ⏳ 图片管理 - 已上传图片管理
- ⏳ AI图片生成 - AI生成图片

### 2.6 部署菜单 (待实现 GUI)
- ⏳ 部署到Cloudflare - 部署向导
- ⏳ Worker配置 - 部署配置

### 2.7 设置菜单 (待实现 GUI)
- ⏳ Head设置 - HTML Head配置
- ⏳ 背景图片设置 - 页面背景设置
- ⏳ 主题设置 - 界面主题切换

### 2.8 帮助菜单 (部分实现)
- ⏳ 使用说明 - 帮助文档窗口
- ⏳ 快捷键 - 快捷键列表
- ✅ 关于 - 关于对话框

## 3. 界面设计规范

### 3.1 视觉风格
- Win11 风格设计
- 圆角矩形 (CornerRadius: 8-12)
- 毛玻璃效果 (Acrylic/Blur)
- 白色主色调 (#FFFFFF)
- 蓝色强调色 (#0078D4)
- 阴影效果

### 3.2 窗口规范
- 最小宽度: 500px
- 最小高度: 400px
- 默认字体: Segoe UI, Microsoft YaHei
- 标题栏: 自定义无边框

### 3.3 控件规范
- 按钮: Win11PrimaryButtonStyle, Win11SecondaryButtonStyle
- 输入框: Win11TextBoxStyle
- 下拉框: Win11ComboBoxStyle
- 复选框: Win11CheckBoxStyle
- 列表: Win11ListBoxStyle

## 4. 窗口详细规格

### 4.1 AI配置窗口 (AIConfigWindow)
**功能**: 配置AI API参数
**尺寸**: 500x400
**内容**:
- API Key 输入框 (密码框)
- API地址输入框 (带默认值)
- 模型选择下拉框 (预设模型列表)
- Tokens最大值输入框 (数字)
- 测试连接按钮
- 保存配置按钮

### 4.2 AI对话窗口 (AIDialogWindow)
**功能**: 与AI对话生成网页
**尺寸**: 700x600
**内容**:
- 聊天记录显示区 (只读)
- 输入框 (多行)
- 发送按钮
- 清空对话按钮
- 导出配置按钮

### 4.3 图片设置窗口 (ImageSettingsWindow)
**功能**: 配置图床API
**尺寸**: 450x300
**内容**:
- API Token输入框
- 测试连接按钮
- 保存按钮

### 4.4 图片管理窗口 (ImageManagerWindow)
**功能**: 管理已上传图片
**尺寸**: 700x500
**内容**:
- 图片列表 (缩略图+信息)
- 上传按钮
- 删除按钮
- 复制链接按钮
- 刷新按钮

### 4.5 Cloudflare部署窗口 (DeployWindow)
**功能**: 部署到Cloudflare Workers
**尺寸**: 600x550
**内容**:
- API Token输入框
- 项目名称输入框
- 自定义域名输入框 (可选)
- 部署日志显示区
- 部署按钮
- 打开项目目录按钮

### 4.6 Head设置窗口 (HeadSettingsWindow)
**功能**: 配置HTML Head
**尺寸**: 600x500
**内容**:
- 页面标题输入框
- 语言选择下拉框
- Meta标签列表 (可添加/删除)
- 自定义CSS输入区
- 自定义JS输入区
- 保存按钮

### 4.7 背景图片设置窗口 (BackgroundSettingsWindow)
**功能**: 设置页面背景
**尺寸**: 500x400
**内容**:
- 背景图片URL输入框
- 或选择本地图片按钮
- 背景重复方式下拉框
- 背景位置选择
- 背景尺寸选择
- 预览区域
- 保存按钮

### 4.8 主题设置窗口 (ThemeSettingsWindow)
**功能**: 切换界面主题
**尺寸**: 450x350
**内容**:
- 主题列表 (卡片式)
- 主题预览
- 应用按钮
- 重置按钮

### 4.9 使用说明窗口 (HelpWindow)
**功能**: 显示帮助文档
**尺寸**: 800x600
**内容**:
- 左侧导航树
- 右侧内容显示区
- 搜索框

### 4.10 快捷键窗口 (ShortcutsWindow)
**功能**: 显示快捷键列表
**尺寸**: 500x500
**内容**:
- 分类列表 (文件、编辑、视图等)
- 快捷键表格
- 导出按钮

## 5. 技术实现要求

### 5.1 架构
- MVVM 模式
- CommunityToolkit.Mvvm
- Python.NET 互操作

### 5.2 文件结构
```
Views/
  ├── AIConfigWindow.xaml
  ├── AIDialogWindow.xaml
  ├── ImageSettingsWindow.xaml
  ├── ImageManagerWindow.xaml
  ├── DeployWindow.xaml
  ├── HeadSettingsWindow.xaml
  ├── BackgroundSettingsWindow.xaml
  ├── ThemeSettingsWindow.xaml
  ├── HelpWindow.xaml
  └── ShortcutsWindow.xaml

ViewModels/
  ├── AIConfigViewModel.cs
  ├── AIDialogViewModel.cs
  ├── ImageSettingsViewModel.cs
  ├── ImageManagerViewModel.cs
  ├── DeployViewModel.cs
  ├── HeadSettingsViewModel.cs
  ├── BackgroundSettingsViewModel.cs
  ├── ThemeSettingsViewModel.cs
  ├── HelpViewModel.cs
  └── ShortcutsViewModel.cs
```

### 5.3 数据绑定
- 使用 ObservableProperty 自动属性
- RelayCommand 命令绑定
- 双向绑定支持

### 5.4 错误处理
- 输入验证
- 错误提示对话框
- 日志记录

## 6. 验收标准

- [ ] 所有菜单项都有对应的GUI界面
- [ ] 界面风格统一，符合Win11设计规范
- [ ] 所有功能与后端正确交互
- [ ] 输入验证完善
- [ ] 错误处理完备
- [ ] 代码结构清晰，符合MVVM模式
