using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using System;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class BackgroundSettingsViewModel : ViewModelBase
    {
        [ObservableProperty]
        private string _backgroundImagePath = string.Empty;

        [ObservableProperty]
        private bool _useBackground = false;

        [ObservableProperty]
        private double _backgroundOpacity = 1.0;

        [ObservableProperty]
        private string _backgroundSize = "cover";

        [ObservableProperty]
        private string _backgroundRepeat = "no-repeat";

        [ObservableProperty]
        private string _backgroundPosition = "center";

        public string[] BackgroundSizeOptions { get; } = new[] { "cover", "contain", "auto", "100% 100%" };
        public string[] BackgroundRepeatOptions { get; } = new[] { "no-repeat", "repeat", "repeat-x", "repeat-y" };
        public string[] BackgroundPositionOptions { get; } = new[] { "center", "top left", "top center", "top right", "center left", "center right", "bottom left", "bottom center", "bottom right" };

        public void LoadFromProject(dynamic? pythonProject)
        {
            if (pythonProject == null) return;

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    var headConfig = pythonProject.head_config;
                    if (headConfig != null)
                    {
                        var backgroundConfig = headConfig.get("background", null);
                        if (backgroundConfig != null)
                        {
                            UseBackground = backgroundConfig.get("enabled", false);
                            BackgroundImagePath = backgroundConfig.get("image_path", "");
                            BackgroundOpacity = backgroundConfig.get("opacity", 1.0);
                            BackgroundSize = backgroundConfig.get("size", "cover");
                            BackgroundRepeat = backgroundConfig.get("repeat", "no-repeat");
                            BackgroundPosition = backgroundConfig.get("position", "center");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading background settings: {ex.Message}");
            }
        }

        public void SaveToProject(dynamic? pythonProject)
        {
            System.Diagnostics.Debug.WriteLine("BackgroundSettingsViewModel.SaveToProject: Starting...");
            
            if (pythonProject == null) 
            {
                System.Diagnostics.Debug.WriteLine("BackgroundSettingsViewModel.SaveToProject: pythonProject is null, aborting.");
                return;
            }

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    System.Diagnostics.Debug.WriteLine("BackgroundSettingsViewModel.SaveToProject: Got GIL.");
                    var headConfig = pythonProject.head_config;
                    System.Diagnostics.Debug.WriteLine($"BackgroundSettingsViewModel.SaveToProject: headConfig type: {headConfig.GetType()}");
                    
                    // 创建Python字典来存储背景配置
                    System.Diagnostics.Debug.WriteLine("BackgroundSettingsViewModel.SaveToProject: Creating Python dict...");
                    dynamic builtins = Python.Runtime.Py.Import("builtins");
                    dynamic pyDict = builtins.dict();
                    pyDict["enabled"] = UseBackground;
                    pyDict["image_path"] = BackgroundImagePath;
                    pyDict["opacity"] = BackgroundOpacity;
                    pyDict["size"] = BackgroundSize;
                    pyDict["repeat"] = BackgroundRepeat;
                    pyDict["position"] = BackgroundPosition;
                    
                    System.Diagnostics.Debug.WriteLine("BackgroundSettingsViewModel.SaveToProject: Assigning to headConfig[\"background\"]...");
                    headConfig["background"] = pyDict;
                    System.Diagnostics.Debug.WriteLine("BackgroundSettingsViewModel.SaveToProject: Success!");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"BackgroundSettingsViewModel.SaveToProject: Exception - {ex.GetType().Name}: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"BackgroundSettingsViewModel.SaveToProject: Stack trace: {ex.StackTrace}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"BackgroundSettingsViewModel.SaveToProject: Inner exception - {ex.InnerException.GetType().Name}: {ex.InnerException.Message}");
                    System.Diagnostics.Debug.WriteLine($"BackgroundSettingsViewModel.SaveToProject: Inner stack trace: {ex.InnerException.StackTrace}");
                }
            }
        }

        [RelayCommand]
        private void BrowseImage()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "图片文件|*.jpg;*.jpeg;*.png;*.gif;*.webp|所有文件|*.*",
                Title = "选择背景图片"
            };

            if (dialog.ShowDialog() == true)
            {
                BackgroundImagePath = dialog.FileName;
                UseBackground = true;
            }
        }

        [RelayCommand]
        private void ClearImage()
        {
            BackgroundImagePath = string.Empty;
            UseBackground = false;
        }

        [RelayCommand]
        private void SaveSettings()
        {
            if (Application.Current.MainWindow is Window window)
            {
                window.Close();
            }
        }
    }
}
