using System.Windows;
using System.Windows.Input;

namespace PyHTML.WPF.Views
{
    public partial class DeployWindow : Window
    {
        public DeployWindow()
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

        private void ApiTokenPasswordBox_PasswordChanged(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.DeployViewModel vm)
            {
                vm.ApiToken = ApiTokenPasswordBox.Password;
            }
        }
    }
}
