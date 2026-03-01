import sys
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
        QLabel, QTabWidget, QSplitter, QMessageBox, QComboBox
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QFont
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.ai_client import AIClient
from core.prompt_generator import PromptGenerator
from core.project import Project


class AIRequestThread(QThread):
    component_selection_finished = pyqtSignal(list)
    project_generation_finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, ai_client: AIClient, prompt_generator: PromptGenerator, user_input: str):
        super().__init__()
        self.ai_client = ai_client
        self.prompt_generator = prompt_generator
        self.user_input = user_input

    def run(self):
        try:
            # 第一阶段：请求组件选择
            self.select_components()
        except Exception as e:
            self.error.emit(str(e))
    
    def select_components(self):
        try:
            component_prompt = self.prompt_generator.generate_component_selection_prompt()
            messages = [
                {'role': 'system', 'content': component_prompt},
                {'role': 'user', 'content': self.user_input}
            ]
            response = self.ai_client.chat(messages, temperature=0.0)
            selected_components = self.prompt_generator.parse_component_selection(response)
            self.component_selection_finished.emit(selected_components)
            
            # 第二阶段：基于选择的组件生成项目
            self.generate_project(selected_components)
        except Exception as e:
            self.error.emit(str(e))
    
    def generate_project(self, selected_components):
        try:
            system_prompt = self.prompt_generator.generate_system_prompt()
            enhanced_input = f"{self.user_input}\n\n请使用以下组件：{', '.join(selected_components)}"
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': enhanced_input}
            ]
            response = self.ai_client.chat(messages, temperature=0.7)
            parsed_data = self.prompt_generator.parse_ai_response(response)
            self.project_generation_finished.emit(parsed_data)
        except Exception as e:
            self.error.emit(str(e))


