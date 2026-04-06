using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyHTML.WPF.Services;
using System;
using System.Threading.Tasks;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class ImageSettingsViewModel : ViewModelBase
    {
        private readonly PythonEngineService _pythonService;
        private dynamic? _imageManager;

        [ObservableProperty]
        private string _apiToken = string.Empty;

        [ObservableProperty]
        private bool _isTesting;

        [ObservableProperty]
        private string _testResult = string.Empty;

        [ObservableProperty]
        private bool _testResultIsError;

        public ImageSettingsViewModel()
        {
            _pythonService = PythonEngineService.Instance;
            LoadSettings();
        }

        private void LoadSettings()
        {
            try
            {
                _imageManager = _pythonService.GetImageManager();
                if (_imageManager != null)
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        ApiToken = _imageManager.load_image_api_token() ?? string.Empty;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading image settings: {ex.Message}");
            }
        }

        [RelayCommand]
        private async Task TestConnection()
        {
            if (string.IsNullOrWhiteSpace(ApiToken))
            {
                TestResult = "请输入 API Token";
                TestResultIsError = true;
                return;
            }

            IsTesting = true;
            TestResult = "正在测试连接...";
            TestResultIsError = false;

            try
            {
                await Task.Run(() =>
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        var imageManager = _pythonService.GetImageManager();
                        if (imageManager != null)
                        {
                            // 保存临时token用于测试
                            imageManager.save_image_api_token(ApiToken);
                            
                            // 尝试获取临时token来验证
                            var tempToken = imageManager.get_temp_token(force_refresh: true);
                            
                            if (!string.IsNullOrEmpty(tempToken))
                            {
                                TestResult = "连接成功！API Token 有效。";
                                TestResultIsError = false;
                            }
                            else
                            {
                                TestResult = "连接失败，请检查 API Token 是否正确";
                                TestResultIsError = true;
                            }
                        }
                        else
                        {
                            TestResult = "图片管理器未初始化";
                            TestResultIsError = true;
                        }
                    }
                });
            }
            catch (Exception ex)
            {
                TestResult = $"测试失败: {ex.Message}";
                TestResultIsError = true;
            }
            finally
            {
                IsTesting = false;
            }
        }

        [RelayCommand]
        private void SaveSettings()
        {
            try
            {
                if (_imageManager != null)
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        _imageManager.save_image_api_token(ApiToken);
                    }
                }

                MessageBox.Show("设置已保存！", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"保存设置失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
