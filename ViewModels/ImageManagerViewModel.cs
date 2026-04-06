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
    public partial class ImageItemViewModel : ObservableObject
    {
        [ObservableProperty]
        private string _id = string.Empty;

        [ObservableProperty]
        private string _url = string.Empty;

        [ObservableProperty]
        private string _thumbnailUrl = string.Empty;

        [ObservableProperty]
        private string _deleteUrl = string.Empty;

        [ObservableProperty]
        private string _fileName = string.Empty;

        [ObservableProperty]
        private long _fileSize;

        [ObservableProperty]
        private DateTime _uploadTime;

        [ObservableProperty]
        private string _filePath = string.Empty;

        public string FileSizeDisplay => FileSize > 0 ? $"{FileSize / 1024.0:F1} KB" : "未知大小";
        public string UploadTimeDisplay => UploadTime.ToString("yyyy-MM-dd HH:mm");
    }

    public partial class ImageManagerViewModel : ViewModelBase
    {
        private readonly PythonEngineService _pythonService;
        private dynamic? _imageManager;

        [ObservableProperty]
        private ObservableCollection<ImageItemViewModel> _images = new();

        [ObservableProperty]
        private ImageItemViewModel? _selectedImage;

        [ObservableProperty]
        private bool _isUploading;

        [ObservableProperty]
        private string _uploadProgress = string.Empty;

        [ObservableProperty]
        private int _totalImages;

        public ImageManagerViewModel()
        {
            _pythonService = PythonEngineService.Instance;
            LoadImages();
        }

        private void LoadImages()
        {
            try
            {
                _imageManager = _pythonService.GetImageManager();
                if (_imageManager != null)
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        var images = _imageManager.get_all_images();
                        Images.Clear();

                        foreach (var img in images)
                        {
                            var vm = new ImageItemViewModel
                            {
                                Id = img.get("id", ""),
                                Url = img.get("links", new System.Dynamic.ExpandoObject())?.url ?? "",
                                ThumbnailUrl = img.get("links", new System.Dynamic.ExpandoObject())?.thumbnail_url ?? "",
                                DeleteUrl = img.get("links", new System.Dynamic.ExpandoObject())?.delete_url ?? "",
                                FileName = img.get("filename", "未知文件"),
                                FileSize = img.get("size", 0L),
                                UploadTime = DateTime.FromFileTime(img.get("upload_time", 0L) * 10000 + 504911232000000000),
                                FilePath = img.get("file_path", "")
                            };
                            Images.Add(vm);
                        }

                        TotalImages = Images.Count;
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading images: {ex.Message}");
            }
        }

        [RelayCommand]
        private async Task UploadImage()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "图片文件|*.jpg;*.jpeg;*.png;*.gif;*.webp|所有文件|*.*",
                Title = "选择要上传的图片",
                Multiselect = false
            };

            if (dialog.ShowDialog() != true)
                return;

            await UploadImageInternal(dialog.FileName);
        }

        [RelayCommand]
        private async Task UploadImages()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "图片文件|*.jpg;*.jpeg;*.png;*.gif;*.webp|所有文件|*.*",
                Title = "选择要上传的图片",
                Multiselect = true
            };

            if (dialog.ShowDialog() != true)
                return;

            foreach (var fileName in dialog.FileNames)
            {
                await UploadImageInternal(fileName);
            }
        }

        private async Task UploadImageInternal(string filePath)
        {
            IsUploading = true;
            UploadProgress = $"正在上传: {Path.GetFileName(filePath)}...";

            try
            {
                await Task.Run(() =>
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        var imageManager = _pythonService.GetImageManager();
                        if (imageManager != null)
                        {
                            var result = imageManager.upload_image(filePath);
                            
                            if (result != null)
                            {
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    var vm = new ImageItemViewModel
                                    {
                                        Id = result.get("id", ""),
                                        Url = result.get("links", new System.Dynamic.ExpandoObject())?.url ?? "",
                                        ThumbnailUrl = result.get("links", new System.Dynamic.ExpandoObject())?.thumbnail_url ?? "",
                                        DeleteUrl = result.get("links", new System.Dynamic.ExpandoObject())?.delete_url ?? "",
                                        FileName = result.get("filename", Path.GetFileName(filePath)),
                                        FileSize = result.get("size", new FileInfo(filePath).Length),
                                        UploadTime = DateTime.Now,
                                        FilePath = result.get("file_path", "")
                                    };
                                    Images.Insert(0, vm);
                                    TotalImages = Images.Count;
                                });
                            }
                            else
                            {
                                Application.Current.Dispatcher.Invoke(() =>
                                {
                                    MessageBox.Show($"上传失败: {Path.GetFileName(filePath)}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                                });
                            }
                        }
                    }
                });

                UploadProgress = $"上传完成: {Path.GetFileName(filePath)}";
            }
            catch (Exception ex)
            {
                UploadProgress = $"上传失败: {ex.Message}";
                MessageBox.Show($"上传失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                IsUploading = false;
            }
        }

        [RelayCommand]
        private void DeleteImage()
        {
            if (SelectedImage == null)
            {
                MessageBox.Show("请先选择要删除的图片", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            var result = MessageBox.Show(
                $"确定要删除图片 \"{SelectedImage.FileName}\" 吗？\n此操作将同时删除云端图片，无法恢复。",
                "确认删除",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result != MessageBoxResult.Yes)
                return;

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    var imageManager = _pythonService.GetImageManager();
                    if (imageManager != null)
                    {
                        dynamic imageData = new System.Dynamic.ExpandoObject();
                        imageData.links = new System.Dynamic.ExpandoObject();
                        imageData.links.delete_url = SelectedImage.DeleteUrl;

                        bool success = imageManager.delete_image(SelectedImage.FilePath, imageData);
                        
                        if (success)
                        {
                            Images.Remove(SelectedImage);
                            SelectedImage = null;
                            TotalImages = Images.Count;
                            StatusMessage = "图片已删除";
                        }
                        else
                        {
                            MessageBox.Show("删除失败", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"删除失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private void CopyUrl()
        {
            if (SelectedImage == null)
            {
                MessageBox.Show("请先选择图片", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            Clipboard.SetText(SelectedImage.Url);
            StatusMessage = "URL已复制到剪贴板";
        }

        [RelayCommand]
        private void CopyMarkdown()
        {
            if (SelectedImage == null)
            {
                MessageBox.Show("请先选择图片", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            string markdown = $"![{SelectedImage.FileName}]({SelectedImage.Url})";
            Clipboard.SetText(markdown);
            StatusMessage = "Markdown已复制到剪贴板";
        }

        [RelayCommand]
        private void OpenInBrowser()
        {
            if (SelectedImage == null)
            {
                MessageBox.Show("请先选择图片", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = SelectedImage.Url,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"无法打开浏览器: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        [RelayCommand]
        private void Refresh()
        {
            LoadImages();
            StatusMessage = "图片列表已刷新";
        }
    }
}
