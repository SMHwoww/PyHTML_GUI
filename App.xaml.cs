using PyHTML.WPF.Services;
using System.Windows;

namespace PyHTML.WPF
{
    public partial class App : Application
    {
        protected override void OnExit(ExitEventArgs e)
        {
            PythonEngineService.Instance.Dispose();
            base.OnExit(e);
        }
    }
}
