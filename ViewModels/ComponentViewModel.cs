using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace PyHTML.WPF.ViewModels
{
    /// <summary>
    /// 组件属性项，用于属性编辑器绑定
    /// </summary>
    public partial class ComponentPropertyItem : ObservableObject
    {
        [ObservableProperty]
        private string _key = string.Empty;

        [ObservableProperty]
        private object? _value;

        [ObservableProperty]
        private string _type = "string";

        [ObservableProperty]
        private string _displayName = string.Empty;

        [ObservableProperty]
        private string _description = string.Empty;

        private ComponentViewModel? _parent;

        partial void OnValueChanged(object? value)
        {
            _parent?.UpdateProperty(Key, value ?? string.Empty);
        }

        public ComponentPropertyItem(string key, object? value, string type, string displayName, string description, ComponentViewModel? parent)
        {
            _key = key;
            _value = value;
            _type = type;
            _displayName = displayName;
            _description = description;
            _parent = parent;
        }
    }

    public partial class ComponentViewModel : ObservableObject
    {
        [ObservableProperty]
        private string _name = string.Empty;

        [ObservableProperty]
        private string _displayName = string.Empty;

        [ObservableProperty]
        private string _description = string.Empty;

        [ObservableProperty]
        private string _icon = string.Empty;

        [ObservableProperty]
        private string _category = string.Empty;

        [ObservableProperty]
        private bool _isSelected;

        [ObservableProperty]
        private int _order;

        [ObservableProperty]
        private ObservableCollection<ComponentPropertyItem> _propertyItems = new();

        private dynamic? _pythonComponent;
        private Dictionary<string, object> _properties = new();

        public dynamic? PythonComponent
        {
            get => _pythonComponent;
            set
            {
                _pythonComponent = value;
                LoadFromPython();
            }
        }

        public Dictionary<string, object> Properties
        {
            get => _properties;
            set => SetProperty(ref _properties, value);
        }

        private void LoadFromPython()
        {
            if (_pythonComponent == null) return;

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    Name = _pythonComponent.name ?? string.Empty;
                    DisplayName = _pythonComponent.config?.get("name", Name) ?? Name;
                    Description = _pythonComponent.config?.get("description", string.Empty) ?? string.Empty;
                    Category = _pythonComponent.config?.get("category", "其他") ?? "其他";
                    
                    var fields = _pythonComponent.fields;
                    var values = _pythonComponent.values;
                    
                    if (fields != null)
                    {
                        Properties = new Dictionary<string, object>();
                        PropertyItems.Clear();
                        
                        foreach (var field in fields)
                        {
                            string keyStr = field.get("name", "").ToString();
                            string type = field.get("type", "string").ToString();
                            string displayName = field.get("display_name", keyStr).ToString();
                            string description = field.get("description", string.Empty).ToString();
                            object? value = values.get(keyStr) ?? GetDefaultValue(type);
                            
                            Properties[keyStr] = value ?? string.Empty;
                            PropertyItems.Add(new ComponentPropertyItem(keyStr, value, type, displayName, description, this));
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading component: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Error loading component: {ex.StackTrace}");
            }
        }

        private object GetDefaultValue(string type)
        {
            return type.ToLower() switch
            {
                "string" => string.Empty,
                "number" => 0,
                "boolean" => false,
                "textarea" => string.Empty,
                "color" => "#000000",
                "select" => string.Empty,
                "font" => "Microsoft YaHei",
                "picture" => string.Empty,
                "pictures" => new List<string>(),
                "music" => string.Empty,
                _ => string.Empty
            };
        }

        public void UpdateProperty(string key, object value)
        {
            if (Properties.ContainsKey(key))
            {
                Properties[key] = value;
                OnPropertyChanged(nameof(Properties));
            }

            if (_pythonComponent != null)
            {
                try
                {
                    using (Python.Runtime.Py.GIL())
                    {
                        _pythonComponent.set_value(key, value);
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Error updating property: {ex.Message}");
                }
            }
        }
    }

    public partial class ComponentLibraryViewModel : ObservableObject
    {
        [ObservableProperty]
        private ObservableCollection<ComponentViewModel> _components = new();

        [ObservableProperty]
        private ObservableCollection<string> _categories = new();

        [ObservableProperty]
        private string? _selectedCategory;

        public IEnumerable<ComponentViewModel> FilteredComponents =>
            string.IsNullOrEmpty(SelectedCategory)
                ? Components
                : Components.Where(c => c.Category == SelectedCategory);

        partial void OnSelectedCategoryChanged(string? value)
        {
            OnPropertyChanged(nameof(FilteredComponents));
        }

        public void LoadComponents(dynamic componentLoader)
        {
            Components.Clear();
            Categories.Clear();

            try
            {
                using (Python.Runtime.Py.GIL())
                {
                    var components = componentLoader.get_all_components();
                    var categories = new HashSet<string>();

                    foreach (var comp in components)
                    {
                        var vm = new ComponentViewModel
                        {
                            PythonComponent = comp
                        };
                        Components.Add(vm);
                        categories.Add(vm.Category);
                    }

                    foreach (var cat in categories.OrderBy(c => c))
                    {
                        Categories.Add(cat);
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading components: {ex.Message}");
            }
        }
    }
}
