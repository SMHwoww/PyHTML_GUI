using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Windows;

namespace PyHTML.WPF.ViewModels
{
    public partial class ThemeSettingsViewModel : ViewModelBase
    {
        [ObservableProperty]
        private string _selectedTheme = "Light";

        [ObservableProperty]
        private string _primaryColor = "#0078D4";

        [ObservableProperty]
        private bool _useSystemTheme = true;

        [ObservableProperty]
        private bool _enableAnimations = true;

        [ObservableProperty]
        private bool _enableTransparency = true;

        public string[] AvailableThemes { get; } = new[] { "Light", "Dark", "System" };
        public string[] AvailableColors { get; } = new[] { "#0078D4", "#107C10", "#D83B01", "#A80000", "#5C2D91", "#0063B1" };

        [RelayCommand]
        private void ApplyTheme()
        {
            MessageBox.Show("主题设置已应用！", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        [RelayCommand]
        private void ResetToDefault()
        {
            SelectedTheme = "Light";
            PrimaryColor = "#0078D4";
            UseSystemTheme = true;
            EnableAnimations = true;
            EnableTransparency = true;
        }
    }
}
