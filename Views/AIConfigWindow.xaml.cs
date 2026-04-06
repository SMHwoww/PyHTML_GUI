using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace PyHTML.WPF.Views
{
    public partial class AIConfigWindow : Window
    {
        private bool _isPasswordVisible = false;

        public AIConfigWindow()
        {
            InitializeComponent();
        }

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2)
            {
                // 双击标题栏不执行任何操作（禁用最大化）
                return;
            }
            DragMove();
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void ApiKeyPasswordBox_PasswordChanged(object sender, RoutedEventArgs e)
        {
            if (DataContext is ViewModels.AIConfigViewModel viewModel)
            {
                viewModel.ApiKey = ApiKeyPasswordBox.Password;
            }
        }

        private void TogglePasswordVisibility_Click(object sender, RoutedEventArgs e)
        {
            _isPasswordVisible = !_isPasswordVisible;
            
            if (_isPasswordVisible)
            {
                // 显示密码 - 切换到普通文本框
                var textBox = new TextBox
                {
                    Text = ApiKeyPasswordBox.Password,
                    Style = (Style)FindResource("Win11TextBoxStyle")
                };
                textBox.TextChanged += (s, ev) =>
                {
                    if (DataContext is ViewModels.AIConfigViewModel viewModel)
                    {
                        viewModel.ApiKey = textBox.Text;
                    }
                };
                
                // 替换控件
                var parent = (Grid)ApiKeyPasswordBox.Parent;
                var index = parent.Children.IndexOf(ApiKeyPasswordBox);
                parent.Children.RemoveAt(index);
                parent.Children.Insert(index, textBox);
                Grid.SetColumn(textBox, 0);
                textBox.Name = "ApiKeyTextBox";
            }
            else
            {
                // 隐藏密码 - 切换回密码框
                var textBox = (TextBox)((Grid)ApiKeyPasswordBox.Parent).Children[0];
                
                ApiKeyPasswordBox.Password = textBox.Text;
                if (DataContext is ViewModels.AIConfigViewModel viewModel)
                {
                    viewModel.ApiKey = textBox.Text;
                }
                
                // 替换控件
                var parent = (Grid)textBox.Parent;
                var index = parent.Children.IndexOf(textBox);
                parent.Children.RemoveAt(index);
                parent.Children.Insert(index, ApiKeyPasswordBox);
                Grid.SetColumn(ApiKeyPasswordBox, 0);
            }
        }
    }
}
