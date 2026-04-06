using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace PyHTML.WPF.Converters
{
    public class BooleanToBrushConverter : IValueConverter
    {
        public Brush? TrueBrush { get; set; }
        public Brush? FalseBrush { get; set; }

        public object Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
        {
            bool boolValue = value is true;
            
            // 支持参数指定是错误状态还是文本颜色
            if (parameter?.ToString() == "Error")
            {
                return boolValue 
                    ? new SolidColorBrush(System.Windows.Media.Color.FromRgb(253, 237, 237))  // 错误背景色
                    : new SolidColorBrush(System.Windows.Media.Color.FromRgb(237, 247, 237)); // 成功背景色
            }
            else if (parameter?.ToString() == "Text")
            {
                return boolValue
                    ? new SolidColorBrush(System.Windows.Media.Color.FromRgb(211, 47, 47))   // 错误文字色
                    : new SolidColorBrush(System.Windows.Media.Color.FromRgb(46, 125, 50));  // 成功文字色
            }
            
            return boolValue ? TrueBrush : FalseBrush;
        }

        public object ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
