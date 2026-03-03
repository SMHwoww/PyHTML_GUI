import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class Theme:
    """主题类，用于管理应用程序的外观样式
    
    该类负责存储主题的基本信息、颜色、字体和样式，并生成对应的样式表。
    """
    
    # 默认颜色配置
    DEFAULT_COLORS = {
        'primary': '#4CAF50',
        'secondary': '#333333',
        'background': '#f0f0f0',
        'text': '#333333',
        'text_light': '#ffffff',
        'text_black': '#000000',
        'input_background': '#ffffff',
        'menu_text': '#ffffff',
        'border': '#dddddd',
        'hover': '#45a049',
        'pressed': '#3d8b40',
        'error': '#f44336',
        'success': '#4CAF50',
        'warning': '#ff9800',
        'info': '#2196f3'
    }
    
    # 默认字体配置
    DEFAULT_FONTS = {
        'family': 'Microsoft YaHei',
        'size': 12
    }
    
    def __init__(self, data: Dict[str, Any]):
        """初始化主题对象
        
        Args:
            data: 包含主题信息的字典，支持以下键：
                - name: 主题名称
                - description: 主题描述
                - author: 主题作者
                - version: 主题版本
                - colors: 颜色配置
                - fonts: 字体配置
                - styles: 样式配置
                - background_image: 背景图片路径
        """
        self.name = data.get('name', 'Untitled')
        self.description = data.get('description', '')
        self.author = data.get('author', '')
        self.version = data.get('version', '1.0')
        
        # 初始化颜色配置，确保所有必要的键都存在
        self.colors = self.DEFAULT_COLORS.copy()
        if 'colors' in data:
            self.colors.update(data['colors'])
        
        # 初始化字体配置
        self.fonts = self.DEFAULT_FONTS.copy()
        if 'fonts' in data:
            self.fonts.update(data['fonts'])
        
        self.styles = data.get('styles', {})
        self.background_image = data.get('background_image', '')
    
    def to_dict(self) -> Dict[str, Any]:
        """将主题对象转换为字典
        
        Returns:
            包含主题所有信息的字典
        """
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
        """生成主题样式表
        
        Returns:
            包含完整样式定义的字符串
        """
        # 构建样式表字符串
        stylesheet_parts = [
            # 主窗口样式
            f"""
            QMainWindow {{
                background-color: {self.colors['background']};
                border: 1px solid {self.colors['border']};
                {f'background-image: url({self.background_image}); background-repeat: no-repeat; background-position: center;' if self.background_image else ''}
            }}
            """,
            
            # 基础组件样式
            f"""
            QWidget {{
                font-family: {self.fonts['family']};
                font-size: {self.fonts['size']}px;
                color: {self.colors['text_black']};
            }}
            QLabel {{
                font-weight: bold;
                color: {self.colors['text_black']};
            }}
            """,
            
            # 按钮样式
            f"""
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
            """,
            
            # 列表组件样式
            f"""
            QListWidget {{
                background-color: {self.colors['input_background']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
            }}
            """,
            
            # 输入组件样式
            f"""
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QCheckBox {{
                background-color: {self.colors['input_background']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 4px;
                color: {self.colors['text_black']};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border-color: {self.colors['primary']};
                outline: none;
            }}
            """,
            
            # 菜单栏样式
            f"""
            QMenuBar {{
                background-color: {self.colors['secondary']};
                color: {self.colors['menu_text']};
            }}
            QMenuBar::item {{
                color: {self.colors['menu_text']};
            }}
            QMenuBar::item:selected {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_light']};
            }}
            """,
            
            # 菜单样式
            f"""
            QMenu {{
                background-color: {self.colors['secondary']};
                color: {self.colors['menu_text']};
            }}
            QMenu::item:selected {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_light']};
            }}
            """,
            
            # 状态栏样式
            f"""
            QStatusBar {{
                background-color: {self.colors['background']};
                border-top: 1px solid {self.colors['border']};
                color: {self.colors['text_black']};
            }}
            """,
            
            # 自定义标题栏样式
            f"""
            .CustomTitleBar {{
                background-color: {self.colors['secondary']};
                color: {self.colors['menu_text']};
                height: 30px;
            }}
            .TitleLabel {{
                color: {self.colors['menu_text']};
                font-weight: bold;
                font-size: 14px;
            }}
            .TitleButton {{
                background-color: transparent;
                color: {self.colors['menu_text']};
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
            """,
            
            # 自定义菜单栏样式
            f"""
            .CustomMenuBar {{
                background-color: {self.colors['secondary']};
                color: {self.colors['menu_text']};
                padding: 2px 0;
            }}
            .CustomMenuBar QPushButton {{
                background-color: transparent;
                color: {self.colors['menu_text']};
                border: none;
                padding: 4px 10px;
                font-size: 14px;
            }}
            .CustomMenuBar QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            .CustomMenuBar QMenu {{
                background-color: {self.colors['secondary']};
                color: {self.colors['menu_text']};
            }}
            .CustomMenuBar QMenu::item:selected {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_light']};
            }}
            """
        ]
        
        return ''.join(stylesheet_parts)


