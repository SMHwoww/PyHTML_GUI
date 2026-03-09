import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import requests

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


class AIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = 'qwen-max', base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', max_tokens: Optional[int] = 8192):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.config_path = self._get_config_path()
        
        if not self.api_key:
            self.api_key = self._load_api_key()
    
    def _get_config_path(self) -> Path:
        home_dir = Path.home()
        config_dir = home_dir / '.pyhtml'
        config_dir.mkdir(exist_ok=True)
        return config_dir / 'ai_config.json'
    
    def _load_api_key(self) -> Optional[str]:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.model = config.get('model', 'qwen-max')
                    self.base_url = config.get('base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
                    self.max_tokens = config.get('max_tokens', 8192)
                    return config.get('api_key')
            except Exception as e:
                print(f'Failed to load API key: {e}')
        return None
    
    def save_config(self, api_key: str, model: str = 'qwen-max', base_url: str = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', max_tokens: Optional[int] = 8192):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens
        config = {'api_key': api_key, 'model': model, 'base_url': base_url, 'max_tokens': max_tokens}
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'Failed to save config: {e}')
    
    def test_connection(self) -> bool:
        if not self.api_key:
            return False
        try:
            response = self.chat([
                {'role': 'user', 'content': '请回复"连接成功"'}
            ], temperature=0.0)
            return '连接成功' in response
        except Exception as e:
            print(f'Connection test failed: {e}')
            return False
    
    def chat(self, messages: list, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        if not self.api_key:
            raise ValueError('API key not set')
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature
        }
        
        if max_tokens is not None:
            data['max_tokens'] = max_tokens
        elif self.max_tokens:
            data['max_tokens'] = self.max_tokens
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            raise Exception('请求超时，请重试')
        except requests.exceptions.RequestException as e:
            raise Exception(f'API 请求失败: {e}')
        except KeyError as e:
            raise Exception(f'API 返回格式错误: {e}')
        except Exception as e:
            raise Exception(f'调用 AI 失败: {e}')


class AIApiConfigDialog(QWidget if HAS_PYQT else object):
    def __init__(self, parent=None):
        if not HAS_PYQT:
            raise ImportError('PyQt5 is required for GUI')
        super().__init__(parent)
        
        self.ai_client = AIClient()
        self.setWindowTitle('AI配置')
        self.setGeometry(300, 200, 500, 200)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel('API Key:')
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(self.ai_client.api_key or '')
        
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        
        base_url_layout = QHBoxLayout()
        base_url_label = QLabel('API地址:')
        self.base_url_input = QLineEdit()
        self.base_url_input.setText(self.ai_client.base_url)
        self.base_url_input.setPlaceholderText('请输入API请求地址')
        
        base_url_layout.addWidget(base_url_label)
        base_url_layout.addWidget(self.base_url_input)
        
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
        
        # 添加 tokens 最大值控制
        max_tokens_layout = QHBoxLayout()
        max_tokens_label = QLabel('Tokens最大值:')
        self.max_tokens_input = QLineEdit()
        self.max_tokens_input.setText(str(self.ai_client.max_tokens))
        self.max_tokens_input.setPlaceholderText('请输入最大tokens数')
        
        max_tokens_layout.addWidget(max_tokens_label)
        max_tokens_layout.addWidget(self.max_tokens_input)
        
        button_layout = QHBoxLayout()
        self.test_btn = QPushButton('测试连接')
        self.test_btn.clicked.connect(self.test_connection)
        self.save_btn = QPushButton('保存配置')
        self.save_btn.clicked.connect(self.save_config)
        
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(api_key_layout)
        layout.addLayout(base_url_layout)
        layout.addLayout(model_layout)
        layout.addLayout(max_tokens_layout)
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def test_connection(self):
        from PyQt5.QtWidgets import QMessageBox
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText()
        base_url = self.base_url_input.text().strip()
        max_tokens_str = self.max_tokens_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, '提示', '请输入 API Key')
            return
        
        if not base_url:
            QMessageBox.warning(self, '提示', '请输入 API 地址')
            return
        
        try:
            max_tokens = int(max_tokens_str) if max_tokens_str else 8192
            if max_tokens <= 0:
                raise ValueError('Tokens最大值必须大于0')
        except ValueError as e:
            QMessageBox.warning(self, '提示', f'无效的Tokens最大值: {e}')
            return
        
        self.test_btn.setEnabled(False)
        self.test_btn.setText('测试中...')
        
        test_client = AIClient(api_key, model, base_url, max_tokens)
        
        class TestThread(QThread):
            finished = pyqtSignal(bool)
            
            def __init__(self, client):
                super().__init__()
                self.client = client
            
            def run(self):
                result = self.client.test_connection()
                self.finished.emit(result)
        
        # 确保之前的测试线程已终止
        if hasattr(self, 'test_thread') and self.test_thread and hasattr(self.test_thread, 'isRunning') and self.test_thread.isRunning():
            self.test_thread.terminate()
            self.test_thread.wait()
        
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
        from PyQt5.QtWidgets import QMessageBox
        api_key = self.api_key_input.text().strip()
        model = self.model_combo.currentText()
        base_url = self.base_url_input.text().strip()
        max_tokens_str = self.max_tokens_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, '提示', '请输入 API Key')
            return
        
        if not base_url:
            QMessageBox.warning(self, '提示', '请输入 API 地址')
            return
        
        try:
            max_tokens = int(max_tokens_str) if max_tokens_str else 8192
            if max_tokens <= 0:
                raise ValueError('Tokens最大值必须大于0')
        except ValueError as e:
            QMessageBox.warning(self, '提示', f'无效的Tokens最大值: {e}')
            return
        
        self.ai_client.save_config(api_key, model, base_url, max_tokens)
        QMessageBox.information(self, '成功', '配置已保存！')


class AIDialogWidget(QWidget if HAS_PYQT else object):
    project_loaded = pyqtSignal(object)

    def __init__(self, component_loader, parent=None):
        if not HAS_PYQT:
            raise ImportError('PyQt5 is required for GUI')
        super().__init__(parent)
        
        self.component_loader = component_loader
        self.ai_client = AIClient()
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        chat_tab = self.create_chat_tab()
        layout.addWidget(chat_tab)
    
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
    

    def add_user_message(self, text):
        self.chat_history.append(f'<div style="color: #2196F3; font-weight: bold;">你:</div><div style="margin-left: 10px; margin-bottom: 10px;">{text}</div>')
    
    def add_system_message(self, text):
        self.chat_history.append(f'<div style="color: #4CAF50; font-weight: bold;">AI:</div><div style="margin-left: 10px; margin-bottom: 10px;">{text}</div>')
    
    def add_error_message(self, text):
        self.chat_history.append(f'<div style="color: #F44336; font-weight: bold;">错误:</div><div style="margin-left: 10px; margin-bottom: 10px;">{text}</div>')
    
    def send_message(self):
        # 这个方法会在 gui/ai_dialog.py 中实现
        pass
    

