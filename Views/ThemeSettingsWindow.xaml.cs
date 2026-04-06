using System.Windows;
using System.Windows.Input;

namespace PyHTML.WPF.Views
{
    public partial class ThemeSettingsWindow : Window
    {
        public ThemeSettingsWindow()
        {
            InitializeComponent();
        }

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2)
            {
                return;
            }
            DragMove();
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void ColorBorder_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (sender is FrameworkElement element && element.Tag is string color)
            {
                if (DataContext is ViewModels.ThemeSettingsViewModel vm)
                {
                    vm.PrimaryColor = color;
                }
            }
        }
    }
}
