import sys
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QListWidget, QListWidgetItem, QSplitter, QFileDialog, QMessageBox,
        QAction, QStatusBar, QLabel, QPushButton, QLineEdit, QComboBox, QColorDialog
    )
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QColor
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    print('Warning: PyQt5 not installed. GUI will not be available.')

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import Project, ComponentLoader, HTMLGenerator, PreviewServer
from utils import get_components_dir


class MainWindow(QMainWindow if HAS_PYQT else object):
    def __init__(self):
        if not HAS_PYQT:
            raise ImportError('PyQt5 is required for GUI')
        
        super().__init__()
        self.project = Project('Untitled')
        self.component_loader = ComponentLoader(str(get_components_dir()))
        self.component_loader.load_builtin_components()
        self.html_generator = HTMLGenerator()
        self.preview_server = PreviewServer(8765)
        
        # 自动保存设置
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_interval = 30000  # 30秒
        self.auto_save_timer.start(self.auto_save_interval)
        
        self.init_ui()
        self.refresh_component_library()
    
    def init_ui(self):
        self.setWindowTitle('pyHTML - 报纸组件化HTML生成器')
        self.setGeometry(100, 100, 1200, 800)
        
        self.create_menu_bar()
        self.create_central_widget()
        self.create_status_bar()
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu('文件(&F)')
        
        new_action = QAction('新建项目(&N)', self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction('打开项目(&O)', self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction('保存项目(&S)', self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('导出HTML(&E)', self)
        export_action.triggered.connect(self.export_html)
        file_menu.addAction(export_action)
        
        view_menu = menubar.addMenu('视图(&V)')
        
        preview_action = QAction('预览(&P)', self)
        preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(preview_action)
    
    def create_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = self.create_left_panel()
        middle_panel = self.create_middle_panel()
        right_panel = self.create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
    
    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        label = QLabel('组件库 (双击添加)')
        layout.addWidget(label)
        
        self.component_library = QListWidget()
        self.component_library.itemDoubleClicked.connect(self.add_component_from_library)
        layout.addWidget(self.component_library)
        
        return panel
    
    def create_middle_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        label = QLabel('页面组件')
        layout.addWidget(label)
        
        self.page_components = QListWidget()
        self.page_components.setSelectionMode(QListWidget.SingleSelection)
        self.page_components.currentItemChanged.connect(self.on_component_selected)
        layout.addWidget(self.page_components)
        
        button_layout = QHBoxLayout()
        
        remove_button = QPushButton('删除选中')
        remove_button.clicked.connect(self.remove_selected_component)
        button_layout.addWidget(remove_button)
        
        export_button = QPushButton('导出HTML')
        export_button.clicked.connect(self.export_html)
        button_layout.addWidget(export_button)
        
        preview_button = QPushButton('预览')
        preview_button.clicked.connect(self.toggle_preview)
        button_layout.addWidget(preview_button)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        label = QLabel('属性编辑')
        layout.addWidget(label)
        
        self.properties_panel = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_panel)
        layout.addWidget(self.properties_panel)
        
        self.clear_properties_panel()
        
        return panel
    
    def create_status_bar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage('就绪')
    
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
    
    def clear_properties_panel(self):
        # 清空属性面板中的所有控件
        while self.properties_layout.count() > 0:
            widget = self.properties_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # 添加提示信息
        placeholder = QLabel('请选择一个组件以编辑其属性')
        placeholder.setAlignment(Qt.AlignCenter)
        self.properties_layout.addWidget(placeholder)
    
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
    
    def update_properties_panel(self, component):
        # 清空属性面板
        self.clear_properties_panel()
        
        # 添加组件名称
        component_label = QLabel(f'组件: {component.display_name}')
        self.properties_layout.addWidget(component_label)
        
        # 为每个字段创建编辑控件
        for field in component.fields:
            field_name = field['name']
            field_type = field['type']
            field_label = field['label']
            field_value = component.get_value(field_name)
            
            # 创建字段标签
            label = QLabel(field_label)
            self.properties_layout.addWidget(label)
            
            # 根据字段类型创建不同的编辑控件
            if field_type == 'string':
                # 字符串类型 - 使用 QLineEdit
                line_edit = QLineEdit()
                line_edit.setText(str(field_value))
                line_edit.textChanged.connect(lambda text, fn=field_name, c=component: c.set_value(fn, text))
                self.properties_layout.addWidget(line_edit)
            
            elif field_type == 'select':
                # 选择类型 - 使用 QComboBox
                combo_box = QComboBox()
                # 添加选项
                for option in field['options']:
                    combo_box.addItem(option['label'], option['value'])
                # 设置当前值
                index = combo_box.findData(field_value)
                if index >= 0:
                    combo_box.setCurrentIndex(index)
                # 连接信号
                combo_box.currentIndexChanged.connect(lambda index, cb=combo_box, fn=field_name, c=component: 
                    c.set_value(fn, cb.itemData(index)))
                self.properties_layout.addWidget(combo_box)
            
            elif field_type == 'color':
                # 颜色类型 - 使用 QPushButton + QColorDialog
                color_button = QPushButton()
                color_button.setStyleSheet(f'background-color: {field_value};')
                color_button.clicked.connect(lambda fn=field_name, c=component, btn=color_button: 
                    self.open_color_dialog(fn, c, btn))
                self.properties_layout.addWidget(color_button)
        
        # 添加一个垂直伸缩器，使控件顶部对齐
        self.properties_layout.addStretch(1)
    
    def export_html(self):
        file_path, _ = QFileDialog.getSaveFileName(self, '导出HTML', '', 'HTML File (*.html)')
        if file_path:
            try:
                self.html_generator.save_html(self.project.components, file_path, self.project.title)
                self.statusBar.showMessage(f'已导出: {file_path}')
                QMessageBox.information(self, '成功', f'HTML已导出到: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法导出HTML: {str(e)}')
    
    def toggle_preview(self):
        try:
            url = self.preview_server.start(self.project)
            self.preview_server.open_browser()
            self.statusBar.showMessage(f'预览已打开: {url}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法启动预览: {str(e)}')
    
    def open_color_dialog(self, field_name, component, button):
        # 打开颜色选择对话框
        color = QColorDialog.getColor(QColor(component.get_value(field_name)), self, '选择颜色')
        if color.isValid():
            # 更新组件的颜色值
            component.set_value(field_name, color.name())
            # 更新按钮的背景色
            button.setStyleSheet(f'background-color: {color.name()};')
    
    def new_project(self):
        # 新建项目
        self.project = Project('Untitled')
        self.refresh_page_components()
        self.clear_properties_panel()
        self.statusBar.showMessage('已创建新项目')
    
    def open_project(self):
        # 打开项目
        file_path, _ = QFileDialog.getOpenFileName(self, '打开项目', '', 'pyHTML项目文件 (*.pyhtml)')
        if file_path:
            try:
                self.project = Project.load(file_path)
                self.refresh_page_components()
                self.clear_properties_panel()
                self.statusBar.showMessage(f'已打开项目: {self.project.name}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法打开项目: {str(e)}')
    
    def save_project(self):
        # 保存项目
        if not self.project.file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, '保存项目', '', 'pyHTML项目文件 (*.pyhtml)')
            if not file_path:
                return
        else:
            file_path = self.project.file_path
        
        try:
            self.project.save(file_path)
            self.statusBar.showMessage(f'已保存项目: {self.project.name}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法保存项目: {str(e)}')
    
    def auto_save(self):
        # 自动保存项目
        if self.project.file_path:
            try:
                self.project.save()
                self.statusBar.showMessage(f'自动保存: {self.project.name}')
            except Exception:
                pass
    
    def closeEvent(self, event):
        # 停止自动保存定时器
        self.auto_save_timer.stop()
        # 停止预览服务器
        self.preview_server.stop()
        event.accept()


def run_gui():
    if not HAS_PYQT:
        print('Error: PyQt5 is required for GUI. Please install it with: pip install PyQt5')
        return
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
