using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyHTML.WPF.Services;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class AIConfigViewModel : ViewModelBase
    {
        private readonly PythonEngineService _pythonService;
        private dynamic? _aiClient;

        [ObservableProperty]
        private string _apiKey = string.Empty;

        [ObservableProperty]
        private string _baseUrl = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions";

        [ObservableProperty]
        private string _selectedModel = "qwen-max";

        [ObservableProperty]
        private int _maxTokens = 8192;

        [ObservableProperty]
        private bool _isTesting;

        [ObservableProperty]
        private string _testResult = string.Empty;

        [ObservableProperty]
        private bool _testResultIsError;

        public List<string> AvailableModels { get; } = new()
        {
            "qwen3-max-preview",
            "qwen3-max-2025-09-23",
            "qwen3-max-2026-01-23",
            "qwen3-max",
            "qwen-plus-2025-04-28",
            "qwen-plus-2025-07-14",
            "qwen-plus-2025-07-28",
            "qwen-plus-2025-09-11",
            "qwen-plus-2025-12-01",
            "qwen-plus-latest",
            "qwen-plus",
            "qwen3.5-plus-2026-02-15",
            "qwen3.5-plus",
            "qwen-flash-2025-07-28",
            "qwen-flash",
            "qwen3.5-flash-2026-02-23",
            "qwen3.5-flash",
            "qwen-turbo-2025-04-28",
            "qwen-turbo-2025-07-15",
            "qwen-turbo-latest",
            "qwen-turbo"
        };

        public AIConfigViewModel()
        {
            _pythonService = PythonEngineService.Instance;
            LoadConfig();
        }

        private void LoadConfig()
        {
            try
            {
                _aiClient = _pythonService.GetAIClient();
                if (_aiClient != null)
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        ApiKey = _aiClient.api_key ?? string.Empty;
                        BaseUrl = _aiClient.base_url ?? BaseUrl;
                        SelectedModel = _aiClient.model ?? SelectedModel;
                        MaxTokens = _aiClient.max_tokens ?? 8192;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading AI config: {ex.Message}");
            }
        }

        [RelayCommand]
        private async Task TestConnection()
        {
            if (string.IsNullOrWhiteSpace(ApiKey))
            {
                TestResult = "请输入 API Key";
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
                        var testClient = _pythonService.GetAIClient();
                        if (testClient != null)
                        {
                            // 创建临时客户端测试连接
                            dynamic tempClient = _pythonService.GetAIClient();
                            tempClient.api_key = ApiKey;
                            tempClient.model = SelectedModel;
                            tempClient.base_url = BaseUrl;
                            tempClient.max_tokens = MaxTokens;

                            bool success = tempClient.test_connection();
                            if (success)
                            {
                                TestResult = "连接成功！";
                                TestResultIsError = false;
                            }
                            else
                            {
                                TestResult = "连接失败，请检查 API Key 是否正确";
                                TestResultIsError = true;
                            }
                        }
                        else
                        {
                            TestResult = "AI 客户端未初始化";
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
        private void SaveConfig()
        {
            try
            {
                if (string.IsNullOrWhiteSpace(ApiKey))
                {
                    MessageBox.Show("请输入 API Key", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                using (Python.Runtime.Py.GIL())
                {
                    var client = _pythonService.GetAIClient();
                    if (client != null)
                    {
                        client.save_config(ApiKey, SelectedModel, BaseUrl, MaxTokens);
                    }
                }

                MessageBox.Show("配置已保存！", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"保存配置失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
