using PyHTML.WPF.ViewModels;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace PyHTML.WPF
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
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
                MaximizeButton.Content = "\xE923"; // Restore icon
            }
            else
            {
                WindowState = WindowState.Maximized;
                MaximizeButton.Content = "\xE922"; // Maximize icon
            }
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            if (DataContext is MainViewModel vm)
            {
                vm.ExitCommand.Execute(null);
            }
            else
            {
                Close();
            }
        }

        private void ComponentLibrary_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (sender is ListBox listBox && listBox.SelectedItem is ComponentViewModel component)
            {
                if (DataContext is MainViewModel vm)
                {
                    vm.AddComponentCommand.Execute(component);
                }
            }
        }

        protected override void OnMouseLeftButtonDown(MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);

            // Allow dragging the window from the title bar area
            if (e.GetPosition(this).Y <= 32)
            {
                DragMove();
            }
        }
    }
}
