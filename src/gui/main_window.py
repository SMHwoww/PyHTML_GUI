import sys
import os
import json
import time
import threading
import webbrowser
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QListWidget, QListWidgetItem, QSplitter, QFileDialog, QMessageBox,
        QAction, QStatusBar, QLabel, QPushButton, QLineEdit, QComboBox, QColorDialog,
        QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit, QFontComboBox, QMenu,
        QShortcut, QDialog, QInputDialog
    )
    from PyQt5.QtCore import Qt, QTimer, QRect, QEvent, QThread, pyqtSignal, QCoreApplication
    from PyQt5.QtGui import QColor, QFont, QPainter, QRegion, QIcon, QPixmap, QKeySequence, QPainterPath
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    print('Warning: PyQt5 not installed. GUI will not be available.')

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import Project, ComponentLoader, HTMLGenerator, PreviewServer
from core.cloudflare_worker import CloudflareWorkerGenerator
from core.theme import ThemeManager, Theme
from core.ai_client import AIDialogWidget, AIApiConfigDialog, AIClient
from core.prompt_generator import PromptGenerator
from utils import get_components_dir


COLOR_NAME_MAP = {
    'primary': '主色',
    'secondary': '次要色',
    'background': '背景色',
    'text': '文本色',
    'text_light': '浅色文本',
    'border': '边框色',
    'hover': '悬停色',
    'pressed': '按下色'
}


