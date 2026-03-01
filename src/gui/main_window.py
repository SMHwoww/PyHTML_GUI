import sys
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QListWidget, QListWidgetItem, QSplitter, QFileDialog, QMessageBox,
        QAction, QStatusBar, QLabel, QPushButton, QLineEdit, QComboBox, QColorDialog,
        QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit, QFontComboBox
    )
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QColor, QFont
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
        
        # 预览更新防抖定时器
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_delay = 300  # 300毫秒延迟
        
        self.init_ui()
        self.refresh_component_library()
    
    def init_ui(self):
        # 设置窗口标志，去除默认标题栏
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置窗口图标
        from PyQt5.QtGui import QIcon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'asset', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 设置样式
        self.setStyleSheet('''
            QMainWindow {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
            }
            QWidget {
                font-family: Microsoft YaHei;
                font-size: 12px;
            }
            QLabel {
                font-weight: bold;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border-color: #4CAF50;
                outline: none;
            }
            QMenuBar {
                background-color: #333;
                color: white;
            }
            QMenuBar::item {
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
            }
            QMenu {
                background-color: #333;
                color: white;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
            QStatusBar {
                background-color: #f0f0f0;
                border-top: 1px solid #ddd;
            }
            .CustomTitleBar {
                background-color: #333;
                color: white;
                height: 30px;
            }
            .TitleLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
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
        
        self.create_custom_title_bar()
        self.create_menu_bar()
        self.create_central_widget()
        self.create_status_bar()
    
    def create_custom_title_bar(self):
        # 创建自定义标题栏
        title_bar = QWidget()
        title_bar.setObjectName('CustomTitleBar')
        title_bar.setStyleSheet('''
            .CustomTitleBar {
                background-color: #333;
                color: white;
                height: 30px;
            }
        ''')
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(0)
        
        # 左侧：图标和标题
        left_layout = QHBoxLayout()
        left_layout.setContentsMargins(5, 0, 5, 0)
        left_layout.setSpacing(10)
        
        # 应用图标
        from PyQt5.QtGui import QIcon
        import os
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'asset', 'icon.png')
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            pixmap = icon.pixmap(20, 20)
            icon_label.setPixmap(pixmap)
        else:
            # 默认图标
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
                    text-align: center;
                }
            ''')
        left_layout.addWidget(icon_label)
        
        # 标题标签
        title_label = QLabel('pyHTML - 报纸组件化HTML生成器')
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
        
        # 占位符，使按钮靠右
        title_layout.addStretch(1)
        
        # 右侧：窗口控制按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        
        # 最小化按钮
        min_button = QPushButton('−')
        min_button.setObjectName('TitleButton')
        min_button.setStyleSheet('''
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
        min_button.clicked.connect(self.showMinimized)
        button_layout.addWidget(min_button)
        
        # 最大化/还原按钮
        self.max_button = QPushButton('□')
        self.max_button.setObjectName('TitleButton')
        self.max_button.setStyleSheet('''
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
        self.max_button.clicked.connect(self.toggle_maximize)
        button_layout.addWidget(self.max_button)
        
        # 关闭按钮
        close_button = QPushButton('×')
        close_button.setObjectName('TitleButton')
        close_button.setStyleSheet('''
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
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        title_layout.addLayout(button_layout)
        
        # 设置标题栏高度
        title_bar.setFixedHeight(30)
        
        # 添加到主窗口
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        main_layout.addWidget(title_bar)
        
        # 保存原始的中心部件布局
        central_widget = self.centralWidget()
        if central_widget:
            main_layout.addWidget(central_widget)
        
        self.setCentralWidget(main_widget)
        
        # 窗口拖动功能
        self.drag_position = None
        title_bar.mousePressEvent = self.title_bar_mouse_press_event
        title_bar.mouseMoveEvent = self.title_bar_mouse_move_event
    
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
        else:
            self.showMaximized()
            self.max_button.setText('▢')
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 调整菜单栏样式
        menubar.setStyleSheet('''
            QMenuBar {
                background-color: #333;
                color: white;
                padding: 2px 0;
            }
            QMenuBar::item {
                color: white;
                padding: 4px 10px;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
            }
        ''')
        
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
        
        import_component_action = QAction('导入组件(&I)', self)
        import_component_action.triggered.connect(self.import_component)
        file_menu.addAction(import_component_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('导出HTML(&E)', self)
        export_action.triggered.connect(self.export_html)
        file_menu.addAction(export_action)
        
        export_worker_action = QAction('导出为Cloudflare Worker(&W)', self)
        export_worker_action.triggered.connect(self.export_cloudflare_worker)
        file_menu.addAction(export_worker_action)
        
        view_menu = menubar.addMenu('视图(&V)')
        
        preview_action = QAction('预览(&P)', self)
        preview_action.triggered.connect(self.toggle_preview)
        view_menu.addAction(preview_action)
        
        # 添加设置菜单
        settings_menu = menubar.addMenu('设置(&S)')
        
        head_settings_action = QAction('Head设置(&H)', self)
        head_settings_action.triggered.connect(self.open_head_settings)
        settings_menu.addAction(head_settings_action)
    
    def create_central_widget(self):
        # 创建中心部件内容
        content_widget = QWidget()
        main_layout = QHBoxLayout(content_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = self.create_left_panel()
        middle_panel = self.create_middle_panel()
        right_panel = self.create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        # 设置初始宽度
        total_width = self.width()
        splitter.setSizes([int(total_width * 0.2), int(total_width * 0.3), int(total_width * 0.5)])
        
        # 允许用户通过拖拽调整宽度
        splitter.setOpaqueResize(True)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(splitter)
        
        # 获取当前的中心部件（包含标题栏）
        current_central = self.centralWidget()
        if current_central:
            # 找到垂直布局
            layout = current_central.layout()
            if layout:
                # 添加内容部件
                layout.addWidget(content_widget)
        else:
            # 如果没有中心部件，直接设置
            self.setCentralWidget(content_widget)
    
    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        label = QLabel('组件库 (双击添加)')
        layout.addWidget(label)
        
        self.component_library = QListWidget()
        self.component_library.setDragEnabled(True)
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
        self.page_components.setAcceptDrops(True)
        self.page_components.setDragDropMode(QListWidget.DragDrop)
        self.page_components.currentItemChanged.connect(self.on_component_selected)
        # 重写拖拽事件
        self.page_components.dragEnterEvent = self.drag_enter_event
        self.page_components.dropEvent = self.drop_event
        layout.addWidget(self.page_components)
        
        button_layout = QHBoxLayout()
        
        remove_button = QPushButton('删除选中')
        remove_button.clicked.connect(self.remove_selected_component)
        button_layout.addWidget(remove_button)
        
        # 添加组件层级调整按钮
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
    
    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        label = QLabel('属性编辑')
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(label)
        
        self.properties_panel = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_panel)
        self.properties_layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.properties_panel)
        
        # 添加一个垂直伸缩器，使标签和内容都顶部对齐
        layout.addStretch(1)
        
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
    
    def clear_layout_recursive(self, layout):
        # 递归清理布局及其子控件
        if layout is None:
            return
        
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item is None:
                continue
            
            # 先处理子布局
            child_layout = item.layout()
            if child_layout:
                self.clear_layout_recursive(child_layout)
            
            # 再处理widget
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def clear_properties_panel(self):
        # 清空属性面板中的所有控件
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
                # 交换组件位置
                self.project.components[index], self.project.components[index-1] = self.project.components[index-1], self.project.components[index]
                self.refresh_page_components()
                # 重新选择移动后的组件
                self.page_components.setCurrentRow(index-1)
                self.statusBar.showMessage('组件已上移')
                # 更新预览
                self.preview_timer.start(self.preview_delay)
    
    def move_component_down(self):
        current_item = self.page_components.currentItem()
        if current_item:
            index = current_item.data(Qt.UserRole)
            if index < len(self.project.components) - 1:
                # 交换组件位置
                self.project.components[index], self.project.components[index+1] = self.project.components[index+1], self.project.components[index]
                self.refresh_page_components()
                # 重新选择移动后的组件
                self.page_components.setCurrentRow(index+1)
                self.statusBar.showMessage('组件已下移')
                # 更新预览
                self.preview_timer.start(self.preview_delay)
    
    def drag_enter_event(self, event):
        # 检查拖拽源是否是组件库
        if event.source() == self.component_library:
            event.accept()
        elif event.source() == self.page_components:
            event.accept()
        else:
            event.ignore()
    
    def drop_event(self, event):
        # 从组件库拖拽到页面组件列表
        if event.source() == self.component_library:
            item = event.source().currentItem()
            if item:
                component_name = item.data(Qt.UserRole)
                component = self.component_loader.create_instance(component_name)
                if component:
                    # 确定插入位置
                    drop_pos = self.page_components.dropIndicatorPosition()
                    if drop_pos == QListWidget.OnItem or drop_pos == QListWidget.OnItemButtom:
                        # 插入到选中项目之后
                        current_item = self.page_components.itemAt(event.pos())
                        if current_item:
                            index = current_item.data(Qt.UserRole) + 1
                            self.project.components.insert(index, component)
                        else:
                            self.project.add_component(component)
                    else:
                        # 添加到末尾
                        self.project.add_component(component)
                    self.refresh_page_components()
                    self.statusBar.showMessage(f'已添加组件: {component.display_name}')
                    # 更新预览
                    self.preview_timer.start(self.preview_delay)
        # 在页面组件列表内部拖拽调整顺序
        elif event.source() == self.page_components:
            source_item = event.source().currentItem()
            if source_item:
                source_index = source_item.data(Qt.UserRole)
                # 确定目标位置
                target_item = self.page_components.itemAt(event.pos())
                if target_item:
                    target_index = target_item.data(Qt.UserRole)
                    # 移除源组件
                    component = self.project.components.pop(source_index)
                    # 插入到目标位置
                    if source_index < target_index:
                        self.project.components.insert(target_index, component)
                    else:
                        self.project.components.insert(target_index, component)
                    self.refresh_page_components()
                    # 重新选择移动后的组件
                    new_index = target_index if source_index > target_index else target_index - 1
                    self.page_components.setCurrentRow(new_index)
                    self.statusBar.showMessage('组件位置已调整')
                    # 更新预览
                    self.preview_timer.start(self.preview_delay)
    
    def update_properties_panel(self, component):
        # 清空属性面板
        self.clear_properties_panel()
        
        # 添加组件名称
        component_label = QLabel(f'组件: {component.display_name}')
        component_label.setStyleSheet('font-size: 14px; font-weight: bold; margin-bottom: 10px;')
        self.properties_layout.addWidget(component_label)
        
        # 为每个字段创建编辑控件
        for field in component.fields:
            field_name = field['name']
            field_type = field['type']
            field_label = field['label']
            field_value = component.get_value(field_name)
            
            # 创建字段容器
            field_container = QWidget()
            field_layout = QVBoxLayout(field_container)
            field_layout.setContentsMargins(0, 0, 0, 10)
            
            # 创建字段标签（除了boolean类型，因为boolean类型的标签在checkbox中）
            if field_type != 'boolean':
                label = QLabel(field_label)
                label.setStyleSheet('font-size: 12px; font-weight: normal; color: #555; margin-bottom: 4px;')
                field_layout.addWidget(label)
            
            # 根据字段类型创建不同的编辑控件
            if field_type == 'string':
                # 字符串类型 - 使用 QLineEdit
                line_edit = QLineEdit()
                line_edit.setText(str(field_value) if field_value is not None else '')
                line_edit.setPlaceholderText(field.get('placeholder', ''))
                line_edit.textChanged.connect(lambda text, fn=field_name, c=component: 
                    (c.set_value(fn, text), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(line_edit)
            
            elif field_type == 'number':
                # 数字类型 - 使用 QSpinBox 或 QDoubleSpinBox
                step = field.get('step', 1)
                if isinstance(step, float) or isinstance(field.get('default'), float):
                    # 使用浮点数输入框
                    spin_box = QDoubleSpinBox()
                    spin_box.setDecimals(2)
                else:
                    # 使用整数输入框
                    spin_box = QSpinBox()
                
                # 设置最小值、最大值和步长
                if 'min' in field:
                    spin_box.setMinimum(field['min'])
                if 'max' in field:
                    spin_box.setMaximum(field['max'])
                spin_box.setSingleStep(step)
                
                # 设置当前值
                if field_value is not None:
                    spin_box.setValue(field_value)
                
                # 连接信号
                spin_box.valueChanged.connect(lambda value, fn=field_name, c=component: 
                    (c.set_value(fn, value), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(spin_box)
            
            elif field_type == 'boolean':
                # 布尔类型 - 使用 QCheckBox
                check_box = QCheckBox(field_label)
                check_box.setChecked(bool(field_value))
                check_box.stateChanged.connect(lambda state, fn=field_name, c=component: 
                    (c.set_value(fn, state == Qt.Checked), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(check_box)
            
            elif field_type == 'textarea':
                # 多行文本类型 - 使用 QTextEdit
                text_edit = QTextEdit()
                text_edit.setPlainText(str(field_value) if field_value is not None else '')
                text_edit.setPlaceholderText(field.get('placeholder', ''))
                # 设置行数（如果有）
                if 'rows' in field:
                    text_edit.setMaximumHeight(field['rows'] * 20)
                else:
                    text_edit.setMaximumHeight(100)
                text_edit.textChanged.connect(lambda fn=field_name, c=component, te=text_edit: 
                    (c.set_value(fn, te.toPlainText()), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(text_edit)
            
            elif field_type == 'font':
                # 字体类型 - 使用 QFontComboBox + QSpinBox
                font_layout = QHBoxLayout()
                font_layout.setSpacing(5)
                
                # 字体选择
                font_combo = QFontComboBox()
                font_combo.setMinimumWidth(150)
                default_font = field.get('default', 'Arial')
                font_combo.setCurrentFont(QFont(default_font))
                font_combo.currentFontChanged.connect(lambda font, fn=field_name, c=component: 
                    (c.set_value(fn, font.family()), self.preview_timer.start(self.preview_delay)))
                font_layout.addWidget(font_combo)
                
                # 字号选择
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
                    (c.set_value(fn, cb.itemData(index)), self.preview_timer.start(self.preview_delay)))
                field_layout.addWidget(combo_box)
            
            elif field_type == 'color':
                # 颜色类型 - 使用 QPushButton + QColorDialog
                color_layout = QHBoxLayout()
                color_layout.setSpacing(5)
                
                color_label = QLabel(field_value)
                color_label.setFixedWidth(80)
                color_label.setStyleSheet('border: 1px solid #ddd; padding: 2px 5px; border-radius: 3px;')
                
                color_button = QPushButton()
                color_button.setFixedWidth(40)
                color_button.setStyleSheet(f'background-color: {field_value}; border: 1px solid #ddd; border-radius: 3px;')
                # 使用默认参数来捕获变量值，避免闭包中的变量绑定问题
                color_button.clicked.connect(lambda checked, fn=field_name, c=component, btn=color_button, lbl=color_label: 
                    (self.open_color_dialog(fn, c, btn), lbl.setText(c.get_value(fn)), self.preview_timer.start(self.preview_delay)))
                
                color_layout.addWidget(color_label)
                color_layout.addWidget(color_button)
                field_layout.addLayout(color_layout)
            
            self.properties_layout.addWidget(field_container)
        
        # 添加一个垂直伸缩器，使控件顶部对齐
        self.properties_layout.addStretch(1)
    
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
        file_path, _ = QFileDialog.getSaveFileName(self, '导出为Cloudflare Worker', '', 'JavaScript File (*.js)')
        if file_path:
            try:
                self.html_generator.save_cloudflare_worker(self.project.components, file_path, self.project.title, self.project.head_config)
                self.statusBar.showMessage(f'已导出: {file_path}')
                QMessageBox.information(self, '成功', f'Cloudflare Worker已导出到: {file_path}\n\n使用方法:\n1. 登录Cloudflare控制台\n2. 进入Workers & Pages\n3. 创建新的Worker\n4. 粘贴生成的代码\n5. 部署并测试')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法导出Cloudflare Worker: {str(e)}')
    
    def toggle_preview(self):
        try:
            url = self.preview_server.start(self.project)
            self.preview_server.open_browser()
            self.statusBar.showMessage(f'预览已打开: {url}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法启动预览: {str(e)}')
    
    def open_color_dialog(self, field_name, component, button):
        # 打开颜色选择对话框
        current_color = component.get_value(field_name)
        # 确保current_color是有效的颜色值
        if not current_color:
            current_color = '#000000'  # 默认黑色
        
        color = QColorDialog.getColor(QColor(current_color), self, '选择颜色')
        if color.isValid():
            # 更新组件的颜色值
            component.set_value(field_name, color.name())
            # 更新按钮的背景色
            button.setStyleSheet(f'background-color: {color.name()};')
            # 预览更新由防抖定时器处理
    
    def import_component(self):
        # 导入组件
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter('压缩包 (*.zip *.rar *.7z *.tar *.tar.gz)')
        
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                try:
                    import tempfile
                    from zipfile import ZipFile
                    
                    path = selected_files[0]
                    # 处理压缩包导入
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # 解压压缩包
                        try:
                            with ZipFile(path, 'r') as zip_ref:
                                zip_ref.extractall(temp_dir)
                        except Exception as e:
                            QMessageBox.critical(self, '错误', f'无法解压压缩包: {str(e)}')
                            return
                        
                        # 从临时目录导入组件
                        component_dir = Path(temp_dir)
                        if (component_dir / 'config.json').exists():
                            # 单个组件
                            component = self.component_loader.load_component(str(component_dir))
                            if component:
                                self.refresh_component_library()
                                self.statusBar.showMessage(f'已导入组件: {component.display_name}')
                                QMessageBox.information(self, '成功', f'已导入组件: {component.display_name}')
                        else:
                            # 检查是否包含多个组件子目录
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
    
    def update_preview(self):
        # 实际更新预览
        self.preview_server.update_html(self.project)
        self.statusBar.showMessage('预览已更新')
    
    def open_head_settings(self):
        # 创建Head设置对话框
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QInputDialog, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Head设置')
        dialog.setGeometry(200, 200, 600, 450)
        
        main_layout = QVBoxLayout(dialog)
        
        # 标题设置
        title_layout = QHBoxLayout()
        title_label = QLabel('页面标题:')
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.project.title)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        main_layout.addLayout(title_layout)
        
        # 语言设置
        lang_layout = QHBoxLayout()
        lang_label = QLabel('语言:')
        self.lang_edit = QLineEdit()
        self.lang_edit.setText(self.project.head_config.get('lang', 'zh-CN'))
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_edit)
        main_layout.addLayout(lang_layout)
        
        # 快捷添加区域
        quick_add_group = QWidget()
        quick_add_layout = QVBoxLayout(quick_add_group)
        quick_add_label = QLabel('快捷添加:')
        quick_add_layout.addWidget(quick_add_label)
        
        quick_add_buttons = QHBoxLayout()
        favicon_button = QPushButton('添加网站图标')
        favicon_button.clicked.connect(lambda: self.add_favicon())
        meta_desc_button = QPushButton('添加描述')
        meta_desc_button.clicked.connect(lambda: self.add_meta_description())
        meta_keywords_button = QPushButton('添加关键词')
        meta_keywords_button.clicked.connect(lambda: self.add_meta_keywords())
        quick_add_buttons.addWidget(favicon_button)
        quick_add_buttons.addWidget(meta_desc_button)
        quick_add_buttons.addWidget(meta_keywords_button)
        quick_add_layout.addLayout(quick_add_buttons)
        main_layout.addWidget(quick_add_group)
        
        # Meta标签设置
        meta_group = QWidget()
        meta_layout = QVBoxLayout(meta_group)
        meta_label = QLabel('Meta标签:')
        meta_layout.addWidget(meta_label)
        
        self.meta_list = QListWidget()
        for meta in self.project.head_config.get('meta_tags', []):
            item = QListWidgetItem(str(meta))
            item.setData(Qt.UserRole, meta)
            self.meta_list.addItem(item)
        meta_layout.addWidget(self.meta_list)
        
        meta_button_layout = QHBoxLayout()
        add_meta_button = QPushButton('添加')
        add_meta_button.clicked.connect(lambda: self.add_meta_tag())
        edit_meta_button = QPushButton('编辑')
        edit_meta_button.clicked.connect(lambda: self.edit_meta_tag())
        delete_meta_button = QPushButton('删除')
        delete_meta_button.clicked.connect(lambda: self.delete_meta_tag())
        meta_button_layout.addWidget(add_meta_button)
        meta_button_layout.addWidget(edit_meta_button)
        meta_button_layout.addWidget(delete_meta_button)
        meta_layout.addLayout(meta_button_layout)
        main_layout.addWidget(meta_group)
        
        # Link标签设置
        link_group = QWidget()
        link_layout = QVBoxLayout(link_group)
        link_label = QLabel('Link标签:')
        link_layout.addWidget(link_label)
        
        self.link_list = QListWidget()
        for link in self.project.head_config.get('links', []):
            item = QListWidgetItem(str(link))
            item.setData(Qt.UserRole, link)
            self.link_list.addItem(item)
        link_layout.addWidget(self.link_list)
        
        link_button_layout = QHBoxLayout()
        add_link_button = QPushButton('添加')
        add_link_button.clicked.connect(lambda: self.add_link_tag())
        edit_link_button = QPushButton('编辑')
        edit_link_button.clicked.connect(lambda: self.edit_link_tag())
        delete_link_button = QPushButton('删除')
        delete_link_button.clicked.connect(lambda: self.delete_link_tag())
        link_button_layout.addWidget(add_link_button)
        link_button_layout.addWidget(edit_link_button)
        link_button_layout.addWidget(delete_link_button)
        link_layout.addLayout(link_button_layout)
        main_layout.addWidget(link_group)
        
        # Script标签设置
        script_group = QWidget()
        script_layout = QVBoxLayout(script_group)
        script_label = QLabel('Script标签:')
        script_layout.addWidget(script_label)
        
        self.script_list = QListWidget()
        for script in self.project.head_config.get('scripts', []):
            item = QListWidgetItem(str(script))
            item.setData(Qt.UserRole, script)
            self.script_list.addItem(item)
        script_layout.addWidget(self.script_list)
        
        script_button_layout = QHBoxLayout()
        add_script_button = QPushButton('添加')
        add_script_button.clicked.connect(lambda: self.add_script_tag())
        edit_script_button = QPushButton('编辑')
        edit_script_button.clicked.connect(lambda: self.edit_script_tag())
        delete_script_button = QPushButton('删除')
        delete_script_button.clicked.connect(lambda: self.delete_script_tag())
        script_button_layout.addWidget(add_script_button)
        script_button_layout.addWidget(edit_script_button)
        script_button_layout.addWidget(delete_script_button)
        script_layout.addLayout(script_button_layout)
        main_layout.addWidget(script_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton('确定')
        ok_button.clicked.connect(lambda: self.save_head_settings(dialog))
        cancel_button = QPushButton('取消')
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def add_meta_tag(self):
        from PyQt5.QtWidgets import QInputDialog
        name, ok1 = QInputDialog.getText(self, '添加Meta标签', '名称:')
        if ok1:
            content, ok2 = QInputDialog.getText(self, '添加Meta标签', '内容:')
            if ok2:
                meta = {'name': name, 'content': content}
                self.project.head_config.setdefault('meta_tags', []).append(meta)
                item = QListWidgetItem(str(meta))
                item.setData(Qt.UserRole, meta)
                self.meta_list.addItem(item)
    
    def edit_meta_tag(self):
        from PyQt5.QtWidgets import QInputDialog
        current_item = self.meta_list.currentItem()
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
    
    def delete_meta_tag(self):
        current_item = self.meta_list.currentItem()
        if current_item:
            meta = current_item.data(Qt.UserRole)
            self.project.head_config.setdefault('meta_tags', []).remove(meta)
            self.meta_list.takeItem(self.meta_list.row(current_item))
    
    def add_link_tag(self):
        from PyQt5.QtWidgets import QInputDialog
        rel, ok1 = QInputDialog.getText(self, '添加Link标签', 'rel:')
        if ok1:
            href, ok2 = QInputDialog.getText(self, '添加Link标签', 'href:')
            if ok2:
                link = {'rel': rel, 'href': href}
                self.project.head_config.setdefault('links', []).append(link)
                item = QListWidgetItem(str(link))
                item.setData(Qt.UserRole, link)
                self.link_list.addItem(item)
    
    def edit_link_tag(self):
        from PyQt5.QtWidgets import QInputDialog
        current_item = self.link_list.currentItem()
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
    
    def delete_link_tag(self):
        current_item = self.link_list.currentItem()
        if current_item:
            link = current_item.data(Qt.UserRole)
            self.project.head_config.setdefault('links', []).remove(link)
            self.link_list.takeItem(self.link_list.row(current_item))
    
    def add_script_tag(self):
        from PyQt5.QtWidgets import QInputDialog, QTextEdit, QDialog, QVBoxLayout, QHBoxLayout, QPushButton
        
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
            self.script_list.addItem(item)
            dialog.accept()
        
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec_()
    
    def edit_script_tag(self):
        from PyQt5.QtWidgets import QInputDialog, QTextEdit, QDialog, QVBoxLayout, QHBoxLayout, QPushButton
        
        current_item = self.script_list.currentItem()
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
    
    def delete_script_tag(self):
        current_item = self.script_list.currentItem()
        if current_item:
            script = current_item.data(Qt.UserRole)
            self.project.head_config.setdefault('scripts', []).remove(script)
            self.script_list.takeItem(self.script_list.row(current_item))
    
    def add_favicon(self):
        from PyQt5.QtWidgets import QInputDialog
        favicon_url, ok = QInputDialog.getText(self, '添加网站图标', '请输入favicon图标URL:')
        if ok and favicon_url:
            # 检查是否已存在favicon链接
            existing_favicon = None
            for link in self.project.head_config.get('links', []):
                if link.get('rel') == 'icon':
                    existing_favicon = link
                    break
            
            if existing_favicon:
                existing_favicon['href'] = favicon_url
                # 更新列表显示
                for i in range(self.link_list.count()):
                    item = self.link_list.item(i)
                    if item.data(Qt.UserRole) == existing_favicon:
                        item.setText(str(existing_favicon))
                        break
            else:
                # 添加新的favicon链接
                favicon_link = {'rel': 'icon', 'href': favicon_url, 'type': 'image/x-icon'}
                self.project.head_config.setdefault('links', []).append(favicon_link)
                item = QListWidgetItem(str(favicon_link))
                item.setData(Qt.UserRole, favicon_link)
                self.link_list.addItem(item)
    
    def add_meta_description(self):
        from PyQt5.QtWidgets import QInputDialog
        description, ok = QInputDialog.getText(self, '添加描述', '请输入页面描述:')
        if ok and description:
            # 检查是否已存在description meta标签
            existing_desc = None
            for meta in self.project.head_config.get('meta_tags', []):
                if meta.get('name') == 'description':
                    existing_desc = meta
                    break
            
            if existing_desc:
                existing_desc['content'] = description
                # 更新列表显示
                for i in range(self.meta_list.count()):
                    item = self.meta_list.item(i)
                    if item.data(Qt.UserRole) == existing_desc:
                        item.setText(str(existing_desc))
                        break
            else:
                # 添加新的description meta标签
                desc_meta = {'name': 'description', 'content': description}
                self.project.head_config.setdefault('meta_tags', []).append(desc_meta)
                item = QListWidgetItem(str(desc_meta))
                item.setData(Qt.UserRole, desc_meta)
                self.meta_list.addItem(item)
    
    def add_meta_keywords(self):
        from PyQt5.QtWidgets import QInputDialog
        keywords, ok = QInputDialog.getText(self, '添加关键词', '请输入页面关键词（用逗号分隔）:')
        if ok and keywords:
            # 检查是否已存在keywords meta标签
            existing_keywords = None
            for meta in self.project.head_config.get('meta_tags', []):
                if meta.get('name') == 'keywords':
                    existing_keywords = meta
                    break
            
            if existing_keywords:
                existing_keywords['content'] = keywords
                # 更新列表显示
                for i in range(self.meta_list.count()):
                    item = self.meta_list.item(i)
                    if item.data(Qt.UserRole) == existing_keywords:
                        item.setText(str(existing_keywords))
                        break
            else:
                # 添加新的keywords meta标签
                keywords_meta = {'name': 'keywords', 'content': keywords}
                self.project.head_config.setdefault('meta_tags', []).append(keywords_meta)
                item = QListWidgetItem(str(keywords_meta))
                item.setData(Qt.UserRole, keywords_meta)
                self.meta_list.addItem(item)
    
    def save_head_settings(self, dialog):
        # 保存Head设置
        self.project.title = self.title_edit.text().strip()
        self.project.head_config['lang'] = self.lang_edit.text().strip()
        # 刷新预览
        self.preview_server.update_html(self.project)
        self.statusBar.showMessage('Head设置已保存')
        dialog.accept()
    
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
