import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class Theme:
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get('name', 'Untitled')
        self.description = data.get('description', '')
        self.author = data.get('author', '')
        self.version = data.get('version', '1.0')
        self.colors = data.get('colors', {
            'primary': '#4CAF50',
            'secondary': '#333333',
            'background': '#f0f0f0',
            'text': '#333333',
            'text_light': '#ffffff',
            'border': '#dddddd',
            'hover': '#45a049',
            'pressed': '#3d8b40',
            'error': '#f44336',
            'success': '#4CAF50',
            'warning': '#ff9800',
            'info': '#2196f3'
        })
        self.fonts = data.get('fonts', {
            'family': 'Microsoft YaHei',
            'size': 12
        })
        self.styles = data.get('styles', {})
        self.background_image = data.get('background_image', '')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'colors': self.colors,
            'fonts': self.fonts,
            'styles': self.styles,
            'background_image': self.background_image
        }
    
    def generate_stylesheet(self) -> str:
        stylesheet = f"""
            QMainWindow {{
                background-color: {self.colors['background']};
                border: 1px solid {self.colors['border']};
                {f'background-image: url({self.background_image}); background-repeat: no-repeat; background-position: center;' if self.background_image else ''}
            }}
            QWidget {{
                font-family: {self.fonts['family']};
                font-size: {self.fonts['size']}px;
            }}
            QLabel {{
                font-weight: bold;
                color: {self.colors['text']};
            }}
            QPushButton {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_light']};
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.colors['hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['pressed']};
            }}
            QListWidget {{
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 4px;
            }}

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border-color: {self.colors['primary']};
                outline: none;
            }}
            QMenuBar {{
                background-color: {self.colors['secondary']};
                color: {self.colors['text']};
            }}

            QMenuBar::item {{
                color: {self.colors['text']};
            }}
            QMenuBar::item:selected {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_light']};
            }}
            QMenu {{
                background-color: {self.colors['secondary']};
                color: {self.colors['text']};
            }}
            QMenu::item:selected {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_light']};
            }}
            QStatusBar {{
                background-color: {self.colors['background']};
                border-top: 1px solid {self.colors['border']};
            }}
            .CustomTitleBar {{
                background-color: {self.colors['secondary']};
                color: {self.colors['text']};
                height: 30px;
            }}
            .TitleLabel {{
                color: {self.colors['text']};
                font-weight: bold;
                font-size: 14px;
            }}
            .TitleButton {{
                background-color: transparent;
                color: {self.colors['text']};
                border: none;
                width: 30px;
                height: 30px;
                font-size: 16px;
            }}
            .TitleButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            .TitleButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
            .CustomMenuBar {{
                background-color: {self.colors['secondary']};
                color: {self.colors['text']};
                padding: 2px 0;
            }}
            .CustomMenuBar QPushButton {{
                background-color: transparent;
                color: {self.colors['text']};
                border: none;
                padding: 4px 10px;
                font-size: 14px;
            }}
            .CustomMenuBar QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            .CustomMenuBar QMenu {{
                background-color: {self.colors['secondary']};
                color: {self.colors['text']};
            }}
            .CustomMenuBar QMenu::item:selected {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_light']};
            }}
        """
        return stylesheet


class ThemeManager:
    def __init__(self):
        self.themes_dir = Path(__file__).parent.parent / 'themes'
        self.user_themes_dir = Path.home() / '.pyhtml' / 'themes'
        self.config_file = Path.home() / '.pyhtml' / 'theme_config.json'
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None
        
        # 确保主题目录存在
        self.themes_dir.mkdir(exist_ok=True)
        # 尝试创建用户主题目录，但如果失败（如权限问题），则忽略
        try:
            self.user_themes_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f'Warning: Failed to create user themes directory: {e}')
        
        # 加载所有主题
        self.load_all_themes()
        
        # 加载上次保存的主题
        self.load_saved_theme()
        
        # 如果没有加载到主题，设置默认主题
        if not self.current_theme:
            if 'default' in self.themes:
                self.current_theme = self.themes['default']
            else:
                # 如果没有默认主题文件，创建一个默认的绿色主题
                self.create_default_theme()
                # 保存默认主题设置
                self.save_theme_config()
    
    def load_all_themes(self):
        # 加载预设主题
        self.load_themes_from_dir(self.themes_dir)
        # 加载用户自定义主题
        self.load_themes_from_dir(self.user_themes_dir)
    
    def load_themes_from_dir(self, directory: Path):
        try:
            if not directory.exists():
                return
            
            for item in directory.iterdir():
                if item.is_file() and item.suffix == '.json':
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            theme = Theme(data)
                            self.themes[theme.name.lower().replace(' ', '_')] = theme
                    except Exception as e:
                        print(f'Failed to load theme from {item}: {e}')
        except Exception as e:
            print(f'Warning: Failed to load themes from directory {directory}: {e}')
    
    def load_saved_theme(self):
        """加载上次保存的主题"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme_name = config.get('theme')
                    if theme_name:
                        self.set_theme(theme_name)
        except Exception as e:
            print(f'Warning: Failed to load saved theme: {e}')
    
    def get_theme(self, name: str) -> Optional[Theme]:
        return self.themes.get(name.lower().replace(' ', '_'))
    
    def get_all_themes(self) -> List[Theme]:
        return list(self.themes.values())
    
    def set_theme(self, name: str) -> bool:
        theme = self.get_theme(name)
        if theme:
            self.current_theme = theme
            # 保存主题设置
            self.save_theme_config()
            return True
        return False
    
    def save_theme(self, theme: Theme, is_user_theme: bool = True):
        try:
            if is_user_theme:
                save_dir = self.user_themes_dir
            else:
                save_dir = self.themes_dir
            
            # 确保保存目录存在
            save_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = save_dir / f"{theme.name.lower().replace(' ', '_')}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(theme.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 重新加载主题
            self.load_all_themes()
            return True
        except Exception as e:
            print(f'Warning: Failed to save theme: {e}')
            return False
    
    def save_theme_config(self):
        """保存主题配置到文件"""
        try:
            # 确保配置文件目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            if self.current_theme:
                config = {
                    'theme': self.current_theme.name.lower().replace(' ', '_')
                }
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'Warning: Failed to save theme config: {e}')
    
    def get_current_stylesheet(self) -> str:
        if self.current_theme:
            return self.current_theme.generate_stylesheet()
        return ''
    
    def create_theme_from_current(self, name: str, description: str = '') -> Theme:
        if not self.current_theme:
            return Theme({})
        
        theme_data = self.current_theme.to_dict()
        theme_data['name'] = name
        theme_data['description'] = description
        theme_data['author'] = 'User'
        
        return Theme(theme_data)
    
    def create_default_theme(self):
        """创建默认的绿色主题"""
        default_theme_data = {
            'name': '默认主题',
            'description': 'PyHTML的默认绿色主题',
            'author': 'PyHTML Team',
            'version': '1.0',
            'colors': {
                'primary': '#4CAF50',
                'secondary': '#333333',
                'background': '#f0f0f0',
                'text': '#333333',
                'text_light': '#ffffff',
                'border': '#dddddd',
                'hover': '#45a049',
                'pressed': '#3d8b40',
                'error': '#f44336',
                'success': '#4CAF50',
                'warning': '#ff9800',
                'info': '#2196f3'
            },
            'fonts': {
                'family': 'Microsoft YaHei',
                'size': 12
            },
            'styles': {},
            'background_image': ''
        }
        self.current_theme = Theme(default_theme_data)
        # 将默认主题添加到主题字典中
        self.themes['default'] = self.current_theme