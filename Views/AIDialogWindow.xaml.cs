using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace PyHTML.WPF.Views
{
    public partial class AIDialogWindow : Window
    {
        public AIDialogWindow()
        {
            InitializeComponent();
            Loaded += AIDialogWindow_Loaded;
        }

        private void AIDialogWindow_Loaded(object sender, RoutedEventArgs e)
        {
            // 监听消息变化，自动滚动到底部
            if (DataContext is ViewModels.AIDialogViewModel vm)
            {
                vm.Messages.CollectionChanged += (s, args) =>
                {
                    Dispatcher.BeginInvoke(() =>
                    {
                        MessagesScrollViewer?.ScrollToEnd();
                    });
                };
            }
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
