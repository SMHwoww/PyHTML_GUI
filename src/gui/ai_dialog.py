import sys
from pathlib import Path

try:
    from PyQt5.QtCore import QThread, pyqtSignal
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.ai_client import AIDialogWidget, AIClient
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


class AIDialogWidgetImpl(AIDialogWidget):
    def __init__(self, component_loader, parent=None):
        super().__init__(component_loader, parent)
        self.prompt_generator = PromptGenerator(component_loader)
    
    def send_message(self):
        user_text = self.user_input.toPlainText().strip()
        if not user_text:
            return
        
        if not self.ai_client.api_key:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, '提示', '请先在 API 配置标签页中配置 API Key')
            return
        
        self.add_user_message(user_text)
        self.user_input.clear()
        self.send_btn.setEnabled(False)
        self.send_btn.setText('分析需求...')
        
        # 确保之前的线程已终止
        if hasattr(self, 'thread') and self.thread and hasattr(self.thread, 'isRunning') and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
        
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
        from PyQt5.QtWidgets import QMessageBox
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
        
        # 确保之前的测试线程已终止
        if hasattr(self, 'test_thread') and self.test_thread and self.test_thread.isRunning():
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
