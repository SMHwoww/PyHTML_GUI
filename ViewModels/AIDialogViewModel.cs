using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyHTML.WPF.Services;
using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class ChatMessage : ObservableObject
    {
        [ObservableProperty]
        private string _role = "user"; // user, assistant, system

        [ObservableProperty]
        private string _content = string.Empty;

        [ObservableProperty]
        private DateTime _timestamp = DateTime.Now;

        [ObservableProperty]
        private bool _isError;

        public bool IsUser => Role == "user";
        public bool IsAssistant => Role == "assistant";
    }

    public partial class AIDialogViewModel : ViewModelBase
    {
        private readonly PythonEngineService _pythonService;
        private dynamic? _aiClient;

        [ObservableProperty]
        private string _userInput = string.Empty;

        [ObservableProperty]
        private ObservableCollection<ChatMessage> _messages = new();

        [ObservableProperty]
        private bool _isSending;

        [ObservableProperty]
        private string _statusText = "准备就绪";

        [ObservableProperty]
        private bool _hasApiKey;

        public AIDialogViewModel()
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
                    _aiClient = _pythonService.GetAIClient();
                    if (_aiClient != null)
                    {
                        using (Python.Runtime.Py.GIL())
                        {
                            HasApiKey = !string.IsNullOrEmpty(_aiClient.api_key);
                        }
                    }
                });

                if (!HasApiKey)
                {
                    StatusText = "请先配置API Key";
                    Messages.Add(new ChatMessage
                    {
                        Role = "system",
                        Content = "欢迎使用AI助手！请先点击左下角的\"配置\"按钮设置API Key。",
                        IsError = false
                    });
                }
                else
                {
                    Messages.Add(new ChatMessage
                    {
                        Role = "assistant",
                        Content = "你好！我是AI助手，可以帮助你创建和优化HTML组件。请告诉我你想要什么效果？"
                    });
                }
            });
        }

        [RelayCommand]
        private async Task SendMessage()
        {
            if (string.IsNullOrWhiteSpace(UserInput))
                return;

            if (!HasApiKey)
            {
                MessageBox.Show("请先配置API Key", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var userMessage = UserInput.Trim();
            UserInput = string.Empty;

            // 添加用户消息
            Messages.Add(new ChatMessage
            {
                Role = "user",
                Content = userMessage
            });

            IsSending = true;
            StatusText = "AI思考中...";

            try
            {
                await Task.Run(() =>
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        var client = _pythonService.GetAIClient();
                        if (client != null)
                        {
                            // 构建消息列表
                            var messagesList = new System.Collections.Generic.List<System.Collections.Generic.Dictionary<string, string>>();

                            // 添加系统提示
                            messagesList.Add(new System.Collections.Generic.Dictionary<string, string>
                            {
                                { "role", "system" },
                                { "content", "你是一个专业的网页组件设计助手，可以帮助用户创建和优化HTML组件。请提供简洁实用的建议。" }
                            });

                            // 添加历史消息（最近10条）
                            int startIndex = Math.Max(0, Messages.Count - 10);
                            for (int i = startIndex; i < Messages.Count; i++)
                            {
                                var msg = Messages[i];
                                if (msg.Role != "system" && !msg.IsError)
                                {
                                    messagesList.Add(new System.Collections.Generic.Dictionary<string, string>
                                    {
                                        { "role", msg.Role },
                                        { "content", msg.Content }
                                    });
                                }
                            }

                            // 调用AI
                            string response = client.chat(messagesList, temperature: 0.7);

                            // 在UI线程添加回复
                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                Messages.Add(new ChatMessage
                                {
                                    Role = "assistant",
                                    Content = response
                                });
                            });
                        }
                    }
                });

                StatusText = "准备就绪";
            }
            catch (Exception ex)
            {
                Messages.Add(new ChatMessage
                {
                    Role = "system",
                    Content = $"错误: {ex.Message}",
                    IsError = true
                });
                StatusText = "发送失败";
            }
            finally
            {
                IsSending = false;
            }
        }

        [RelayCommand]
        private void ClearChat()
        {
            Messages.Clear();
            Messages.Add(new ChatMessage
            {
                Role = "assistant",
                Content = "对话已清空。有什么我可以帮你的吗？"
            });
            StatusText = "准备就绪";
        }

        [RelayCommand]
        private void OpenConfig()
        {
            var window = new Views.AIConfigWindow
            {
                Owner = Application.Current.MainWindow
            };
            window.ShowDialog();

            // 刷新API Key状态
            if (_aiClient != null)
            {
                using (Python.Runtime.Py.GIL())
                {
                    HasApiKey = !string.IsNullOrEmpty(_aiClient.api_key);
                }
            }
        }

        [RelayCommand]
        private void GenerateComponent()
        {
            if (!HasApiKey)
            {
                MessageBox.Show("请先配置API Key", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            // 添加提示消息
            Messages.Add(new ChatMessage
            {
                Role = "system",
                Content = "请描述你想要的组件效果，例如：\"创建一个带有渐变背景的标题组件\""
            });
        }
    }
}
