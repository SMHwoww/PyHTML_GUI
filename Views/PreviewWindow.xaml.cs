using Microsoft.Win32;
using Microsoft.Web.WebView2.Core;
using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Windows;

namespace PyHTML.WPF.Views
{
    public partial class PreviewWindow : Window
    {
        private string _htmlContent = string.Empty;
        private string _tempFilePath = string.Empty;

        public PreviewWindow()
        {
            InitializeComponent();
            InitializeWebView();
        }

        private async void InitializeWebView()
        {
            try
            {
                await WebView.EnsureCoreWebView2Async();
                WebView.CoreWebView2.NavigationCompleted += CoreWebView2_NavigationCompleted;
                WebView.CoreWebView2.SourceChanged += CoreWebView2_SourceChanged;
                StatusText.Text = "预览引擎已就绪";
            }
            catch (Exception ex)
            {
                MessageBox.Show($"初始化预览引擎失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void CoreWebView2_NavigationCompleted(object? sender, CoreWebView2NavigationCompletedEventArgs e)
        {
            StatusText.Text = e.IsSuccess ? "加载完成" : "加载失败";
        }

        private void CoreWebView2_SourceChanged(object? sender, CoreWebView2SourceChangedEventArgs e)
        {
            UrlText.Text = WebView.Source?.ToString() ?? string.Empty;
        }

        public void SetHtmlContent(string htmlContent)
        {
            _htmlContent = htmlContent;
            RefreshPreview();
        }

        private void RefreshPreview()
        {
            if (WebView.CoreWebView2 != null && !string.IsNullOrEmpty(_htmlContent))
            {
                WebView.CoreWebView2.NavigateToString(_htmlContent);
                StatusText.Text = "正在加载...";
            }
        }

        private void RefreshButton_Click(object sender, RoutedEventArgs e)
        {
            RefreshPreview();
        }

        private void ZoomComboBox_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
        {
            if (WebView.CoreWebView2 != null && ZoomComboBox.SelectedItem is System.Windows.Controls.ComboBoxItem item)
            {
                var zoomText = item.Content.ToString()?.Replace("%", "");
                if (double.TryParse(zoomText, out double zoomPercent))
                {
                    WebView.ZoomFactor = zoomPercent / 100.0;
                }
            }
        }

        private void OpenInBrowser_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (string.IsNullOrEmpty(_tempFilePath) || !File.Exists(_tempFilePath))
                {
                    _tempFilePath = Path.Combine(Path.GetTempPath(), $"pyhtml_preview_{Guid.NewGuid()}.html");
                    File.WriteAllText(_tempFilePath, _htmlContent);
                }

                Process.Start(new ProcessStartInfo
                {
                    FileName = _tempFilePath,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开浏览器失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ExportHtml_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new SaveFileDialog
            {
                Filter = "HTML文件 (*.html)|*.html|所有文件 (*.*)|*.*",
                Title = "导出HTML",
                FileName = "index.html"
            };

            if (dialog.ShowDialog() == true)
            {
                try
                {
                    File.WriteAllText(dialog.FileName, _htmlContent);
                    MessageBox.Show("HTML导出成功！", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"导出失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
        }

        private void MinimizeButton_Click(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }

        private void MaximizeButton_Click(object sender, RoutedEventArgs e)
        {
            if (WindowState == WindowState.Maximized)
            {
                WindowState = WindowState.Normal;
            }
            else
            {
                WindowState = WindowState.Maximized;
            }
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        protected override void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            base.OnClosing(e);

            // Clean up temp file
            if (!string.IsNullOrEmpty(_tempFilePath) && File.Exists(_tempFilePath))
            {
                try
                {
                    File.Delete(_tempFilePath);
                }
                catch
                {
                    // Ignore cleanup errors
                }
            }
        }
    }
}
