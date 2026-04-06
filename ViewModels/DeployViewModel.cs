using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Win32;
using PyHTML.WPF.Services;
using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Threading.Tasks;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class LogEntry : ObservableObject
    {
        [ObservableProperty]
        private string _message = string.Empty;

        [ObservableProperty]
        private DateTime _timestamp = DateTime.Now;

        [ObservableProperty]
        private bool _isError;
    }

    public partial class DeployViewModel : ViewModelBase
    {
        private readonly PythonEngineService _pythonService;
        private dynamic? _cloudflareWorker;

        [ObservableProperty]
        private string _projectDirectory = string.Empty;

        [ObservableProperty]
        private string _workerName = string.Empty;

        [ObservableProperty]
        private string _customDomain = string.Empty;

        [ObservableProperty]
        private string _apiToken = string.Empty;

        [ObservableProperty]
        private bool _autoDeploy = true;

        [ObservableProperty]
        private bool _isDeploying;

        [ObservableProperty]
        private ObservableCollection<LogEntry> _logs = new();

        [ObservableProperty]
        private string _deployStatus = string.Empty;

        [ObservableProperty]
        private bool _deploySuccess;

        [ObservableProperty]
        private string? _deployedUrl;

        public DeployViewModel()
        {
            _pythonService = PythonEngineService.Instance;
            
            // 尝试从环境变量加载 API Token
            var envToken = Environment.GetEnvironmentVariable("CLOUDFLARE_API_TOKEN");
            if (!string.IsNullOrEmpty(envToken))
            {
                ApiToken = envToken;
            }
        }

        [RelayCommand]
        private void BrowseDirectory()
        {
            var dialog = new OpenFolderDialog
            {
                Title = "选择部署目录"
            };

            if (dialog.ShowDialog() == true)
            {
                ProjectDirectory = dialog.FolderName;
            }
        }

        [RelayCommand]
        private async Task Deploy()
        {
            if (string.IsNullOrWhiteSpace(ProjectDirectory))
            {
                MessageBox.Show("请选择部署目录", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (AutoDeploy && string.IsNullOrWhiteSpace(ApiToken))
            {
                MessageBox.Show("请输入 Cloudflare API Token", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            // 获取主窗口的项目
            var mainWindow = Application.Current.MainWindow;
            if (mainWindow?.DataContext is not MainViewModel mainVm)
            {
                MessageBox.Show("无法获取项目信息", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            IsDeploying = true;
            Logs.Clear();
            DeployStatus = "准备部署...";
            DeploySuccess = false;
            DeployedUrl = null;

            try
            {
                await Task.Run(() =>
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        var cloudflare = _pythonService.GetCloudflareWorker();
                        if (cloudflare == null)
                        {
                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                AddLog("Cloudflare Worker 模块未加载", true);
                            });
                            return;
                        }

                        // 设置环境变量
                        if (!string.IsNullOrEmpty(ApiToken))
                        {
                            Environment.SetEnvironmentVariable("CLOUDFLARE_API_TOKEN", ApiToken);
                        }

                        // 创建项目
                        Application.Current.Dispatcher.Invoke(() =>
                        {
                            AddLog("创建 Cloudflare Worker 项目...");
                        });

                        string workerName = string.IsNullOrWhiteSpace(WorkerName) ? 
                            (mainVm.ProjectName ?? "pyhtml-worker") : WorkerName;

                        // 清理 worker 名称
                        workerName = workerName.ToLower().Replace(" ", "-");
                        foreach (char c in System.IO.Path.GetInvalidFileNameChars())
                        {
                            workerName = workerName.Replace(c.ToString(), "");
                        }

                        string projectPath = cloudflare.create_worker_project(
                            ProjectDirectory,
                            mainVm.PythonProject.components,
                            mainVm.ProjectName,
                            mainVm.PythonProject.head_config,
                            workerName,
                            CustomDomain
                        );

                        Application.Current.Dispatcher.Invoke(() =>
                        {
                            AddLog($"项目已创建: {projectPath}");
                        });

                        if (AutoDeploy)
                        {
                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                AddLog("开始部署到 Cloudflare...");
                            });

                            // 创建日志回调
                            Action<string> logCallback = (msg) =>
                            {
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    AddLog(msg);
                                });
                            };

                            dynamic result = cloudflare.deploy_worker(projectPath, ApiToken, CustomDomain, logCallback);

                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                DeploySuccess = result[0];
                                DeployedUrl = result[1];
                                
                                if (DeploySuccess)
                                {
                                    DeployStatus = "部署成功!";
                                    AddLog($"部署成功! URL: {DeployedUrl}");
                                }
                                else
                                {
                                    DeployStatus = "部署失败";
                                    AddLog("部署失败，请查看日志", true);
                                }
                            });
                        }
                        else
                        {
                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                DeploySuccess = true;
                                DeployStatus = "项目已创建";
                                AddLog("项目已创建，请手动部署");
                            });
                        }
                    }
                });
            }
            catch (Exception ex)
            {
                DeployStatus = "部署出错";
                AddLog($"错误: {ex.Message}", true);
            }
            finally
            {
                IsDeploying = false;
            }
        }

        [RelayCommand]
        private void OpenDeployedUrl()
        {
            if (string.IsNullOrEmpty(DeployedUrl))
                return;

            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = DeployedUrl,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"无法打开浏览器: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private void ClearLogs()
        {
            Logs.Clear();
        }

        private void AddLog(string message, bool isError = false)
        {
            Logs.Add(new LogEntry
            {
                Message = message,
                IsError = isError,
                Timestamp = DateTime.Now
            });
        }
    }
}
