using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace PyHTML.WPF.Converters
{
    public class RoleToBrushConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            var role = value?.ToString()?.ToLower() ?? "user";
            
            return role switch
            {
                "user" => new SolidColorBrush(Color.FromRgb(0, 120, 212)), // Primary blue
                "assistant" => new SolidColorBrush(Color.FromRgb(240, 240, 240)), // Light gray
                "system" => new SolidColorBrush(Color.FromRgb(255, 243, 205)), // Light yellow
                _ => new SolidColorBrush(Colors.LightGray)
            };
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