class AIDialogWidget(QWidget if HAS_PYQT else object):
    project_loaded = pyqtSignal(object)

    def __init__(self, component_loader, parent=None):
        if not HAS_PYQT:
            raise ImportError('PyQt5 is required for GUI')
        super().__init__(parent)
        
        self.component_loader = component_loader
        self.ai_client = AIClient()
        self.prompt_generator = PromptGenerator(component_loader)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        tab_widget = QTabWidget()
        
        chat_tab = self.create_chat_tab()
        config_tab = self.create_config_tab()
        
        tab_widget.addTab(chat_tab, 'AI 对话')
        tab_widget.addTab(config_tab, 'API 配置')
        
        layout.addWidget(tab_widget)
    
    def create_chat_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont('Microsoft YaHei', 10))
        
        input_layout = QHBoxLayout()
        self.user_input = QTextEdit()
        self.user_input.setMaximumHeight(80)
        self.user_input.setPlaceholderText('请描述你想要创建的网页...')
        self.user_input.setFont(QFont('Microsoft YaHei', 10))
        
        self.send_btn = QPushButton('发送')
        self.send_btn.setMinimumWidth(80)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.user_input)
        input_layout.addWidget(self.send_btn)
        
        layout.addWidget(self.chat_history)
        layout.addLayout(input_layout)
        
        self.add_system_message('你好！我可以帮你生成网页项目。请描述你的需求，我会根据你的描述生成 .pyhtml 配置文件。')
        
        return widget
    
    def create_config_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel('API Key:')
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(self.ai_client.api_key or '')
        
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        
        model_layout = QHBoxLayout()
        model_label = QLabel('模型:')
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            'qwen3-max-preview', 'qwen3-max-2025-09-23', 'qwen3-max-2026-01-23', 'qwen3-max',
            'qwen-plus-2025-04-28', 'qwen-plus-2025-07-14', 'qwen-plus-2025-07-28', 'qwen-plus-2025-09-11',
            'qwen-plus-2025-12-01', 'qwen-plus-latest', 'qwen-plus', 'qwen3.5-plus-2026-02-15',
            'qwen3.5-plus', 'qwen-flash-2025-07-28', 'qwen-flash', 'qwen3.5-flash-2026-02-23',
            'qwen3.5-flash', 'qwen-turbo-2025-04-28', 'qwen-turbo-2025-07-15', 'qwen-turbo-latest', 'qwen-turbo'
        ])
        self.model_combo.setCurrentText(self.ai_client.model)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        
        button_layout = QHBoxLayout()
        self.test_btn = QPushButton('测试连接')
        self.test_btn.clicked.connect(self.test_connection)
        self.save_btn = QPushButton('保存配置')
        self.save_btn.clicked.connect(self.save_config)
        
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(api_key_layout)
        layout.addLayout(model_layout)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return widget
    
    def add_user_message(self, text):
        self.chat_history.append(f'<div style="color: #2196F3; font-weight: bold;">你:</div><div style="margin-left: 10px; margin-bottom: 10px;">{text}</div>')
    
    def add_system_message(self, text):
        self.chat_history.append(f'<div style="color: #4CAF50; font-weight: bold;">AI:</div><div style="margin-left: 10px; margin-bottom: 10px;">{text}</div>')
    
    def add_error_message(self, text):
        self.chat_history.append(f'<div style="color: #F44336; font-weight: bold;">错误:</div><div style="margin-left: 10px; margin-bottom: 10px;">{text}</div>')
    
    def send_message(self):
        user_text = self.user_input.toPlainText().strip()
        if not user_text:
            return
        
        if not self.ai_client.api_key:
            QMessageBox.warning(self, '提示', '请先在 API 配置标签页中配置 API Key')
            return
        
        self.add_user_message(user_text)
        self.user_input.clear()
        self.send_btn.setEnabled(False)
        self.send_btn.setText('分析需求...')
        
        self.thread = AIRequestThread(self.ai_client, self.prompt_generator, user_text)
        self.thread.component_selection_finished.connect(self.on_component_selection_finished)
        self.thread.project_generation_finished.connect(self.on_project_generation_finished)
        self.thread.error.connect(self.on_request_error)
        self.thread.start()
    
    def on_component_selection_finished(self, selected_components):
        self.send_btn.setText('生成项目...')
        components_str = ', '.join(selected_components)
        self.add_system_message(f'已选择组件: {components_str}')
    
    def on_project_generation_finished(self, data):
        self.send_btn.setEnabled(True)
        self.send_btn.setText('发送')
        
        try:
            project = Project.from_dict(data, self.component_loader)
            self.add_system_message('项目生成成功！正在加载...')
            self.project_loaded.emit(project)
            self.add_system_message('项目已加载到编辑器，你可以预览或继续编辑。')
        except Exception as e:
            self.add_error_message(f'加载项目失败: {e}')
    
    def on_request_error(self, error_msg):
        self.send_btn.setEnabled(True)
        self.send_btn.setText('发送')
        self.add_error_message(error_msg)
    
    def test_connection(self):
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText()
        
        if not api_key:
            QMessageBox.warning(self, '提示', '请输入 API Key')
            return
        
        self.test_btn.setEnabled(False)
        self.test_btn.setText('测试中...')
        
        test_client = AIClient(api_key, model)
        
        class TestThread(QThread):
            finished = pyqtSignal(bool)
            
            def __init__(self, client):
                super().__init__()
                self.client = client
            
            def run(self):
                result = self.client.test_connection()
                self.finished.emit(result)
        
        self.test_thread = TestThread(test_client)
        
        def on_test_finished(success):
            self.test_btn.setEnabled(True)
            self.test_btn.setText('测试连接')
            if success:
                QMessageBox.information(self, '成功', '连接成功！')
            else:
                QMessageBox.warning(self, '失败', '连接失败，请检查 API Key 是否正确')
        
        self.test_thread.finished.connect(on_test_finished)
        self.test_thread.start()
    
    def save_config(self):
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText()
        
        if not api_key:
            QMessageBox.warning(self, '提示', '请输入 API Key')
            return
        
        self.ai_client.save_config(api_key, model)
        QMessageBox.information(self, '成功', '配置已保存！')
