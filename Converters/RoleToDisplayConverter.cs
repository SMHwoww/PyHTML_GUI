using System;
using System.Globalization;
using System.Windows.Data;

namespace PyHTML.WPF.Converters
{
    public class RoleToDisplayConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            var role = value?.ToString()?.ToLower() ?? "user";
            
            return role switch
            {
                "user" => "我",
                "assistant" => "AI助手",
                "system" => "系统",
                _ => role
            };
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
