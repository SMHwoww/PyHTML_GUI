using System.Windows;
using System.Windows.Input;

namespace PyHTML.WPF.Views
{
    public partial class BackgroundSettingsWindow : Window
    {
        public BackgroundSettingsWindow()
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
    }
}
