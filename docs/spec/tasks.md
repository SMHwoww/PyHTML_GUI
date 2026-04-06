# PyHTML GUI 界面开发任务列表

## 阶段一：AI助手功能 GUI (优先级：高)

### Task 1.1: AI配置窗口
- [ ] 创建 AIConfigWindow.xaml
- [ ] 创建 AIConfigViewModel.cs
- [ ] 实现 API Key 输入框 (密码显示)
- [ ] 实现 API地址输入框
- [ ] 实现模型选择下拉框
- [ ] 实现 Tokens最大值输入框
- [ ] 实现测试连接功能
- [ ] 实现保存配置功能
- [ ] 集成到主窗口菜单

### Task 1.2: AI对话窗口
- [ ] 创建 AIDialogWindow.xaml
- [ ] 创建 AIDialogViewModel.cs
- [ ] 实现聊天记录显示区
- [ ] 实现用户输入框
- [ ] 实现发送消息功能
- [ ] 实现清空对话功能
- [ ] 实现导出配置功能
- [ ] 集成到主窗口菜单

## 阶段二：图片功能 GUI (优先级：高)

### Task 2.1: 图片设置窗口
- [ ] 创建 ImageSettingsWindow.xaml
- [ ] 创建 ImageSettingsViewModel.cs
- [ ] 实现 API Token 输入框
- [ ] 实现测试连接功能
- [ ] 实现保存配置功能
- [ ] 集成到主窗口菜单

### Task 2.2: 图片管理窗口
- [ ] 创建 ImageManagerWindow.xaml
- [ ] 创建 ImageManagerViewModel.cs
- [ ] 实现图片列表显示
- [ ] 实现上传图片功能
- [ ] 实现删除图片功能
- [ ] 实现复制链接功能
- [ ] 实现刷新列表功能
- [ ] 集成到主窗口菜单

## 阶段三：部署功能 GUI (优先级：中)

### Task 3.1: Cloudflare部署窗口
- [ ] 创建 DeployWindow.xaml
- [ ] 创建 DeployViewModel.cs
- [ ] 实现 API Token 输入框
- [ ] 实现项目名称输入框
- [ ] 实现自定义域名输入框
- [ ] 实现部署日志显示区
- [ ] 实现部署功能
- [ ] 实现打开项目目录功能
- [ ] 集成到主窗口菜单

## 阶段四：设置功能 GUI (优先级：中)

### Task 4.1: Head设置窗口
- [ ] 创建 HeadSettingsWindow.xaml
- [ ] 创建 HeadSettingsViewModel.cs
- [ ] 实现页面标题输入框
- [ ] 实现语言选择下拉框
- [ ] 实现 Meta标签管理
- [ ] 实现自定义CSS输入区
- [ ] 实现自定义JS输入区
- [ ] 集成到主窗口菜单

### Task 4.2: 背景图片设置窗口
- [ ] 创建 BackgroundSettingsWindow.xaml
- [ ] 创建 BackgroundSettingsViewModel.cs
- [ ] 实现背景图片URL输入框
- [ ] 实现本地图片选择按钮
- [ ] 实现背景重复方式选择
- [ ] 实现背景位置选择
- [ ] 实现背景尺寸选择
- [ ] 实现预览功能
- [ ] 集成到主窗口菜单

### Task 4.3: 主题设置窗口
- [ ] 创建 ThemeSettingsWindow.xaml
- [ ] 创建 ThemeSettingsViewModel.cs
- [ ] 实现主题列表显示
- [ ] 实现主题预览
- [ ] 实现应用主题功能
- [ ] 实现重置功能
- [ ] 集成到主窗口菜单

## 阶段五：帮助功能 GUI (优先级：低)

### Task 5.1: 使用说明窗口
- [ ] 创建 HelpWindow.xaml
- [ ] 创建 HelpViewModel.cs
- [ ] 实现左侧导航树
- [ ] 实现右侧内容显示
- [ ] 实现搜索功能
- [ ] 集成到主窗口菜单

### Task 5.2: 快捷键窗口
- [ ] 创建 ShortcutsWindow.xaml
- [ ] 创建 ShortcutsViewModel.cs
- [ ] 实现快捷键列表显示
- [ ] 实现分类筛选
- [ ] 实现导出功能
- [ ] 集成到主窗口菜单

## 阶段六：编辑功能 (优先级：低)

### Task 6.1: 撤销/重做功能
- [ ] 实现撤销栈
- [ ] 实现重做栈
- [ ] 实现撤销命令
- [ ] 实现重做命令
- [ ] 集成到主窗口菜单

### Task 6.2: 剪切/复制/粘贴功能
- [ ] 实现组件剪切功能
- [ ] 实现组件复制功能
- [ ] 实现组件粘贴功能
- [ ] 实现组件删除功能
- [ ] 集成到主窗口菜单

## 阶段七：视图功能 (优先级：低)

### Task 7.1: 刷新预览功能
- [ ] 实现强制刷新预览功能
- [ ] 集成到主窗口菜单

## 依赖关系

```
阶段一 (AI助手)
    └── 依赖: ai_client.py ✅

阶段二 (图片功能)
    └── 依赖: image_manager.py ✅

阶段三 (部署功能)
    └── 依赖: cloudflare_worker.py ✅

阶段四 (设置功能)
    └── 依赖: project.py ✅

阶段五 (帮助功能)
    └── 依赖: 无 (静态内容)

阶段六 (编辑功能)
    └── 依赖: 需要新增撤销栈实现

阶段七 (视图功能)
    └── 依赖: preview_server.py ✅
```

## 开发顺序建议

1. **第一周**: 阶段一 (AI助手) + 阶段二 (图片功能)
2. **第二周**: 阶段三 (部署功能) + 阶段四 (设置功能)
3. **第三周**: 阶段五 (帮助功能) + 阶段六 (编辑功能) + 阶段七 (视图功能)

## 每个任务的开发步骤

对于每个窗口开发任务，按以下步骤进行：

1. **创建 ViewModel**
   - 继承 ViewModelBase
   - 定义 ObservableProperty 属性
   - 实现 RelayCommand 命令
   - 实现与 Python 后端的交互

2. **创建 View (XAML)**
   - 设置窗口基本属性
   - 应用 Win11WindowStyle
   - 布局控件
   - 绑定 ViewModel

3. **创建 View Code-Behind**
   - 实现构造函数
   - 实现窗口关闭处理

4. **集成到主窗口**
   - 在 MainViewModel 添加打开窗口命令
   - 在 MainWindow.xaml 绑定菜单项

5. **测试验证**
   - 功能测试
   - 界面风格检查
   - 错误处理验证
