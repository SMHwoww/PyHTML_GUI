using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System;
using System.Collections.ObjectModel;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class MetaTagItem : ObservableObject
    {
        [ObservableProperty]
        private string _name = string.Empty;

        [ObservableProperty]
        private string _content = string.Empty;
    }

    public partial class LinkTagItem : ObservableObject
    {
        [ObservableProperty]
        private string _rel = string.Empty;

        [ObservableProperty]
        private string _href = string.Empty;

        [ObservableProperty]
        private string _type = string.Empty;
    }

    public partial class ScriptTagItem : ObservableObject
    {
        [ObservableProperty]
        private string _src = string.Empty;

        [ObservableProperty]
        private string _content = string.Empty;
    }

    public partial class HeadSettingsViewModel : ViewModelBase
    {
        [ObservableProperty]
        private string _pageTitle = string.Empty;

        [ObservableProperty]
        private string _language = "zh-CN";

        [ObservableProperty]
        private ObservableCollection<MetaTagItem> _metaTags = new();

        [ObservableProperty]
        private ObservableCollection<LinkTagItem> _linkTags = new();

        [ObservableProperty]
        private ObservableCollection<ScriptTagItem> _scriptTags = new();

        [ObservableProperty]
        private MetaTagItem? _selectedMetaTag;

        [ObservableProperty]
        private LinkTagItem? _selectedLinkTag;

        [ObservableProperty]
        private ScriptTagItem? _selectedScriptTag;

        public HeadSettingsViewModel()
        {
        }

        public void LoadFromProject(dynamic? pythonProject)
        {
            if (pythonProject == null) return;

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    PageTitle = pythonProject.title ?? string.Empty;
                    Language = pythonProject.head_config?.get("lang", "zh-CN") ?? "zh-CN";

                    MetaTags.Clear();
                    var metaTags = pythonProject.head_config?.get("meta_tags", new System.Collections.Generic.List<object>());
                    if (metaTags != null)
                    {
                        foreach (var tag in metaTags)
                        {
                            MetaTags.Add(new MetaTagItem
                            {
                                Name = tag.get("name", ""),
                                Content = tag.get("content", "")
                            });
                        }
                    }

                    LinkTags.Clear();
                    var linkTags = pythonProject.head_config?.get("links", new System.Collections.Generic.List<object>());
                    if (linkTags != null)
                    {
                        foreach (var tag in linkTags)
                        {
                            LinkTags.Add(new LinkTagItem
                            {
                                Rel = tag.get("rel", ""),
                                Href = tag.get("href", ""),
                                Type = tag.get("type", "")
                            });
                        }
                    }

                    ScriptTags.Clear();
                    var scriptTags = pythonProject.head_config?.get("scripts", new System.Collections.Generic.List<object>());
                    if (scriptTags != null)
                    {
                        foreach (var tag in scriptTags)
                        {
                            ScriptTags.Add(new ScriptTagItem
                            {
                                Src = tag.get("src", ""),
                                Content = tag.get("content", "")
                            });
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading head settings: {ex.Message}");
            }
        }

        public void SaveToProject(dynamic? pythonProject)
        {
            System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Starting...");
            
            if (pythonProject == null) 
            {
                System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: pythonProject is null, aborting.");
                return;
            }

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Got GIL.");
                    pythonProject.title = PageTitle;
                    System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Set title.");
                    
                    var headConfig = pythonProject.head_config;
                    System.Diagnostics.Debug.WriteLine($"HeadSettingsViewModel.SaveToProject: headConfig type: {headConfig.GetType()}");
                    headConfig["lang"] = Language;

                    dynamic builtins = Python.Runtime.Py.Import("builtins");
                    System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Imported builtins.");

                    // 创建Python列表用于meta标签
                    System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Creating meta tags...");
                    dynamic metaList = builtins.list();
                    foreach (var tag in MetaTags)
                    {
                        dynamic dict = builtins.dict();
                        dict["name"] = tag.Name;
                        dict["content"] = tag.Content;
                        metaList.append(dict);
                    }
                    headConfig["meta_tags"] = metaList;

                    // 创建Python列表用于link标签
                    System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Creating link tags...");
                    dynamic linkList = builtins.list();
                    foreach (var tag in LinkTags)
                    {
                        dynamic dict = builtins.dict();
                        dict["rel"] = tag.Rel;
                        dict["href"] = tag.Href;
                        if (!string.IsNullOrEmpty(tag.Type))
                        {
                            dict["type"] = tag.Type;
                        }
                        linkList.append(dict);
                    }
                    headConfig["links"] = linkList;

                    // 创建Python列表用于script标签
                    System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Creating script tags...");
                    dynamic scriptList = builtins.list();
                    foreach (var tag in ScriptTags)
                    {
                        dynamic dict = builtins.dict();
                        if (!string.IsNullOrEmpty(tag.Src))
                        {
                            dict["src"] = tag.Src;
                        }
                        if (!string.IsNullOrEmpty(tag.Content))
                        {
                            dict["content"] = tag.Content;
                        }
                        scriptList.append(dict);
                    }
                    headConfig["scripts"] = scriptList;
                    
                    System.Diagnostics.Debug.WriteLine("HeadSettingsViewModel.SaveToProject: Success!");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"HeadSettingsViewModel.SaveToProject: Exception - {ex.GetType().Name}: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"HeadSettingsViewModel.SaveToProject: Stack trace: {ex.StackTrace}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"HeadSettingsViewModel.SaveToProject: Inner exception - {ex.InnerException.GetType().Name}: {ex.InnerException.Message}");
                    System.Diagnostics.Debug.WriteLine($"HeadSettingsViewModel.SaveToProject: Inner stack trace: {ex.InnerException.StackTrace}");
                }
            }
        }

        [RelayCommand]
        private void AddMetaTag()
        {
            MetaTags.Add(new MetaTagItem { Name = "description", Content = "" });
        }

        [RelayCommand]
        private void RemoveMetaTag()
        {
            if (SelectedMetaTag != null)
            {
                MetaTags.Remove(SelectedMetaTag);
            }
        }

        [RelayCommand]
        private void AddLinkTag()
        {
            LinkTags.Add(new LinkTagItem { Rel = "stylesheet", Href = "" });
        }

        [RelayCommand]
        private void RemoveLinkTag()
        {
            if (SelectedLinkTag != null)
            {
                LinkTags.Remove(SelectedLinkTag);
            }
        }

        [RelayCommand]
        private void AddScriptTag()
        {
            ScriptTags.Add(new ScriptTagItem { Src = "" });
        }

        [RelayCommand]
        private void RemoveScriptTag()
        {
            if (SelectedScriptTag != null)
            {
                ScriptTags.Remove(SelectedScriptTag);
            }
        }

        [RelayCommand]
        private void AddFavicon()
        {
            LinkTags.Add(new LinkTagItem { Rel = "icon", Href = "favicon.ico", Type = "image/x-icon" });
        }

        [RelayCommand]
        private void AddDescription()
        {
            MetaTags.Add(new MetaTagItem { Name = "description", Content = "页面描述" });
        }

        [RelayCommand]
        private void AddKeywords()
        {
            MetaTags.Add(new MetaTagItem { Name = "keywords", Content = "关键词1, 关键词2" });
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
