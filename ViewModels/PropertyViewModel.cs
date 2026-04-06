using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace PyHTML.WPF.ViewModels
{
    public partial class PropertyItemViewModel : ObservableObject
    {
        [ObservableProperty]
        private string _key = string.Empty;

        [ObservableProperty]
        private string _displayName = string.Empty;

        [ObservableProperty]
        private string _description = string.Empty;

        [ObservableProperty]
        private string _type = "string";

        [ObservableProperty]
        private object? _value;

        [ObservableProperty]
        private object? _defaultValue;

        [ObservableProperty]
        private ObservableCollection<string> _options = new();

        [ObservableProperty]
        private bool _isRequired;

        public bool IsString => Type == "string";
        public bool IsNumber => Type == "number";
        public bool IsBoolean => Type == "boolean";
        public bool IsTextArea => Type == "textarea";
        public bool IsColor => Type == "color";
        public bool IsSelect => Type == "select";
        public bool IsFont => Type == "font";
        public bool IsPicture => Type == "picture";
        public bool IsPictures => Type == "pictures";
        public bool IsMusic => Type == "music";

        public event EventHandler<PropertyChangedEventArgs>? PropertyValueChanged;

        partial void OnValueChanged(object? value)
        {
            PropertyValueChanged?.Invoke(this, new PropertyChangedEventArgs(Key, value));
        }
    }

    public class PropertyChangedEventArgs : EventArgs
    {
        public string Key { get; }
        public object? Value { get; }

        public PropertyChangedEventArgs(string key, object? value)
        {
            Key = key;
            Value = value;
        }
    }

    public partial class PropertyEditorViewModel : ObservableObject
    {
        [ObservableProperty]
        private ObservableCollection<PropertyItemViewModel> _properties = new();

        [ObservableProperty]
        private ComponentViewModel? _selectedComponent;

        [ObservableProperty]
        private bool _hasSelection;

        public event EventHandler? PropertiesChanged;

        partial void OnSelectedComponentChanged(ComponentViewModel? value)
        {
            HasSelection = value != null;
            LoadProperties(value);
        }

        private void LoadProperties(ComponentViewModel? component)
        {
            Properties.Clear();

            if (component?.PythonComponent == null) return;

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    var pyProps = component.PythonComponent.properties;
                    if (pyProps == null) return;

                    foreach (var key in pyProps.keys())
                    {
                        string keyStr = key.ToString();
                        var prop = pyProps[key];

                        var vm = new PropertyItemViewModel
                        {
                            Key = keyStr,
                            DisplayName = prop.name?.ToString() ?? keyStr,
                            Description = prop.description?.ToString() ?? string.Empty,
                            Type = prop.type?.ToString() ?? "string",
                            Value = prop.value,
                            DefaultValue = prop.default_value,
                            IsRequired = prop.required ?? false
                        };

                        var options = prop.options;
                        if (options != null)
                        {
                            foreach (var opt in options)
                            {
                                vm.Options.Add(opt.ToString());
                            }
                        }

                        vm.PropertyValueChanged += OnPropertyValueChanged;
                        Properties.Add(vm);
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading properties: {ex.Message}");
            }
        }

        private void OnPropertyValueChanged(object? sender, PropertyChangedEventArgs e)
        {
            if (SelectedComponent != null)
            {
                SelectedComponent.UpdateProperty(e.Key, e.Value ?? string.Empty);
                PropertiesChanged?.Invoke(this, EventArgs.Empty);
            }
        }

        public void RefreshProperties()
        {
            LoadProperties(SelectedComponent);
        }
    }

    public static class FontList
    {
        public static readonly List<string> Fonts = new()
        {
            "Microsoft YaHei",
            "SimHei",
            "SimSun",
            "NSimSun",
            "FangSong",
            "KaiTi",
            "LiSu",
            "YouYuan",
            "Arial",
            "Arial Black",
            "Comic Sans MS",
            "Courier New",
            "Georgia",
            "Impact",
            "Lucida Console",
            "Tahoma",
            "Times New Roman",
            "Trebuchet MS",
            "Verdana",
            "Helvetica",
            "PingFang SC",
            "Hiragino Sans GB",
            "WenQuanYi Micro Hei"
        };
    }
}
