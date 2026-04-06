using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using PyHTML.WPF.Services;
using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class MainViewModel : ViewModelBase
    {
        private readonly PythonEngineService _pythonService;

        [ObservableProperty]
        private string _windowTitle = "pyHTML - 组件化HTML生成器";

        [ObservableProperty]
        private string _projectName = "未命名项目";

        [ObservableProperty]
        private string? _projectFilePath;

        [ObservableProperty]
        private bool _isProjectModified;

        [ObservableProperty]
        private ComponentLibraryViewModel _componentLibrary = new();

        [ObservableProperty]
        private ObservableCollection<ComponentViewModel> _pageComponents = new();

        [ObservableProperty]
        private ComponentViewModel? _selectedComponent;

        [ObservableProperty]
        private string _previewHtml = string.Empty;

        [ObservableProperty]
        private bool _isPreviewVisible = true;

        [ObservableProperty]
        private ComponentViewModel? _copiedComponent;

        private dynamic? _pythonProject;
        private dynamic? _componentLoader;

        public dynamic? PythonProject => _pythonProject;

        public MainViewModel()
        {
            _pythonService = PythonEngineService.Instance;
            InitializeAsync();
        }

        private async void InitializeAsync()
        {
            await ExecuteAsync(async () =>
            {
                await Task.Run(() =>
                {
                    _pythonService.Initialize();
                    _componentLoader = _pythonService.GetComponentLoader();
                });

                LoadComponentLibrary();
                CreateNewProject();
            }, "正在初始化...");
        }

        private void LoadComponentLibrary()
        {
            if (_componentLoader != null)
            {
                ComponentLibrary.LoadComponents(_componentLoader);
            }
        }

        [RelayCommand]
        private void CreateNewProject()
        {
            Execute(() =>
            {
                _pythonProject = _pythonService.CreateProject("未命名项目");
                ProjectName = "未命名项目";
                ProjectFilePath = null;
                IsProjectModified = false;
                PageComponents.Clear();
                SelectedComponent = null;
                UpdatePreview();
                StatusMessage = "新项目已创建";
            });
        }

        [RelayCommand]
        private void OpenProject()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "pyHTML项目 (*.pyhtml)|*.pyhtml|所有文件 (*.*)|*.*",
                Title = "打开项目"
            };

            if (dialog.ShowDialog() == true)
            {
                Execute(() =>
                {
                    _pythonProject = _pythonService.LoadProject(dialog.FileName);
                    ProjectFilePath = dialog.FileName;
                    ProjectName = Path.GetFileNameWithoutExtension(dialog.FileName);
                    IsProjectModified = false;

                    LoadPageComponents();
                    UpdatePreview();
                    StatusMessage = $"项目已打开: {ProjectName}";
                }, "正在打开项目...");
            }
        }

        [RelayCommand]
        private void SaveProject()
        {
            if (string.IsNullOrEmpty(ProjectFilePath))
            {
                SaveProjectAs();
                return;
            }

            Execute(() =>
            {
                SaveProjectInternal(ProjectFilePath);
            }, "正在保存...");
        }

        [RelayCommand]
        private void SaveProjectAs()
        {
            var dialog = new SaveFileDialog
            {
                Filter = "pyHTML项目 (*.pyhtml)|*.pyhtml|所有文件 (*.*)|*.*",
                Title = "保存项目",
                FileName = ProjectName
            };

            if (dialog.ShowDialog() == true)
            {
                Execute(() =>
                {
                    SaveProjectInternal(dialog.FileName);
                    ProjectFilePath = dialog.FileName;
                    ProjectName = Path.GetFileNameWithoutExtension(dialog.FileName);
                }, "正在保存...");
            }
        }

        private void SaveProjectInternal(string filePath)
        {
            if (_pythonProject != null)
            {
                using (Python.Runtime.Py.GIL())
                {
                    _pythonProject.save(filePath);
                }
                IsProjectModified = false;
                StatusMessage = $"项目已保存: {ProjectName}";
            }
        }

        [RelayCommand]
        private void ExportHtml()
        {
            var dialog = new SaveFileDialog
            {
                Filter = "HTML文件 (*.html)|*.html|所有文件 (*.*)|*.*",
                Title = "导出HTML",
                FileName = $"{ProjectName}.html"
            };

            if (dialog.ShowDialog() == true)
            {
                Execute(() =>
                {
                    if (_pythonProject != null)
                    {
                        _pythonService.SaveHTML(_pythonProject, dialog.FileName);
                        StatusMessage = $"HTML已导出: {dialog.FileName}";
                    }
                }, "正在导出HTML...");
            }
        }

        [RelayCommand]
        private void AddComponent(ComponentViewModel? component)
        {
            if (component == null) return;

            Execute(() =>
            {
                var newComponent = new ComponentViewModel
                {
                    Name = component.Name,
                    DisplayName = component.DisplayName,
                    Description = component.Description,
                    Category = component.Category,
                    Properties = new System.Collections.Generic.Dictionary<string, object>(component.Properties),
                    Order = PageComponents.Count
                };

                if (_pythonProject != null && _componentLoader != null)
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        var pyComponent = _componentLoader.create_component(component.Name);
                        newComponent.PythonComponent = pyComponent;
                        _pythonProject.add_component(pyComponent);
                    }
                }

                PageComponents.Add(newComponent);
                IsProjectModified = true;
                UpdatePreview();
                StatusMessage = $"已添加组件: {newComponent.DisplayName}";
            });
        }

        [RelayCommand]
        private void RemoveComponent(ComponentViewModel? component)
        {
            if (component == null) return;

            Execute(() =>
            {
                if (_pythonProject != null && component.PythonComponent != null)
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        _pythonProject.remove_component(component.PythonComponent);
                    }
                }

                PageComponents.Remove(component);
                if (SelectedComponent == component)
                    SelectedComponent = null;

                ReorderComponents();
                IsProjectModified = true;
                UpdatePreview();
                StatusMessage = "组件已删除";
            });
        }

        [RelayCommand]
        private void CopyComponent()
        {
            if (SelectedComponent != null)
            {
                CopiedComponent = SelectedComponent;
                StatusMessage = $"已复制组件: {SelectedComponent.DisplayName}";
            }
        }

        [RelayCommand]
        private void PasteComponent()
        {
            if (CopiedComponent == null) return;

            Execute(() =>
            {
                var newComponent = new ComponentViewModel
                {
                    Name = CopiedComponent.Name,
                    DisplayName = CopiedComponent.DisplayName,
                    Description = CopiedComponent.Description,
                    Category = CopiedComponent.Category,
                    Properties = new Dictionary<string, object>(CopiedComponent.Properties),
                    Order = PageComponents.Count
                };

                if (_pythonProject != null && _componentLoader != null)
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        var pyComponent = _componentLoader.create_component(CopiedComponent.Name);
                        if (pyComponent != null)
                        {
                            foreach (var kvp in CopiedComponent.Properties)
                            {
                                pyComponent.set_value(kvp.Key, kvp.Value);
                            }
                            newComponent.PythonComponent = pyComponent;
                            _pythonProject.add_component(pyComponent);
                        }
                    }
                }

                PageComponents.Add(newComponent);
                IsProjectModified = true;
                UpdatePreview();
                StatusMessage = $"已粘贴组件: {newComponent.DisplayName}";
            });
        }

        [RelayCommand]
        private void MoveComponentUp(ComponentViewModel? component)
        {
            if (component == null) return;

            var index = PageComponents.IndexOf(component);
            if (index > 0)
            {
                Execute(() =>
                {
                    PageComponents.Move(index, index - 1);
                    ReorderComponents();
                    IsProjectModified = true;
                    UpdatePreview();
                });
            }
        }

        [RelayCommand]
        private void MoveComponentDown(ComponentViewModel? component)
        {
            if (component == null) return;

            var index = PageComponents.IndexOf(component);
            if (index < PageComponents.Count - 1)
            {
                Execute(() =>
                {
                    PageComponents.Move(index, index + 1);
                    ReorderComponents();
                    IsProjectModified = true;
                    UpdatePreview();
                });
            }
        }

        [RelayCommand]
        private void TogglePreview()
        {
            Execute(() =>
            {
                if (_pythonProject != null)
                {
                    var html = _pythonService.GenerateHTML(_pythonProject);
                    var previewWindow = new Views.PreviewWindow
                    {
                        Owner = Application.Current.MainWindow
                    };
                    previewWindow.SetHtmlContent(html);
                    previewWindow.Show();
                }
            });
        }

        [RelayCommand]
        private void ShowAbout()
        {
            MessageBox.Show(
                "pyHTML - 组件化HTML生成器\n\n版本: v0.6.0 (.NET WPF Edition)\n\n使用 WPF + Python.NET 技术构建",
                "关于",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }

        [RelayCommand]
        private void Exit()
        {
            if (IsProjectModified)
            {
                var result = MessageBox.Show(
                    "项目有未保存的更改，是否保存？",
                    "确认退出",
                    MessageBoxButton.YesNoCancel,
                    MessageBoxImage.Question);

                if (result == MessageBoxResult.Yes)
                {
                    SaveProject();
                }
                else if (result == MessageBoxResult.Cancel)
                {
                    return;
                }
            }

            Application.Current.Shutdown();
        }

        // ==================== AI助手菜单命令 ====================
        [RelayCommand]
        private void OpenAIConfig()
        {
            var window = new Views.AIConfigWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();
        }

        [RelayCommand]
        private void OpenAIDialog()
        {
            var window = new Views.AIDialogWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.Show();
        }

        // ==================== 图片菜单命令 ====================
        [RelayCommand]
        private void OpenImageSettings()
        {
            var window = new Views.ImageSettingsWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();
        }

        [RelayCommand]
        private void OpenImageManager()
        {
            var window = new Views.ImageManagerWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();
        }

        // ==================== 部署菜单命令 ====================
        [RelayCommand]
        private void OpenDeployWindow()
        {
            var window = new Views.DeployWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();
        }

        // ==================== 设置菜单命令 ====================
        [RelayCommand]
        private void OpenHeadSettings()
        {
            var window = new Views.HeadSettingsWindow
            {
                Owner = Application.Current.MainWindow
            };
            
            if (window.DataContext is ViewModels.HeadSettingsViewModel vm)
            {
                vm.LoadFromProject(_pythonProject);
            }
            
            window.ShowDialog();
            
            if (window.DataContext is ViewModels.HeadSettingsViewModel headVm)
            {
                headVm.SaveToProject(_pythonProject);
                IsProjectModified = true;
                UpdatePreview();
            }
        }

        [RelayCommand]
        private void OpenBackgroundSettings()
        {
            var window = new Views.BackgroundSettingsWindow
            {
                Owner = Application.Current.MainWindow
            };
            
            if (window.DataContext is ViewModels.BackgroundSettingsViewModel vm)
            {
                vm.LoadFromProject(_pythonProject);
            }
            
            window.ShowDialog();
            
            if (window.DataContext is ViewModels.BackgroundSettingsViewModel bgVm)
            {
                bgVm.SaveToProject(_pythonProject);
                IsProjectModified = true;
                UpdatePreview();
            }
        }

        [RelayCommand]
        private void OpenThemeSettings()
        {
            var window = new Views.ThemeSettingsWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();
        }

        // ==================== 帮助菜单命令 ====================
        [RelayCommand]
        private void OpenHelpWindow()
        {
            var window = new Views.HelpWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();
        }

        [RelayCommand]
        private void OpenShortcutsWindow()
        {
            var window = new Views.ShortcutsWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();
        }

        private void LoadPageComponents()
        {
            PageComponents.Clear();

            if (_pythonProject != null)
            {
                using (Python.Runtime.Py.GIL())
                {
                    var components = _pythonProject.components;
                    foreach (var comp in components)
                    {
                        var vm = new ComponentViewModel
                        {
                            PythonComponent = comp
                        };
                        PageComponents.Add(vm);
                    }
                }
            }
        }

        private void ReorderComponents()
        {
            for (int i = 0; i < PageComponents.Count; i++)
            {
                PageComponents[i].Order = i;
            }
        }

        private void UpdatePreview()
        {
            if (_pythonProject != null)
            {
                try
                {
                    System.Diagnostics.Debug.WriteLine("UpdatePreview: Starting HTML generation...");
                    PreviewHtml = _pythonService.GenerateHTML(_pythonProject);
                    System.Diagnostics.Debug.WriteLine("UpdatePreview: HTML generation complete.");
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"UpdatePreview: Error generating preview - {ex.GetType().Name}: {ex.Message}");
                    System.Diagnostics.Debug.WriteLine($"UpdatePreview: Stack trace: {ex.StackTrace}");
                    if (ex.InnerException != null)
                    {
                        System.Diagnostics.Debug.WriteLine($"UpdatePreview: Inner exception - {ex.InnerException.GetType().Name}: {ex.InnerException.Message}");
                        System.Diagnostics.Debug.WriteLine($"UpdatePreview: Inner stack trace: {ex.InnerException.StackTrace}");
                    }
                }
            }
            else
            {
                System.Diagnostics.Debug.WriteLine("UpdatePreview: _pythonProject is null, skipping.");
            }
        }

        partial void OnSelectedComponentChanged(ComponentViewModel? value)
        {
            if (value != null)
            {
                StatusMessage = $"选中组件: {value.DisplayName}";
            }
        }
    }
}