class MainWindow(QMainWindow if HAS_PYQT else object):
    def __init__(self):
        if not HAS_PYQT:
            raise ImportError('PyQt5 is required for GUI')
        
        super().__init__()
        self.project = Project('Untitled')
        self.component_loader = ComponentLoader(str(get_components_dir()))
        self.component_loader.load_builtin_components()
        self.html_generator = HTMLGenerator()
        self.cloudflare_worker_generator = CloudflareWorkerGenerator()
        self.preview_server = PreviewServer(8765)
        self.theme_manager = ThemeManager()
        
        self._background_pixmap_cache = None
        self._background_path_cache = None
        
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_interval = 30000
        self.auto_save_timer.start(self.auto_save_interval)
        
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_delay = 300
        
        self.copied_component = None
        
        self.init_ui()
        self.refresh_component_library()
        self.add_shortcuts()
    
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 1200, 800)
        
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'asset', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.apply_theme()
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        main_layout.addWidget(self._create_title_bar())
        main_layout.addWidget(self._create_menu_bar())
        main_layout.addWidget(self._create_central_content())
        
        self.setCentralWidget(main_widget)
        
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('就绪')
        
        self.setWindowRadius(10)
    
    def _create_title_bar(self):
        title_bar = QWidget()
        title_bar.setObjectName('CustomTitleBar')
        title_bar.setStyleSheet('''
            .CustomTitleBar {
                background-color: #333;
                color: white;
                height: 30px;
            }
        ''')
        title_bar.setFixedHeight(30)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(0)
        
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(5, 0, 5, 0)
        left_layout.setSpacing(10)
        
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'asset', 'icon.png')
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(20, 20)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText('H')
            icon_label.setStyleSheet('''
                QLabel {
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    background-color: #4CAF50;
                    border-radius: 10px;
                    min-width: 20px;
                    min-height: 20px;
                }
            ''')
        left_layout.addWidget(icon_label)
        
        title_label = QLabel('pyHTML - 组件化HTML生成器')
        title_label.setObjectName('TitleLabel')
        title_label.setStyleSheet('''
            .TitleLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        ''')
        left_layout.addWidget(title_label)
        
        title_layout.addLayout(left_layout)
        title_layout.addStretch(1)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        
        min_button = self._create_title_button('−', self.showMinimized)
        button_layout.addWidget(min_button)
        
        self.max_button = self._create_title_button('□', self.toggle_maximize)
        button_layout.addWidget(self.max_button)
        
        close_button = self._create_title_button('×', self.close, is_close=True)
        button_layout.addWidget(close_button)
        
        title_layout.addLayout(button_layout)
        
        self.drag_position = None
        title_bar.mousePressEvent = self.title_bar_mouse_press_event
        title_bar.mouseMoveEvent = self.title_bar_mouse_move_event
        
        return title_bar
    
    def _create_title_button(self, text, callback, is_close=False):
        btn = QPushButton(text)
        btn.setObjectName('TitleButton')
        if is_close:
            btn.setStyleSheet('''
                .TitleButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    width: 30px;
                    height: 30px;
                    font-size: 16px;
                }
                .TitleButton:hover {
                    background-color: rgba(255, 0, 0, 0.5);
                }
                .TitleButton:pressed {
                    background-color: rgba(255, 0, 0, 0.7);
                }
            ''')
        else:
            btn.setStyleSheet('''
                .TitleButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    width: 30px;
                    height: 30px;
                    font-size: 16px;
                }
                .TitleButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                .TitleButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            ''')
        btn.clicked.connect(callback)
        return btn
    
    def _create_menu_bar(self):
        menubar = QWidget()
        menubar.setObjectName('CustomMenuBar')
        menubar.setStyleSheet('''
            .CustomMenuBar {
                background-color: #333;
                color: white;
                padding: 2px 0;
            }
        ''')
        menubar.setFixedHeight(25)
        
        menu_layout = QHBoxLayout(menubar)
        menu_layout.setContentsMargins(5, 0, 5, 0)
        menu_layout.setSpacing(0)
        
        file_menu = self._create_file_menu()
        view_menu = self._create_view_menu()
        ai_menu = self._create_ai_menu()
        settings_menu = self._create_settings_menu()
        
        file_menu_button = QPushButton('文件(&F)')
        file_menu_button.setMenu(file_menu)
        menu_layout.addWidget(file_menu_button)
        
        view_menu_button = QPushButton('视图(&V)')
        view_menu_button.setMenu(view_menu)
        menu_layout.addWidget(view_menu_button)
        
        ai_menu_button = QPushButton('AI助手beta(&A)')
        ai_menu_button.setMenu(ai_menu)
        menu_layout.addWidget(ai_menu_button)
        
        settings_menu_button = QPushButton('设置(&S)')
        settings_menu_button.setMenu(settings_menu)
        menu_layout.addWidget(settings_menu_button)
        
        menu_layout.addStretch(1)
        
        return menubar
    
    def _create_file_menu(self):
        menu = QMenu('文件(&F)', self)
        menu.setStyleSheet('''
            QMenu {
                background-color: #333;
                color: white;
                padding: 2px 0;
            }
            QMenu::item {
                color: white;
                padding: 4px 10px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
        ''')
        
        new_action = QAction('新建项目(&N)', self)
        new_action.triggered.connect(self.new_project)
        menu.addAction(new_action)
        
        open_action = QAction('打开项目(&O)', self)
        open_action.triggered.connect(self.open_project)
        menu.addAction(open_action)
        
        save_action = QAction('保存项目(&S)', self)
        save_action.triggered.connect(self.save_project)
        menu.addAction(save_action)
        
        menu.addSeparator()
        
        import_component_action = QAction('导入组件(&I)', self)
        import_component_action.triggered.connect(self.import_component)
        menu.addAction(import_component_action)
        
        menu.addSeparator()
        
        export_action = QAction('导出HTML(&E)', self)
        export_action.triggered.connect(self.export_html)
        menu.addAction(export_action)
        
        export_worker_action = QAction('部署Cloudflare Worker(&W)', self)
        export_worker_action.triggered.connect(self.export_cloudflare_worker)
        menu.addAction(export_worker_action)
        
        return menu
    
    def _create_view_menu(self):
        menu = QMenu('视图(&V)', self)
        menu.setStyleSheet('''
            QMenu {
                background-color: #333;
                color: white;
                padding: 2px 0;
            }
            QMenu::item {
                color: white;
                padding: 4px 10px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
        ''')
        
        preview_action = QAction('预览(&P)', self)
        preview_action.triggered.connect(self.toggle_preview)
        menu.addAction(preview_action)
        
        return menu
    
    def _create_ai_menu(self):
        menu = QMenu('AI助手beta(&A)', self)
        menu.setStyleSheet('''
            QMenu {
                background-color: #333;
                color: white;
                padding: 2px 0;
            }
            QMenu::item {
                color: white;
                padding: 4px 10px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
        ''')
        
        ai_dialog_action = QAction('打开AI对话(&D)', self)
        ai_dialog_action.triggered.connect(self.open_ai_dialog)
        menu.addAction(ai_dialog_action)
        
        ai_config_action = QAction('AI配置(&C)', self)
        ai_config_action.triggered.connect(self.open_ai_config)
        menu.addAction(ai_config_action)
        
        return menu
    
    def _create_settings_menu(self):
        menu = QMenu('设置(&S)', self)
        menu.setStyleSheet('''
            QMenu {
                background-color: #333;
                color: white;
                padding: 2px 0;
            }
            QMenu::item {
                color: white;
                padding: 4px 10px;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
        ''')
        
        head_settings_action = QAction('Head设置(&H)', self)
        head_settings_action.triggered.connect(self.open_head_settings)
        menu.addAction(head_settings_action)
        
        theme_menu = menu.addMenu('主题(&T)')
        themes = self.theme_manager.get_all_themes()
        for theme in themes:
            theme_action = QAction(theme.name, self)
            theme_action.triggered.connect(lambda checked, name=theme.name: self.change_theme(name))
            theme_menu.addAction(theme_action)
        
        theme_editor_action = QAction('主题编辑器(&E)', self)
        theme_editor_action.triggered.connect(self.open_theme_editor)
        theme_menu.addAction(theme_editor_action)
        
        return menu
    
    def _create_central_content(self):
        content_widget = QWidget()
        main_layout = QHBoxLayout(content_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = self._create_left_panel()
        middle_panel = self._create_middle_panel()
        right_panel = self._create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        total_width = self.width()
        splitter.setSizes([int(total_width * 0.2), int(total_width * 0.3), int(total_width * 0.5)])
        splitter.setOpaqueResize(True)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
        return content_widget
    
    def _create_left_panel(self):
        panel = QWidget()
        panel.setStyleSheet('''
            QWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        ''')
        layout = QVBoxLayout(panel)
        
        label = QLabel('组件库 (双击添加)')
        label.setStyleSheet('background-color: transparent;')
        layout.addWidget(label)
        
        self.component_library = QListWidget()
        self.component_library.setStyleSheet('''
            QListWidget {
                background-color: transparent;
                border: none;
            }
        ''')
        self.component_library.setDragEnabled(True)
        self.component_library.itemDoubleClicked.connect(self.add_component_from_library)
        layout.addWidget(self.component_library)
        
        return panel
    
    def _create_middle_panel(self):
        panel = QWidget()
        panel.setStyleSheet('''
            QWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        ''')
        layout = QVBoxLayout(panel)
        
        label = QLabel('页面组件')
        label.setStyleSheet('background-color: transparent;')
        layout.addWidget(label)
        
        self.page_components = QListWidget()
        self.page_components.setStyleSheet('''
            QListWidget {
                background-color: transparent;
                border: none;
            }
        ''')
        self.page_components.setSelectionMode(QListWidget.SingleSelection)
        self.page_components.setAcceptDrops(True)
        self.page_components.setDragDropMode(QListWidget.DragDrop)
        self.page_components.currentItemChanged.connect(self.on_component_selected)
        self.page_components.dragEnterEvent = self.drag_enter_event
        self.page_components.dropEvent = self.drop_event
        self.page_components.setContextMenuPolicy(Qt.CustomContextMenu)
        self.page_components.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.page_components)
        
        button_layout = QHBoxLayout()
        
        move_up_button = QPushButton('上移')
        move_up_button.clicked.connect(self.move_component_up)
        button_layout.addWidget(move_up_button)
        
        move_down_button = QPushButton('下移')
        move_down_button.clicked.connect(self.move_component_down)
        button_layout.addWidget(move_down_button)
        
        export_button = QPushButton('导出HTML')
        export_button.clicked.connect(self.export_html)
        button_layout.addWidget(export_button)
        
        preview_button = QPushButton('预览')
        preview_button.clicked.connect(self.toggle_preview)
        button_layout.addWidget(preview_button)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def _create_right_panel(self):
        panel = QWidget()
        panel.setStyleSheet('''
            QWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        ''')
        layout = QVBoxLayout(panel)
        
        label = QLabel('属性编辑')
        label.setStyleSheet('background-color: transparent;')
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(label)
        
        self.properties_panel = QWidget()
        self.properties_panel.setStyleSheet('background-color: transparent;')
        self.properties_layout = QVBoxLayout(self.properties_panel)
        self.properties_layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.properties_panel)
        
        layout.addStretch(1)
        
        self.clear_properties_panel()
        
        return panel
    
    def apply_theme(self):
        stylesheet = self.theme_manager.get_current_stylesheet()
        self.setStyleSheet(stylesheet)
        self._background_pixmap_cache = None
        self._background_path_cache = None
        self.update()
    
    def setWindowRadius(self, radius):
        """设置窗口圆角，避免渲染问题"""
        if self.isMaximized():
            self.setMask(QRegion())
            return
        
        try:
            path = QPainterPath()
            rect = self.rect()
            if rect.width() > 0 and rect.height() > 0:
                path.addRoundedRect(0, 0, rect.width(), rect.height(), radius, radius)
                region = QRegion(path.toFillPolygon())
                self.setMask(region)
        except Exception:
            self.setMask(QRegion())
    
    def title_bar_mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def title_bar_mouse_move_event(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.max_button.setText('□')
            QTimer.singleShot(50, lambda: self.setWindowRadius(10))
        else:
            self.setMask(QRegion())
            self.showMaximized()
            self.max_button.setText('▢')
    
    def refresh_component_library(self):
        self.component_library.clear()
        for component in self.component_loader.get_all_components():
            item = QListWidgetItem(f'{component.display_name} ({component.name})')
            item.setData(Qt.UserRole, component.name)
            self.component_library.addItem(item)
    
    def refresh_page_components(self):
        self.page_components.clear()
        for i, component in enumerate(self.project.components):
            item = QListWidgetItem(f'{i+1}. {component.display_name}')
            item.setData(Qt.UserRole, i)
            self.page_components.addItem(item)
    
    def clear_layout_recursive(self, layout):
        if layout is None:
            return
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item is None:
                continue
            child_layout = item.layout()
            if child_layout:
                self.clear_layout_recursive(child_layout)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def clear_properties_panel(self):
        self.clear_layout_recursive(self.properties_layout)
    
    def add_component_from_library(self, item):
        component_name = item.data(Qt.UserRole)
        component = self.component_loader.create_instance(component_name)
        if component:
            self.project.add_component(component)
            self.refresh_page_components()
            self.statusBar.showMessage(f'已添加组件: {component.display_name}')
    
    def on_component_selected(self, current, previous):
        if current:
            index = current.data(Qt.UserRole)
            component = self.project.components[index]
            self.update_properties_panel(component)
        else:
            self.clear_properties_panel()
    
    def remove_selected_component(self):
        current_item = self.page_components.currentItem()
        if current_item:
            index = current_item.data(Qt.UserRole)
            self.project.remove_component(index)
            self.refresh_page_components()
            self.clear_properties_panel()
            self.statusBar.showMessage('已删除组件')
    
    def move_component_up(self):
        current_item = self.page_components.currentItem()
        if current_item:
            index = current_item.data(Qt.UserRole)
            if index > 0:
                self.project.components[index], self.project.components[index-1] = self.project.components[index-1], self.project.components[index]
                self.refresh_page_components()
                self.page_components.setCurrentRow(index-1)
                self.statusBar.showMessage('组件已上移')
                self.preview_timer.start(self.preview_delay)
    
    def move_component_down(self):
        current_item = self.page_components.currentItem()
        if current_item:
            index = current_item.data(Qt.UserRole)
            if index < len(self.project.components) - 1:
                self.project.components[index], self.project.components[index+1] = self.project.components[index+1], self.project.components[index]
                self.refresh_page_components()
                self.page_components.setCurrentRow(index+1)
                self.statusBar.showMessage('组件已下移')
                self.preview_timer.start(self.preview_delay)
    
    def copy_component(self):
        current_item = self.page_components.currentItem()
        if current_item:
            index = current_item.data(Qt.UserRole)
            component = self.project.components[index]
            self.copied_component = {
                'name': component.name,
                'values': component.values.copy()
            }
            self.statusBar.showMessage(f'已复制组件: {component.display_name}')
    
    def paste_component(self):
        if self.copied_component:
            component_name = self.copied_component['name']
            component = self.component_loader.create_instance(component_name)
            if component:
                component.values = self.copied_component['values'].copy()
                self.project.add_component(component)
                self.refresh_page_components()
                self.page_components.setCurrentRow(len(self.project.components) - 1)
                self.statusBar.showMessage(f'已粘贴组件: {component.display_name}')
                self.preview_timer.start(self.preview_delay)
    
    def add_shortcuts(self):
        delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        delete_shortcut.activated.connect(self.remove_selected_component)
        
        copy_shortcut = QShortcut(QKeySequence('Ctrl+C'), self)
        copy_shortcut.activated.connect(self.copy_component)
        
        paste_shortcut = QShortcut(QKeySequence('Ctrl+V'), self)
        paste_shortcut.activated.connect(self.paste_component)
    
    def show_context_menu(self, position):
        menu = QMenu()
        
        copy_action = menu.addAction('复制 (Ctrl+C)')
        copy_action.triggered.connect(self.copy_component)
        
        paste_action = menu.addAction('粘贴 (Ctrl+V)')
        paste_action.triggered.connect(self.paste_component)
        
        delete_action = menu.addAction('删除 (Delete)')
        delete_action.triggered.connect(self.remove_selected_component)
        
        ai_optimize_action = menu.addAction('使用AI优化')
        ai_optimize_action.triggered.connect(self.optimize_component_with_ai)
        
        menu.exec_(self.page_components.mapToGlobal(position))
    
    def drag_enter_event(self, event):
        if event.source() == self.component_library or event.source() == self.page_components:
            event.accept()
        else:
            event.ignore()
    
    def drop_event(self, event):
        if event.source() == self.component_library:
            item = event.source().currentItem()
            if item:
                component_name = item.data(Qt.UserRole)
                component = self.component_loader.create_instance(component_name)
                if component:
                    drop_pos = self.page_components.dropIndicatorPosition()
                    if drop_pos == QListWidget.OnItem or drop_pos == QListWidget.OnItemButtom:
                        current_item = self.page_components.itemAt(event.pos())
                        if current_item:
                            index = current_item.data(Qt.UserRole) + 1
                            self.project.components.insert(index, component)
                        else:
                            self.project.add_component(component)
                    else:
                        self.project.add_component(component)
                    self.refresh_page_components()
                    self.statusBar.showMessage(f'已添加组件: {component.display_name}')
                    self.preview_timer.start(self.preview_delay)
        elif event.source() == self.page_components:
            source_item = event.source().currentItem()
            if source_item:
                source_index = source_item.data(Qt.UserRole)
                target_item = self.page_components.itemAt(event.pos())
                if target_item:
                    target_index = target_item.data(Qt.UserRole)
                    component = self.project.components.pop(source_index)
                    if source_index < target_index:
                        self.project.components.insert(target_index, component)
                    else:
                        self.project.components.insert(target_index, component)
                    self.refresh_page_components()
                    new_index = target_index if source_index > target_index else target_index - 1
                    self.page_components.setCurrentRow(new_index)
                    self.statusBar.showMessage('组件位置已调整')
                    self.preview_timer.start(self.preview_delay)
    
    def update_properties_panel(self, component):
        self.clear_properties_panel()
        
        component_label = QLabel(f'组件: {component.display_name}')
        component_label.setStyleSheet('font-size: 14px; font-weight: bold; margin-bottom: 10px;')
        self.properties_layout.addWidget(component_label)
        
        for field in component.fields:
            field_name = field['name']
            field_type = field['type']
            field_label = field['label']
            field_value = component.get_value(field_name)
            
            field_container = QWidget()
            field_layout = QVBoxLayout(field_container)
            field_layout.setContentsMargins(0, 0, 0, 10)
            
            if field_type != 'boolean':
                label = QLabel(field_label)
                label.setStyleSheet('font-size: 12px; font-weight: normal; color: #555; margin-bottom: 4px;')
                field_layout.addWidget(label)
            
            if field_type == 'string':
                line_edit = QLineEdit()
                line_edit.setText(str(field_value) if field_value is not None else '')
                line_edit.setPlaceholderText(field.get('placeholder', ''))
                line_edit.textChanged.connect(lambda text, fn=field_name, c=component: 
                    (c.set_value(fn, text), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(line_edit)
            
            elif field_type == 'number':
                step = field.get('step', 1)
                if isinstance(step, float) or isinstance(field.get('default'), float):
                    spin_box = QDoubleSpinBox()
                    spin_box.setDecimals(2)
                else:
                    spin_box = QSpinBox()
                
                if 'min' in field:
                    spin_box.setMinimum(field['min'])
                if 'max' in field:
                    spin_box.setMaximum(field['max'])
                spin_box.setSingleStep(step)
                
                if field_value is not None:
                    spin_box.setValue(field_value)
                
                spin_box.valueChanged.connect(lambda value, fn=field_name, c=component: 
                    (c.set_value(fn, value), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(spin_box)
            
            elif field_type == 'boolean':
                check_box = QCheckBox(field_label)
                check_box.setChecked(bool(field_value))
                check_box.stateChanged.connect(lambda state, fn=field_name, c=component: 
                    (c.set_value(fn, state == Qt.Checked), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(check_box)
            
            elif field_type == 'textarea':
                text_edit = QTextEdit()
                text_edit.setPlainText(str(field_value) if field_value is not None else '')
                text_edit.setPlaceholderText(field.get('placeholder', ''))
                if 'rows' in field:
                    text_edit.setMaximumHeight(field['rows'] * 20)
                else:
                    text_edit.setMaximumHeight(100)
                text_edit.textChanged.connect(lambda fn=field_name, c=component, te=text_edit: 
                    (c.set_value(fn, te.toPlainText()), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(text_edit)
            
            elif field_type == 'font':
                font_layout = QHBoxLayout()
                font_layout.setSpacing(5)
                
                font_combo = QFontComboBox()
                font_combo.setMinimumWidth(150)
                default_font = field.get('default', 'Arial')
                font_combo.setCurrentFont(QFont(default_font))
                font_combo.currentFontChanged.connect(lambda font, fn=field_name, c=component: 
                    (c.set_value(fn, font.family()), self.preview_timer.start(self.preview_delay)))
                font_layout.addWidget(font_combo)
                
                size_spin = QSpinBox()
                size_spin.setRange(8, 72)
                size_spin.setFixedWidth(60)
                default_size = field.get('default_size', 16)
                size_spin.setValue(default_size)
                size_field_name = f'{field_name}_size'
                size_spin.valueChanged.connect(lambda value, fn=size_field_name, c=component: 
                    (c.set_value(fn, value), self.preview_timer.start(self.preview_delay)))
                font_layout.addWidget(size_spin)
                
                field_layout.addLayout(font_layout)
            
            elif field_type == 'select':
                combo_box = QComboBox()
                for option in field['options']:
                    combo_box.addItem(option['label'], option['value'])
                index = combo_box.findData(field_value)
                if index >= 0:
                    combo_box.setCurrentIndex(index)
                combo_box.currentIndexChanged.connect(lambda index, cb=combo_box, fn=field_name, c=component: 
                    (c.set_value(fn, cb.itemData(index)), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(combo_box)
            
            elif field_type == 'color':
                color_layout = QHBoxLayout()
                color_layout.setSpacing(5)
                
                color_label = QLabel(field_value)
                color_label.setFixedWidth(80)
                color_label.setStyleSheet('border: 1px solid #ddd; padding: 2px 5px; border-radius: 3px;')
                
                color_button = QPushButton()
                color_button.setFixedWidth(40)
                color_button.setStyleSheet(f'background-color: {field_value}; border: 1px solid #ddd; border-radius: 3px;')
                color_button.clicked.connect(lambda checked, fn=field_name, c=component, btn=color_button, lbl=color_label: 
                    (self.open_color_dialog(fn, c, btn), lbl.setText(c.get_value(fn)), self.preview_timer.start(self.preview_delay)))
                
                color_layout.addWidget(color_label)
                color_layout.addWidget(color_button)
                field_layout.addLayout(color_layout)
            
            elif field_type == 'picture':
                picture_layout = QVBoxLayout()
                
                picture_edit = QLineEdit()
                picture_edit.setText(str(field_value) if field_value is not None else '')
                picture_edit.setPlaceholderText('请输入图片URL或点击上传')
                picture_edit.textChanged.connect(lambda text, fn=field_name, c=component: 
                    (c.set_value(fn, text), self.preview_timer.start(self.preview_delay)))
                picture_layout.addWidget(picture_edit)
                
                upload_button = QPushButton('上传图片')
                upload_button.clicked.connect(lambda checked, fn=field_name, c=component, le=picture_edit: 
                    (self.upload_picture(fn, c, le), self.preview_timer.start(self.preview_delay)))
                picture_layout.addWidget(upload_button)
                
                field_layout.addLayout(picture_layout)
            
            elif field_type == 'music':
                music_edit = QLineEdit()
                music_edit.setText(str(field_value) if field_value is not None else '')
                music_edit.setPlaceholderText('请输入音乐URL或网易云歌曲ID')
                
                def handle_music_input(text, fn=field_name, c=component):
                    if text and not text.startswith('http'):
                        music_url = f'https://music.163.com/song/media/outer/url?id={text}'
                        c.set_value(fn, music_url)
                        music_edit.setText(music_url)
                    else:
                        c.set_value(fn, text)
                    self.preview_timer.start(self.preview_delay)
                
                music_edit.textChanged.connect(handle_music_input)
                field_layout.addWidget(music_edit)
            
            self.properties_layout.addWidget(field_container)
    
    def export_html(self):
        file_path, _ = QFileDialog.getSaveFileName(self, '导出HTML', '', 'HTML File (*.html)')
        if file_path:
            try:
                self.html_generator.save_html(self.project.components, file_path, self.project.title, self.project.head_config)
                self.statusBar.showMessage(f'已导出: {file_path}')
                QMessageBox.information(self, '成功', f'HTML已导出到: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法导出HTML: {str(e)}')
    
    def export_cloudflare_worker(self):
        directory = QFileDialog.getExistingDirectory(self, '选择Cloudflare Worker项目目录')
        if not directory:
            return
        
        try:
            import subprocess
            auto_deploy_enabled = False
            api_token = os.environ.get('CLOUDFLARE_API_TOKEN')
            worker_name = self.project.title
            custom_domain = ''
            
            try:
                result = subprocess.run(
                    ['npm', '--version'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    shell=True
                )
                if result.returncode == 0:
                    dialog = QDialog(self)
                    dialog.setWindowTitle('Cloudflare Worker部署选项')
                    layout = QVBoxLayout(dialog)
                    
                    layout.addWidget(QLabel('请选择部署选项:'))
                    
                    auto_deploy = QCheckBox('自动部署到Cloudflare')
                    layout.addWidget(auto_deploy)
                    
                    worker_name_input = QLineEdit()
                    worker_name_input.setPlaceholderText('Worker名称 (可选，默认使用网站标题)')
                    if self.project.title:
                        worker_name_input.setText(self.project.title)
                    layout.addWidget(QLabel('Worker名称:'))
                    layout.addWidget(worker_name_input)
                    
                    custom_domain_input = QLineEdit()
                    custom_domain_input.setPlaceholderText('自定义域名 (可选，如: example.com)')
                    layout.addWidget(QLabel('自定义域名:'))
                    layout.addWidget(custom_domain_input)
                    
                    api_token_input = QLineEdit()
                    api_token_input.setPlaceholderText('请输入Cloudflare API token (可选，优先使用环境变量)')
                    api_token_input.setEchoMode(QLineEdit.Password)
                    if api_token:
                        api_token_input.setText(api_token)
                        layout.addWidget(QLabel('环境变量已设置，可以使用或修改。'))
                    else:
                        layout.addWidget(QLabel('未设置环境变量，请输入API token。'))
                    layout.addWidget(QLabel('API Token:'))
                    layout.addWidget(api_token_input)
                    
                    button_layout = QHBoxLayout()
                    ok_button = QPushButton('确定')
                    cancel_button = QPushButton('取消')
                    button_layout.addWidget(ok_button)
                    button_layout.addWidget(cancel_button)
                    layout.addLayout(button_layout)
                    
                    ok_button.clicked.connect(dialog.accept)
                    cancel_button.clicked.connect(dialog.reject)
                    
                    if dialog.exec_() == QDialog.Accepted:
                        auto_deploy_enabled = auto_deploy.isChecked()
                        user_api_token = api_token_input.text().strip()
                        if user_api_token:
                            api_token = user_api_token
                        worker_name = worker_name_input.text().strip()
                        custom_domain = custom_domain_input.text().strip()
                else:
                    QMessageBox.warning(self, '警告', '系统找不到npm命令。将仅创建项目结构，不进行自动部署。')
            except FileNotFoundError:
                QMessageBox.warning(self, '警告', '系统找不到npm命令。将仅创建项目结构，不进行自动部署。')
            
            project_path = self.cloudflare_worker_generator.create_worker_project(
                directory,
                self.project.components,
                self.project.title,
                self.project.head_config,
                worker_name,
                custom_domain
            )
            
            if auto_deploy_enabled:
                log_dialog = QDialog(self)
                log_dialog.setWindowTitle('部署日志')
                log_dialog.setGeometry(300, 200, 800, 500)
                log_layout = QVBoxLayout(log_dialog)
                
                log_text = QTextEdit()
                log_text.setReadOnly(True)
                log_text.setStyleSheet('font-family: Consolas, Monaco, monospace;')
                log_layout.addWidget(log_text)
                
                close_button = QPushButton('关闭')
                close_button.clicked.connect(log_dialog.close)
                log_layout.addWidget(close_button)
                
                log_dialog.show()
                
                def log_callback(message):
                    class LogEvent(QEvent):
                        def __init__(self, message):
                            super().__init__(QEvent.User)
                            self.message = message
                    QCoreApplication.postEvent(self, LogEvent(message))
                
                self.statusBar.showMessage('部署已开始...')
                
                def deploy_in_thread():
                    success, deployed_url = self.cloudflare_worker_generator.deploy_worker(project_path, api_token, custom_domain, log_callback)
                    class DeployFinishedEvent(QEvent):
                        def __init__(self, success, project_path, deployed_url, log_dialog):
                            super().__init__(QEvent.User)
                            self.success = success
                            self.project_path = project_path
                            self.deployed_url = deployed_url
                            self.log_dialog = log_dialog
                    QCoreApplication.postEvent(self, DeployFinishedEvent(success, project_path, deployed_url, log_dialog))
                
                deploy_thread = threading.Thread(target=deploy_in_thread, daemon=True)
                deploy_thread.start()
            else:
                self.statusBar.showMessage(f'已创建Cloudflare Worker项目: {project_path}')
                QMessageBox.information(self, '成功', f'Cloudflare Worker项目已创建:\n\n{project_path}')
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法创建Cloudflare Worker项目: {str(e)}')
    
    def toggle_preview(self):
        try:
            url = self.preview_server.start(self.project)
            self.preview_server.open_browser()
            self.statusBar.showMessage(f'预览已打开: {url}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法启动预览: {str(e)}')
    
    def open_color_dialog(self, field_name, component, button):
        current_color = component.get_value(field_name)
        if not current_color:
            current_color = '#000000'
        
        color = QColorDialog.getColor(QColor(current_color), self, '选择颜色')
        if color.isValid():
            component.set_value(field_name, color.name())
            button.setStyleSheet(f'background-color: {color.name()}; border: 1px solid #ddd; border-radius: 3px;')
    
    def upload_picture(self, field_name, component, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择图片', '', '图片文件 (*.jpg *.jpeg *.png *.gif *.webp)')
        if not file_path:
            return
        
        try:
            import requests
            
            token_url = 'https://picui.cn/api/v1/images/tokens'
            token_payload = {'num': 1, 'seconds': 3600}
            token_headers = {'Accept': 'application/json'}
            
            token_response = requests.post(token_url, json=token_payload, headers=token_headers)
            if token_response.status_code != 200:
                QMessageBox.warning(self, '警告', f'获取token失败: 状态码 {token_response.status_code}')
                return
            
            token_data = token_response.json()
            if not token_data.get('status'):
                QMessageBox.warning(self, '警告', f'获取token失败: {token_data.get("message", "未知错误")}')
                return
            
            tokens = token_data.get('data', {}).get('tokens', [])
            if not tokens:
                QMessageBox.warning(self, '警告', '获取token失败: 未返回token')
                return
            
            token = tokens[0].get('token')
            if not token:
                QMessageBox.warning(self, '警告', '获取token失败: token为空')
                return
            
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                data = {'token': token, 'permission': 1}
                
                response = requests.post('https://picui.cn/api/v1/upload', files=files, data=data)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status'):
                        image_data = data.get('data', {})
                        image_url = image_data.get('links', {}).get('url')
                        if image_url:
                            component.set_value(field_name, image_url)
                            line_edit.setText(image_url)
                            self.save_picture_info(image_data)
                            self.statusBar.showMessage('图片上传成功')
                        else:
                            QMessageBox.warning(self, '警告', '上传成功但未返回图片URL')
                    else:
                        QMessageBox.warning(self, '警告', f'上传失败: {data.get("message", "未知错误")}')
                else:
                    QMessageBox.warning(self, '警告', f'上传失败: 状态码 {response.status_code}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'上传失败: {str(e)}')
    
    def save_picture_info(self, image_data):
        save_dir = 'C:\\Users\\Administrator\\.pyhtml\\picturestemp'
        os.makedirs(save_dir, exist_ok=True)
        timestamp = int(time.time() * 1000)
        file_name = f'picture_{timestamp}.json'
        file_path = os.path.join(save_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(image_data, f, ensure_ascii=False, indent=2)
        
        print(f'图片信息已保存到: {file_path}')
    
    def import_component(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter('压缩包 (*.zip)')
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                try:
                    import tempfile
                    from zipfile import ZipFile
                    
                    path = selected_files[0]
                    with tempfile.TemporaryDirectory() as temp_dir:
                        try:
                            with ZipFile(path, 'r') as zip_ref:
                                zip_ref.extractall(temp_dir)
                        except Exception as e:
                            QMessageBox.critical(self, '错误', f'无法解压压缩包: {str(e)}')
                            return
                        
                        component_dir = Path(temp_dir)
                        if (component_dir / 'config.json').exists():
                            component = self.component_loader.load_component(str(component_dir))
                            if component:
                                self.refresh_component_library()
                                self.statusBar.showMessage(f'已导入组件: {component.display_name}')
                                QMessageBox.information(self, '成功', f'已导入组件: {component.display_name}')
                        else:
                            imported_count = 0
                            for item in component_dir.iterdir():
                                if item.is_dir() and (item / 'config.json').exists():
                                    self.component_loader.load_component(str(item))
                                    imported_count += 1
                            if imported_count > 0:
                                self.refresh_component_library()
                                self.statusBar.showMessage(f'已导入 {imported_count} 个组件')
                                QMessageBox.information(self, '成功', f'已导入 {imported_count} 个组件')
                            else:
                                QMessageBox.warning(self, '警告', '未找到有效的组件目录')
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'无法导入组件: {str(e)}')
    
    def new_project(self):
        self.project = Project('Untitled')
        self.refresh_page_components()
        self.clear_properties_panel()
        self.statusBar.showMessage('已创建新项目')
    
    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '打开项目', '', 'pyHTML项目文件 (*.pyhtml)')
        if file_path:
            try:
                self.project = Project.load(file_path, self.component_loader)
                self.refresh_page_components()
                self.clear_properties_panel()
                if hasattr(self.project, 'theme'):
                    self.change_theme(self.project.theme)
                self.statusBar.showMessage(f'已打开项目: {self.project.name}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法打开项目: {str(e)}')
    
    def save_project(self):
        if not self.project.file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, '保存项目', '', 'pyHTML项目文件 (*.pyhtml)')
            if not file_path:
                return
        else:
            file_path = self.project.file_path
        
        try:
            if self.theme_manager.current_theme:
                self.project.theme = self.theme_manager.current_theme.name.lower().replace(' ', '_')
            self.project.save(file_path)
            self.statusBar.showMessage(f'已保存项目: {self.project.name}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法保存项目: {str(e)}')
    
    def auto_save(self):
        if self.project.file_path:
            try:
                self.project.save()
                self.statusBar.showMessage(f'自动保存: {self.project.name}')
            except Exception:
                pass
    
    def update_preview(self):
        self.preview_server.update_html(self.project)
        self.statusBar.showMessage('预览已更新')
    
    def change_theme(self, theme_name):
        if self.theme_manager.set_theme(theme_name):
            self.apply_theme()
            self.statusBar.showMessage(f'已切换到主题: {theme_name}')
    
    def open_theme_editor(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('主题编辑器')
        dialog.setGeometry(200, 200, 800, 600)
        
        main_layout = QVBoxLayout(dialog)
        
        info_layout = QHBoxLayout()
        name_label = QLabel('主题名称:')
        theme_name_edit = QLineEdit()
        if self.theme_manager.current_theme:
            theme_name_edit.setText(self.theme_manager.current_theme.name)
        info_layout.addWidget(name_label)
        info_layout.addWidget(theme_name_edit)
        
        desc_label = QLabel('描述:')
        theme_desc_edit = QLineEdit()
        if self.theme_manager.current_theme:
            theme_desc_edit.setText(self.theme_manager.current_theme.description)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(theme_desc_edit)
        main_layout.addLayout(info_layout)
        
        color_group = QVBoxLayout()
        color_group.addWidget(QLabel('颜色设置:'))
        
        color_grid = QHBoxLayout()
        
        color_edit_layout = QVBoxLayout()
        color_buttons = {}
        
        if self.theme_manager.current_theme:
            colors = self.theme_manager.current_theme.colors
        else:
            colors = {
                'primary': '#4CAF50',
                'secondary': '#333333',
                'background': '#f0f0f0',
                'text': '#333333',
                'text_light': '#ffffff',
                'border': '#dddddd',
                'hover': '#45a049',
                'pressed': '#3d8b40'
            }
        
        for color_name, color_value in colors.items():
            color_row = QHBoxLayout()
            display_name = COLOR_NAME_MAP.get(color_name, color_name)
            color_row.addWidget(QLabel(display_name))
            color_button = QPushButton()
            color_button.setFixedWidth(40)
            color_button.setStyleSheet(f'background-color: {color_value}; border: 1px solid #ddd; border-radius: 3px;')
            color_button.clicked.connect(lambda checked, name=color_name, btn=color_button: self._change_theme_color_editor(name, btn))
            color_row.addWidget(color_button)
            color_edit_layout.addLayout(color_row)
            color_buttons[color_name] = color_button
        
        color_grid.addLayout(color_edit_layout)
        
        font_layout = QVBoxLayout()
        font_layout.addWidget(QLabel('字体设置:'))
        
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel('字体:'))
        font_family_combo = QFontComboBox()
        if self.theme_manager.current_theme:
            font_family_combo.setCurrentFont(QFont(self.theme_manager.current_theme.fonts['family']))
        font_family_layout.addWidget(font_family_combo)
        font_layout.addLayout(font_family_layout)
        
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel('字号:'))
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 24)
        if self.theme_manager.current_theme:
            font_size_spin.setValue(self.theme_manager.current_theme.fonts['size'])
        font_size_layout.addWidget(font_size_spin)
        font_layout.addLayout(font_size_layout)
        
        background_layout = QVBoxLayout()
        background_layout.addWidget(QLabel('背景图片:'))
        
        background_image_layout = QHBoxLayout()
        background_image_edit = QLineEdit()
        if self.theme_manager.current_theme:
            background_image_edit.setText(self.theme_manager.current_theme.background_image)
        background_image_layout.addWidget(background_image_edit)
        
        background_image_button = QPushButton('选择图片')
        background_image_button.clicked.connect(lambda: self._select_background_image_editor(background_image_edit))
        background_image_layout.addWidget(background_image_button)
        
        background_layout.addLayout(background_image_layout)
        font_layout.addLayout(background_layout)
        
        color_grid.addLayout(font_layout)
        color_group.addLayout(color_grid)
        main_layout.addLayout(color_group)
        
        preview_button = QPushButton('预览')
        preview_button.clicked.connect(lambda: self._preview_theme_editor(font_family_combo, font_size_spin, background_image_edit))
        main_layout.addWidget(preview_button)
        
        button_layout = QHBoxLayout()
        save_button = QPushButton('保存为新主题')
        save_button.clicked.connect(lambda: self._save_custom_theme_editor(theme_name_edit, theme_desc_edit, font_family_combo, font_size_spin, background_image_edit, dialog))
        cancel_button = QPushButton('取消')
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def _change_theme_color_editor(self, color_name, button):
        if self.theme_manager.current_theme:
            current_color = self.theme_manager.current_theme.colors.get(color_name, '#000000')
            display_name = COLOR_NAME_MAP.get(color_name, color_name)
            color = QColorDialog.getColor(QColor(current_color), self, f'选择{display_name}颜色')
            if color.isValid():
                button.setStyleSheet(f'background-color: {color.name()}; border: 1px solid #ddd; border-radius: 3px;')
                self.theme_manager.current_theme.colors[color_name] = color.name()
                self.apply_theme()
    
    def _select_background_image_editor(self, edit_widget):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择背景图片', '', '图片文件 (*.jpg *.jpeg *.png *.gif *.webp)')
        if file_path:
            edit_widget.setText(file_path)
    
    def _preview_theme_editor(self, font_combo, size_spin, image_edit):
        if self.theme_manager.current_theme:
            self.theme_manager.current_theme.fonts['family'] = font_combo.currentFont().family()
            self.theme_manager.current_theme.fonts['size'] = size_spin.value()
            self.theme_manager.current_theme.background_image = image_edit.text()
            self.apply_theme()
    
    def _save_custom_theme_editor(self, name_edit, desc_edit, font_combo, size_spin, image_edit, dialog):
        theme_name = name_edit.text().strip()
        if not theme_name:
            QMessageBox.warning(self, '警告', '请输入主题名称')
            return
        
        if self.theme_manager.current_theme:
            theme = self.theme_manager.create_theme_from_current(theme_name, desc_edit.text())
            theme.fonts['family'] = font_combo.currentFont().family()
            theme.fonts['size'] = size_spin.value()
            theme.background_image = image_edit.text()
            
            success = self.theme_manager.save_theme(theme)
            
            if success:
                QMessageBox.information(self, '成功', f'主题 "{theme_name}" 已保存')
                dialog.accept()
            else:
                QMessageBox.warning(self, '警告', '保存主题失败，请检查权限设置')
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.isMaximized():
            self.setWindowRadius(10)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.theme_manager.current_theme and self.theme_manager.current_theme.background_image:
            current_path = self.theme_manager.current_theme.background_image
            
            if self._background_path_cache != current_path or self._background_pixmap_cache is None:
                self._background_pixmap_cache = QPixmap(current_path)
                self._background_path_cache = current_path
            
            if not self._background_pixmap_cache.isNull():
                painter = QPainter(self)
                rect = self.rect()
                scaled_pixmap = self._background_pixmap_cache.scaled(
                    rect.size(), 
                    Qt.IgnoreAspectRatio, 
                    Qt.SmoothTransformation
                )
                painter.drawPixmap(rect, scaled_pixmap)
    
    def open_head_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Head设置')
        dialog.setGeometry(200, 200, 600, 450)
        
        main_layout = QVBoxLayout(dialog)
        
        title_layout = QHBoxLayout()
        title_label = QLabel('页面标题:')
        title_edit = QLineEdit()
        title_edit.setText(self.project.title)
        title_layout.addWidget(title_label)
        title_layout.addWidget(title_edit)
        main_layout.addLayout(title_layout)
        
        lang_layout = QHBoxLayout()
        lang_label = QLabel('语言:')
        lang_edit = QLineEdit()
        lang_edit.setText(self.project.head_config.get('lang', 'zh-CN'))
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(lang_edit)
        main_layout.addLayout(lang_layout)
        
        quick_add_group = QWidget()
        quick_add_layout = QVBoxLayout(quick_add_group)
        quick_add_label = QLabel('快捷添加:')
        quick_add_layout.addWidget(quick_add_label)
        
        quick_add_buttons = QHBoxLayout()
        favicon_button = QPushButton('添加网站图标')
        favicon_button.clicked.connect(lambda: self._add_favicon_editor())
        meta_desc_button = QPushButton('添加描述')
        meta_desc_button.clicked.connect(lambda: self._add_meta_description_editor())
        meta_keywords_button = QPushButton('添加关键词')
        meta_keywords_button.clicked.connect(lambda: self._add_meta_keywords_editor())
        quick_add_buttons.addWidget(favicon_button)
        quick_add_buttons.addWidget(meta_desc_button)
        quick_add_buttons.addWidget(meta_keywords_button)
        quick_add_layout.addLayout(quick_add_buttons)
        main_layout.addWidget(quick_add_group)
        
        meta_group = QWidget()
        meta_layout = QVBoxLayout(meta_group)
        meta_label = QLabel('Meta标签:')
        meta_layout.addWidget(meta_label)
        
        meta_list = QListWidget()
        for meta in self.project.head_config.get('meta_tags', []):
            item = QListWidgetItem(str(meta))
            item.setData(Qt.UserRole, meta)
            meta_list.addItem(item)
        meta_layout.addWidget(meta_list)
        
        meta_button_layout = QHBoxLayout()
        add_meta_button = QPushButton('添加')
        add_meta_button.clicked.connect(lambda: self._add_meta_tag_editor(meta_list))
        edit_meta_button = QPushButton('编辑')
        edit_meta_button.clicked.connect(lambda: self._edit_meta_tag_editor(meta_list))
        delete_meta_button = QPushButton('删除')
        delete_meta_button.clicked.connect(lambda: self._delete_meta_tag_editor(meta_list))
        meta_button_layout.addWidget(add_meta_button)
        meta_button_layout.addWidget(edit_meta_button)
        meta_button_layout.addWidget(delete_meta_button)
        meta_layout.addLayout(meta_button_layout)
        main_layout.addWidget(meta_group)
        
        link_group = QWidget()
        link_layout = QVBoxLayout(link_group)
        link_label = QLabel('Link标签:')
        link_layout.addWidget(link_label)
        
        link_list = QListWidget()
        for link in self.project.head_config.get('links', []):
            item = QListWidgetItem(str(link))
            item.setData(Qt.UserRole, link)
            link_list.addItem(item)
        link_layout.addWidget(link_list)
        
        link_button_layout = QHBoxLayout()
        add_link_button = QPushButton('添加')
        add_link_button.clicked.connect(lambda: self._add_link_tag_editor(link_list))
        edit_link_button = QPushButton('编辑')
        edit_link_button.clicked.connect(lambda: self._edit_link_tag_editor(link_list))
        delete_link_button = QPushButton('删除')
        delete_link_button.clicked.connect(lambda: self._delete_link_tag_editor(link_list))
        link_button_layout.addWidget(add_link_button)
        link_button_layout.addWidget(edit_link_button)
        link_button_layout.addWidget(delete_link_button)
        link_layout.addLayout(link_button_layout)
        main_layout.addWidget(link_group)
        
        script_group = QWidget()
        script_layout = QVBoxLayout(script_group)
        script_label = QLabel('Script标签:')
        script_layout.addWidget(script_label)
        
        script_list = QListWidget()
        for script in self.project.head_config.get('scripts', []):
            item = QListWidgetItem(str(script))
            item.setData(Qt.UserRole, script)
            script_list.addItem(item)
        script_layout.addWidget(script_list)
        
        script_button_layout = QHBoxLayout()
        add_script_button = QPushButton('添加')
        add_script_button.clicked.connect(lambda: self._add_script_tag_editor(script_list))
        edit_script_button = QPushButton('编辑')
        edit_script_button.clicked.connect(lambda: self._edit_script_tag_editor(script_list))
        delete_script_button = QPushButton('删除')
        delete_script_button.clicked.connect(lambda: self._delete_script_tag_editor(script_list))
        script_button_layout.addWidget(add_script_button)
        script_button_layout.addWidget(edit_script_button)
        script_button_layout.addWidget(delete_script_button)
        script_layout.addLayout(script_button_layout)
        main_layout.addWidget(script_group)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确定')
        ok_button.clicked.connect(lambda: self._save_head_settings_editor(title_edit, lang_edit, dialog))
        cancel_button = QPushButton('取消')
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def _add_meta_tag_editor(self, meta_list):
        name, ok1 = QInputDialog.getText(self, '添加Meta标签', '名称:')
        if ok1:
            content, ok2 = QInputDialog.getText(self, '添加Meta标签', '内容:')
            if ok2:
                meta = {'name': name, 'content': content}
                self.project.head_config.setdefault('meta_tags', []).append(meta)
                item = QListWidgetItem(str(meta))
                item.setData(Qt.UserRole, meta)
                meta_list.addItem(item)
    
    def _edit_meta_tag_editor(self, meta_list):
        current_item = meta_list.currentItem()
        if current_item:
            meta = current_item.data(Qt.UserRole)
            name, ok1 = QInputDialog.getText(self, '编辑Meta标签', '名称:', text=meta.get('name', ''))
            if ok1:
                content, ok2 = QInputDialog.getText(self, '编辑Meta标签', '内容:', text=meta.get('content', ''))
                if ok2:
                    meta['name'] = name
                    meta['content'] = content
                    current_item.setText(str(meta))
                    current_item.setData(Qt.UserRole, meta)
    
    def _delete_meta_tag_editor(self, meta_list):
        current_item = meta_list.currentItem()
        if current_item:
            meta = current_item.data(Qt.UserRole)
            self.project.head_config.setdefault('meta_tags', []).remove(meta)
            meta_list.takeItem(meta_list.row(current_item))
    
    def _add_link_tag_editor(self, link_list):
        rel, ok1 = QInputDialog.getText(self, '添加Link标签', 'rel:')
        if ok1:
            href, ok2 = QInputDialog.getText(self, '添加Link标签', 'href:')
            if ok2:
                link = {'rel': rel, 'href': href}
                self.project.head_config.setdefault('links', []).append(link)
                item = QListWidgetItem(str(link))
                item.setData(Qt.UserRole, link)
                link_list.addItem(item)
    
    def _edit_link_tag_editor(self, link_list):
        current_item = link_list.currentItem()
        if current_item:
            link = current_item.data(Qt.UserRole)
            rel, ok1 = QInputDialog.getText(self, '编辑Link标签', 'rel:', text=link.get('rel', ''))
            if ok1:
                href, ok2 = QInputDialog.getText(self, '编辑Link标签', 'href:', text=link.get('href', ''))
                if ok2:
                    link['rel'] = rel
                    link['href'] = href
                    current_item.setText(str(link))
                    current_item.setData(Qt.UserRole, link)
    
    def _delete_link_tag_editor(self, link_list):
        current_item = link_list.currentItem()
        if current_item:
            link = current_item.data(Qt.UserRole)
            self.project.head_config.setdefault('links', []).remove(link)
            link_list.takeItem(link_list.row(current_item))
    
    def _add_script_tag_editor(self, script_list):
        dialog = QDialog(self)
        dialog.setWindowTitle('添加Script标签')
        layout = QVBoxLayout(dialog)
        
        src_layout = QHBoxLayout()
        src_label = QLabel('src (留空为内联脚本):')
        src_edit = QLineEdit()
        src_layout.addWidget(src_label)
        src_layout.addWidget(src_edit)
        layout.addLayout(src_layout)
        
        content_label = QLabel('内容:')
        layout.addWidget(content_label)
        content_edit = QTextEdit()
        layout.addWidget(content_edit)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确定')
        cancel_button = QPushButton('取消')
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        def on_ok():
            script = {}
            src = src_edit.text().strip()
            if src:
                script['src'] = src
            else:
                script['content'] = content_edit.toPlainText()
            self.project.head_config.setdefault('scripts', []).append(script)
            item = QListWidgetItem(str(script))
            item.setData(Qt.UserRole, script)
            script_list.addItem(item)
            dialog.accept()
        
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec_()
    
    def _edit_script_tag_editor(self, script_list):
        current_item = script_list.currentItem()
        if current_item:
            script = current_item.data(Qt.UserRole)
            
            dialog = QDialog(self)
            dialog.setWindowTitle('编辑Script标签')
            layout = QVBoxLayout(dialog)
            
            src_layout = QHBoxLayout()
            src_label = QLabel('src (留空为内联脚本):')
            src_edit = QLineEdit()
            src_edit.setText(script.get('src', ''))
            src_layout.addWidget(src_label)
            src_layout.addWidget(src_edit)
            layout.addLayout(src_layout)
            
            content_label = QLabel('内容:')
            layout.addWidget(content_label)
            content_edit = QTextEdit()
            content_edit.setPlainText(script.get('content', ''))
            layout.addWidget(content_edit)
            
            button_layout = QHBoxLayout()
            ok_button = QPushButton('确定')
            cancel_button = QPushButton('取消')
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            def on_ok():
                src = src_edit.text().strip()
                if src:
                    script['src'] = src
                    if 'content' in script:
                        del script['content']
                else:
                    script['content'] = content_edit.toPlainText()
                    if 'src' in script:
                        del script['src']
                current_item.setText(str(script))
                current_item.setData(Qt.UserRole, script)
                dialog.accept()
            
            ok_button.clicked.connect(on_ok)
            cancel_button.clicked.connect(dialog.reject)
            
            dialog.exec_()
    
    def _delete_script_tag_editor(self, script_list):
        current_item = script_list.currentItem()
        if current_item:
            script = current_item.data(Qt.UserRole)
            self.project.head_config.setdefault('scripts', []).remove(script)
            script_list.takeItem(script_list.row(current_item))
    
    def _add_favicon_editor(self):
        favicon_url, ok = QInputDialog.getText(self, '添加网站图标', '请输入favicon图标URL:')
        if ok and favicon_url:
            existing_favicon = None
            for link in self.project.head_config.get('links', []):
                if link.get('rel') == 'icon':
                    existing_favicon = link
                    break
            
            if existing_favicon:
                existing_favicon['href'] = favicon_url
            else:
                favicon_link = {'rel': 'icon', 'href': favicon_url, 'type': 'image/x-icon'}
                self.project.head_config.setdefault('links', []).append(favicon_link)
    
    def _add_meta_description_editor(self):
        description, ok = QInputDialog.getText(self, '添加描述', '请输入页面描述:')
        if ok and description:
            existing_desc = None
            for meta in self.project.head_config.get('meta_tags', []):
                if meta.get('name') == 'description':
                    existing_desc = meta
                    break
            
            if existing_desc:
                existing_desc['content'] = description
            else:
                desc_meta = {'name': 'description', 'content': description}
                self.project.head_config.setdefault('meta_tags', []).append(desc_meta)
    
    def _add_meta_keywords_editor(self):
        keywords, ok = QInputDialog.getText(self, '添加关键词', '请输入页面关键词（用逗号分隔）:')
        if ok and keywords:
            existing_keywords = None
            for meta in self.project.head_config.get('meta_tags', []):
                if meta.get('name') == 'keywords':
                    existing_keywords = meta
                    break
            
            if existing_keywords:
                existing_keywords['content'] = keywords
            else:
                keywords_meta = {'name': 'keywords', 'content': keywords}
                self.project.head_config.setdefault('meta_tags', []).append(keywords_meta)
    
    def _save_head_settings_editor(self, title_edit, lang_edit, dialog):
        self.project.title = title_edit.text().strip()
        self.project.head_config['lang'] = lang_edit.text().strip()
        self.preview_server.update_html(self.project)
        self.statusBar.showMessage('Head设置已保存')
        dialog.accept()
    
    def open_ai_dialog(self):
        from gui.ai_dialog import AIDialogWidgetImpl
        
        dialog = QDialog(self)
        dialog.setWindowTitle('AI 助手')
        dialog.setGeometry(200, 200, 700, 600)
        
        layout = QVBoxLayout(dialog)
        
        ai_widget = AIDialogWidgetImpl(self.component_loader)
        
        def on_project_loaded(project):
            self.project = project
            self.refresh_page_components()
            self.clear_properties_panel()
            self.statusBar.showMessage(f'已加载项目: {self.project.name}')
            self.preview_timer.start(self.preview_delay)
            dialog.accept()
        
        ai_widget.project_loaded.connect(on_project_loaded)
        
        layout.addWidget(ai_widget)
        
        dialog.exec_()
    
    def open_ai_config(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('AI配置')
        dialog.setGeometry(300, 200, 500, 200)
        
        layout = QVBoxLayout(dialog)
        
        config_widget = AIApiConfigDialog()
        layout.addWidget(config_widget)
        
        dialog.exec_()
    
    def optimize_component_with_ai(self):
        current_item = self.page_components.currentItem()
        if not current_item:
            QMessageBox.warning(self, '提示', '请先选择一个组件')
            return
        
        index = current_item.data(Qt.UserRole)
        component = self.project.components[index]
        
        original_values = component.values.copy()
        
        dialog = QDialog(self)
        dialog.setWindowTitle('AI 优化组件')
        dialog.setGeometry(300, 200, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        component_label = QLabel(f'优化组件: {component.display_name}')
        component_label.setStyleSheet('font-weight: bold;')
        layout.addWidget(component_label)
        
        user_requirement_label = QLabel('优化需求:')
        layout.addWidget(user_requirement_label)
        
        user_requirement_edit = QTextEdit()
        user_requirement_edit.setPlaceholderText('请输入您的具体优化需求，例如：增加动画效果、调整颜色方案等...')
        user_requirement_edit.setMaximumHeight(150)
        layout.addWidget(user_requirement_edit)
        
        status_label = QLabel('状态: 准备就绪')
        layout.addWidget(status_label)
        
        button_layout = QHBoxLayout()
        
        optimize_button = QPushButton('开始优化')
        cancel_button = QPushButton('取消')
        
        button_layout.addWidget(optimize_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        class OptimizeThread(QThread):
            finished = pyqtSignal(dict)
            error = pyqtSignal(str)
            
            def __init__(self, ai_client, prompt):
                super().__init__()
                self.ai_client = ai_client
                self.prompt = prompt
            
            def run(self):
                try:
                    messages = [
                        {'role': 'system', 'content': '你是一个专业的网页组件优化助手，负责优化HTML组件的配置。'}, 
                        {'role': 'user', 'content': self.prompt}
                    ]
                    response = self.ai_client.chat(messages, temperature=0.7)
                    
                    response = response.strip()
                    if response.startswith('```json'):
                        response = response[7:]
                    if response.startswith('```'):
                        response = response[3:]
                    if response.endswith('```'):
                        response = response[:-3]
                    response = response.strip()
                    
                    data = json.loads(response)
                    self.finished.emit(data)
                except Exception as e:
                    self.error.emit(str(e))
        
        optimize_thread = None
        
        def start_optimize():
            nonlocal optimize_thread
            ai_client = AIClient()
            if not ai_client.api_key:
                QMessageBox.warning(self, '提示', '请先在AI助手的API配置中设置API Key')
                return
            
            prompt_text = f"请优化以下组件的配置，使其更加美观和实用：\n\n" \
                         f"组件类型: {component.display_name}\n" \
                         f"当前配置: {component.values}\n\n" \
                         f"请返回优化后的配置，只返回JSON格式，格式如下：\n" \
                         f"{{\"values\": {{...}}}}"
            
            user_requirement = user_requirement_edit.toPlainText().strip()
            
            combined_prompt = prompt_text
            if user_requirement:
                combined_prompt += f"\n\n用户额外需求: {user_requirement}"
            
            status_label.setText('状态: 优化中...')
            optimize_button.setEnabled(False)
            
            optimize_thread = OptimizeThread(ai_client, combined_prompt)
            
            def on_finished(data):
                nonlocal optimize_thread
                status_label.setText('状态: 优化完成')
                optimize_button.setEnabled(True)
                optimize_thread = None
                
                if 'values' in data:
                    component.values = data['values']
                    self.update_properties_panel(component)
                    
                    try:
                        url = self.preview_server.start(self.project)
                    except Exception:
                        pass
                    
                    self.preview_timer.start(self.preview_delay)
                    
                    reply = QMessageBox.question(
                        None, '优化完成', 
                        '组件优化完成，是否满意？\n在浏览器输入http://localhost:8765/或刷新预览界面看效果\n不满意可以选择"否"回退到原始状态。',
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.No:
                        component.values = original_values
                        self.update_properties_panel(component)
                        self.preview_timer.start(self.preview_delay)
                        QMessageBox.information(None, '已回退', '已回退到原始状态')
                else:
                    QMessageBox.warning(None, '错误', 'AI返回的格式不正确')
            
            def on_error(error_msg):
                nonlocal optimize_thread
                status_label.setText('状态: 优化失败')
                optimize_button.setEnabled(True)
                optimize_thread = None
                QMessageBox.warning(None, '错误', f'优化失败: {error_msg}')
            
            optimize_thread.finished.connect(on_finished)
            optimize_thread.error.connect(on_error)
            optimize_thread.start()
        
        def on_dialog_close():
            nonlocal optimize_thread
            if optimize_thread and optimize_thread.isRunning():
                optimize_thread.terminate()
                optimize_thread.wait()
        
        dialog.finished.connect(on_dialog_close)
        
        optimize_button.clicked.connect(start_optimize)
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec_()
    
    def closeEvent(self, event):
        if self.project.components and not self.project.file_path:
            reply = QMessageBox.question(
                self, 
                '未保存的内容', 
                '您有未保存的内容，确定要关闭吗？',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        self.auto_save_timer.stop()
        self.preview_server.stop()
        event.accept()
    
    def event(self, event):
        if event.type() == QEvent.User:
            if hasattr(event, 'message'):
                for widget in QApplication.topLevelWidgets():
                    if hasattr(widget, 'windowTitle') and widget.windowTitle() == '部署日志':
                        layout = widget.layout()
                        if layout:
                            for i in range(layout.count()):
                                item = layout.itemAt(i)
                                if item and item.widget() and isinstance(item.widget(), QTextEdit):
                                    item.widget().append(event.message)
                                    cursor = item.widget().textCursor()
                                    cursor.movePosition(cursor.End)
                                    item.widget().setTextCursor(cursor)
                        break
                return True
            elif hasattr(event, 'success') and hasattr(event, 'project_path'):
                if event.success:
                    self.statusBar.showMessage('部署成功!')
                    message = f'Cloudflare Worker已成功部署!\n\n项目目录: {event.project_path}'
                    if hasattr(event, 'deployed_url') and event.deployed_url:
                        message += f'\n\n部署地址: {event.deployed_url}'
                        webbrowser.open(event.deployed_url)
                    QMessageBox.information(None, '成功', message)
                else:
                    self.statusBar.showMessage('部署失败')
                    QMessageBox.warning(None, '部署失败', f'Cloudflare Worker项目已创建，但部署失败。\n\n项目目录: {event.project_path}\n\n请查看部署日志了解详情。')
                return True
        return super().event(event)


def run_gui():
    if not HAS_PYQT:
        print('Error: PyQt5 is required for GUI. Please install it with: pip install PyQt5')
        return
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())