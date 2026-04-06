using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace PyHTML.WPF.Converters
{
    public class RoleToAlignmentConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            var role = value?.ToString()?.ToLower() ?? "user";
            
            return role switch
            {
                "user" => HorizontalAlignment.Right,
                "assistant" => HorizontalAlignment.Left,
                "system" => HorizontalAlignment.Center,
                _ => HorizontalAlignment.Left
            };
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