class ThemeManager:
    """主题管理器类，用于管理应用程序的主题
    
    该类负责加载、保存和管理主题，包括预设主题和用户自定义主题。
    """
    
    # 路径常量
    APP_DIR = Path(__file__).parent.parent
    THEMES_DIR = APP_DIR / 'themes'
    USER_DATA_DIR = Path.home() / '.pyhtml'
    USER_THEMES_DIR = USER_DATA_DIR / 'themes'
    CONFIG_FILE = USER_DATA_DIR / 'theme_config.json'
    
    def __init__(self):
        """初始化主题管理器
        
        初始化主题目录、加载主题配置，并设置默认主题。
        """
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None
        
        # 初始化目录结构
        self._initialize_directories()
        
        # 加载所有主题
        self.load_all_themes()
        
        # 加载上次保存的主题
        self.load_saved_theme()
        
        # 如果没有加载到主题，使用默认主题
        if not self.current_theme and 'default' in self.themes:
            self.current_theme = self.themes['default']
    
    def _initialize_directories(self):
        """初始化主题相关目录
        
        确保预设主题目录和用户主题目录存在。
        """
        # 确保预设主题目录存在
        self.THEMES_DIR.mkdir(exist_ok=True)
        
        # 尝试创建用户主题目录，但如果失败（如权限问题），则忽略
        try:
            self.USER_THEMES_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f'Warning: Failed to create user themes directory: {e}')
    
    def load_all_themes(self):
        """加载所有主题
        
        加载预设主题和用户自定义主题。
        """
        # 清空现有主题
        self.themes.clear()
        
        # 加载预设主题
        self.load_themes_from_dir(self.THEMES_DIR)
        # 加载用户自定义主题
        self.load_themes_from_dir(self.USER_THEMES_DIR)
    
    def load_themes_from_dir(self, directory: Path):
        """从指定目录加载主题
        
        Args:
            directory: 主题目录路径
        """
        try:
            if not directory.exists():
                return
            
            for item in directory.iterdir():
                if item.is_file() and item.suffix == '.json':
                    try:
                        with open(item, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            theme = Theme(data)
                            # 使用标准化的主题名称作为键
                            theme_key = self._normalize_theme_name(theme.name)
                            self.themes[theme_key] = theme
                    except Exception as e:
                        print(f'Failed to load theme from {item}: {e}')
        except Exception as e:
            print(f'Warning: Failed to load themes from directory {directory}: {e}')
    
    def load_saved_theme(self):
        """加载上次保存的主题"""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme_name = config.get('theme')
                    if theme_name:
                        self.set_theme(theme_name)
        except Exception as e:
            print(f'Warning: Failed to load saved theme: {e}')
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """获取指定名称的主题
        
        Args:
            name: 主题名称
            
        Returns:
            主题对象，如果不存在则返回 None
        """
        theme_key = self._normalize_theme_name(name)
        return self.themes.get(theme_key)
    
    def get_all_themes(self) -> List[Theme]:
        """获取所有可用主题
        
        Returns:
            主题对象列表
        """
        return list(self.themes.values())
    
    def set_theme(self, name: str) -> bool:
        """设置当前主题
        
        Args:
            name: 主题名称
            
        Returns:
            是否设置成功
        """
        theme = self.get_theme(name)
        if theme:
            self.current_theme = theme
            # 保存主题设置
            self.save_theme_config()
            return True
        return False
    
    def save_theme(self, theme: Theme, is_user_theme: bool = True) -> bool:
        """保存主题
        
        Args:
            theme: 主题对象
            is_user_theme: 是否保存为用户主题
            
        Returns:
            是否保存成功
        """
        try:
            # 确定保存目录
            save_dir = self.USER_THEMES_DIR if is_user_theme else self.THEMES_DIR
            
            # 确保保存目录存在
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            file_name = f"{self._normalize_theme_name(theme.name)}.json"
            file_path = save_dir / file_name
            
            # 保存主题数据
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
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            if self.current_theme:
                config = {
                    'theme': self._normalize_theme_name(self.current_theme.name)
                }
                with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'Warning: Failed to save theme config: {e}')
    
    def get_current_stylesheet(self) -> str:
        """获取当前主题的样式表
        
        Returns:
            样式表字符串
        """
        if self.current_theme:
            return self.current_theme.generate_stylesheet()
        return ''
    
    def create_theme_from_current(self, name: str, description: str = '') -> Theme:
        """从当前主题创建新主题
        
        Args:
            name: 新主题名称
            description: 新主题描述
            
        Returns:
            新主题对象
        """
        if not self.current_theme:
            return Theme({})
        
        theme_data = self.current_theme.to_dict()
        theme_data['name'] = name
        theme_data['description'] = description
        theme_data['author'] = 'User'
        
        return Theme(theme_data)
    
    def _normalize_theme_name(self, name: str) -> str:
        """标准化主题名称
        
        将主题名称转换为小写并替换空格为下划线，用于作为字典键。
        
        Args:
            name: 原始主题名称
            
        Returns:
            标准化后的主题名称
        """
        return name.lower().replace(' ', '_')
    
