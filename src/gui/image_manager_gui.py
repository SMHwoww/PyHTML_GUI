from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QCheckBox,
                            QTextEdit, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication
import os
import requests
import hashlib
import time
from typing import Dict, Any, Optional
from core.image_manager import ImageManager
from core.ai_client import AIClient

HAS_REQUESTS = True


def get_cache_dir() -> str:
    config_dir = os.path.join(os.path.expanduser('~'), '.pyhtml')
    cache_dir = os.path.join(config_dir, 'image_cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_cache_path(url: str) -> str:
    cache_dir = get_cache_dir()
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    return os.path.join(cache_dir, f'{url_hash}.cache')


class ImageLoadWorker(QThread):
    image_loaded = pyqtSignal(int, QIcon)
    
    def __init__(self, row, url):
        super().__init__()
        self.row = row
        self.url = url
    
    def run(self):
        try:
            cache_path = get_cache_path(self.url)
            pixmap = None
            
            if os.path.exists(cache_path):
                pixmap = QPixmap(cache_path)
            
            if not pixmap or pixmap.isNull():
                response = requests.get(self.url, timeout=5)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        with open(cache_path, 'wb') as f:
                            f.write(response.content)
            
            if pixmap and not pixmap.isNull():
                icon = QIcon(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.image_loaded.emit(self.row, icon)
        except Exception:
            pass


class PreviewImageLoadWorker(QThread):
    image_loaded = pyqtSignal(QPixmap)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            cache_path = get_cache_path(self.url)
            pixmap = None
            
            if os.path.exists(cache_path):
                pixmap = QPixmap(cache_path)
            
            if not pixmap or pixmap.isNull():
                response = requests.get(self.url, timeout=10)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if not pixmap.isNull():
                        with open(cache_path, 'wb') as f:
                            f.write(response.content)
            
            if pixmap and not pixmap.isNull():
                self.image_loaded.emit(pixmap)
        except Exception:
            pass


class ImageUploadWorker(QThread):
    upload_completed = pyqtSignal(bool, str, dict)
    
    def __init__(self, image_manager, file_path):
        super().__init__()
        self.image_manager = image_manager
        self.file_path = file_path
    
    def run(self):
        try:
            # 检查是否设置了API token
            api_token = self.image_manager.load_image_api_token()
            if not api_token:
                self.upload_completed.emit(False, '请先在图片设置中设置API token', {})
                return
            
            # 检查API token是否有效（尝试获取临时token）
            temp_token = self.image_manager.get_temp_token()
            if not temp_token:
                # 强制获取新的临时token
                temp_token = self.image_manager.get_temp_token(force_refresh=True)
                if not temp_token:
                    self.upload_completed.emit(False, 'API token 无效或已过期，请在图片设置中检查并更新', {})
                    return
            
            # 使用ImageManager上传图片
            image_data = self.image_manager.upload_image(self.file_path)
            if image_data:
                self.upload_completed.emit(True, '图片上传成功', image_data)
            else:
                # 再次尝试上传
                temp_token = self.image_manager.get_temp_token(force_refresh=True)
                if temp_token:
                    image_data = self.image_manager.upload_image(self.file_path)
                    if image_data:
                        self.upload_completed.emit(True, '图片上传成功', image_data)
                    else:
                        self.upload_completed.emit(False, '上传失败: 可能是临时token过期或网络问题', {})
                else:
                    self.upload_completed.emit(False, '上传失败: 无法获取临时token', {})
        except Exception as e:
            self.upload_completed.emit(False, f'上传失败: {str(e)}', {})


class AIImageWorker(QThread):
    progress = pyqtSignal(str)
    completed = pyqtSignal(bool, str, dict)
    
    def __init__(self, ai_client, prompt, model, size):
        super().__init__()
        self.ai_client = ai_client
        self.prompt = prompt
        self.model = model
        self.size = size
    
    def run(self):
        try:
            if not self.ai_client or not self.ai_client.api_key:
                self.completed.emit(False, '请先在 AI 配置中设置 API Key', {})
                return
            
            api_key = self.ai_client.api_key
            
            self.progress.emit('正在调用 AI API...')
            
            try:
                # 根据模型类型选择合适的API
                if self.model.startswith('wan'):
                    if self.model.startswith('wan2.6'):
                        # wan2.6 使用同步接口
                        image_url = self._call_wan26_api(api_key)
                    else:
                        # 其他 wan 模型使用异步接口
                        image_url = self._call_wan_async_api(api_key)
                else:
                    # 非 wan 系列模型（qwen-image系列）使用同步接口
                    image_url = self._call_qwen_image_api(api_key)
                
                if not image_url:
                    self.completed.emit(False, '无法从响应中获取图片 URL', {})
                    return
                
                self.progress.emit('下载图片中...')
                
                # 下载图片
                temp_dir = os.path.join(os.path.expanduser('~'), '.pyhtml', 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                filename = f'ai_generated_{int(time.time())}.png'
                save_path = os.path.join(temp_dir, filename)
                
                response = requests.get(image_url, timeout=60, stream=True)
                response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                self.completed.emit(True, '图片下载成功', {'local_path': save_path})
                    
            except Exception as e:
                self.completed.emit(False, f'生成失败: {str(e)}', {})
                
        except Exception as e:
            self.completed.emit(False, f'生成失败: {str(e)}', {})
    
    def _call_qwen_image_api(self, api_key):
        """调用 Qwen-Image 系列模型的同步 API"""
        url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'text': self.prompt}
                        ]
                    }
                ]
            },
            'parameters': {
                'negative_prompt': '低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。',
                'prompt_extend': True,
                'watermark': False,
                'size': self.size
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        code = result.get('code')
        if code is not None and code != '':
            message = result.get('message', '未知错误')
            raise Exception(f'API 错误: {code} - {message}')
        
        self.progress.emit('解析响应...')
        
        # 提取图片 URL
        output = result.get('output', {})
        choices = output.get('choices', [])
        if choices:
            message = choices[0].get('message', {})
            content = message.get('content', [])
            if content:
                for item in content:
                    if isinstance(item, dict) and 'image' in item:
                        return item['image']
        
        return None
    
    def _call_wan26_api(self, api_key):
        """调用 Wan2.6 模型的同步 API"""
        url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'text': self.prompt}
                        ]
                    }
                ]
            },
            'parameters': {
                'negative_prompt': '低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。',
                'prompt_extend': True,
                'watermark': False,
                'n': 1,
                'size': self.size
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        code = result.get('code')
        if code is not None and code != '':
            message = result.get('message', '未知错误')
            raise Exception(f'API 错误: {code} - {message}')
        
        self.progress.emit('解析响应...')
        
        # 提取图片 URL
        output = result.get('output', {})
        choices = output.get('choices', [])
        if choices:
            message = choices[0].get('message', {})
            content = message.get('content', [])
            if content:
                for item in content:
                    if isinstance(item, dict) and 'image' in item:
                        return item['image']
        
        return None
    
    def _call_wan_async_api(self, api_key):
        """调用 Wanx 系列模型的异步 API（创建任务 + 查询结果）"""
        # 步骤1：创建任务
        self.progress.emit('创建任务中...')
        
        task_url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis'
        
        headers = {
            'X-DashScope-Async': 'enable',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        payload = {
            'model': self.model,
            'input': {
                'prompt': self.prompt
            },
            'parameters': {
                'style': '<auto>',
                'size': self.size,
                'n': 1,
                'negative_prompt': '低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。'
            }
        }
        
        response = requests.post(task_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        task_result = response.json()
        
        code = task_result.get('code')
        if code is not None and code != '':
            message = task_result.get('message', '未知错误')
            raise Exception(f'创建任务失败: {code} - {message}')
        
        task_id = task_result.get('output', {}).get('task_id')
        if not task_id:
            raise Exception('未获取到任务 ID')
        
        self.progress.emit(f'任务已创建: {task_id}，等待生成...')
        
        # 步骤2：查询任务结果
        result_url = f'https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}'
        
        max_attempts = 200  # 最多查询 200 次
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(2)  # 每 2 秒查询一次
            attempt += 1
            
            self.progress.emit(f'查询进度... ({attempt}/{max_attempts})')
            
            response = requests.get(result_url, headers={'Authorization': f'Bearer {api_key}'}, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            code = result.get('code')
            if code is not None and code != '':
                message = result.get('message', '未知错误')
                raise Exception(f'查询任务失败: {code} - {message}')
            
            output = result.get('output', {})
            task_status = output.get('task_status')
            
            if task_status == 'SUCCEEDED':
                self.progress.emit('解析响应...')
                # 提取图片 URL
                results = output.get('results', [])
                if results:
                    for item in results:
                        if isinstance(item, dict) and 'url' in item:
                            return item['url']
                break
            elif task_status == 'FAILED':
                error_message = output.get('message', '任务失败')
                raise Exception(f'生成失败: {error_message}')
            elif task_status in ['PENDING', 'RUNNING']:
                continue  # 继续查询
        
        raise Exception('任务超时，未能在规定时间内完成')


class AIImageGeneratorDialog(QDialog):
    
    def __init__(self, parent=None, image_manager=None):
        super().__init__(parent)
        self.image_manager = image_manager or ImageManager()
        self.ai_client = AIClient()
        self.current_image_url = None
        self.worker = None
        self.upload_worker = None
        self.preview_workers = []
        self.local_image_path = None
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle('AI 图片生成')
        self.setGeometry(200, 100, 900, 650)
        layout = QVBoxLayout(self)
        
        # 主布局
        main_layout = QHBoxLayout()
        
        # 左侧输入区域
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        # 提示词
        left_layout.addWidget(QLabel('提示词:'))
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText('请输入图片描述...')
        self.prompt_text.setMaximumHeight(150)
        left_layout.addWidget(self.prompt_text)
        
        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel('模型:'))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "wanx-v1",
            "wanx2.0-t2i-turbo",
            "wanx2.1-t2i-plus",
            "wanx2.1-t2i-turbo",
            "wan2.2-t2i-flash",
            "wan2.2-t2i-plus",
            "wan2.5-t2i-preview",
            "wan2.6-t2i",
            "qwen-image",
            "qwen-image-plus",
            "qwen-image-plus-2026-01-09",
            "qwen-image-max",
            "qwen-image-max-2025-12-30",
            "z-image-turbo"
        ])
        self.model_combo.setCurrentText('wanx2.1-t2i-turbo')
        model_layout.addWidget(self.model_combo)
        left_layout.addLayout(model_layout)
        
        # 尺寸选择
        size_layout = QVBoxLayout()
        size_layout.addWidget(QLabel('尺寸:'))
        
        # 预设尺寸选择
        preset_layout = QHBoxLayout()
        self.size_combo = QComboBox()
        preset_layout.addWidget(self.size_combo)
        size_layout.addLayout(preset_layout)
        
        # 自定义尺寸输入
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel('自定义:'))
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(512, 2048)
        self.width_spin.setValue(1024)
        self.width_spin.setFixedWidth(80)
        custom_layout.addWidget(self.width_spin)
        
        custom_layout.addWidget(QLabel('×'))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(512, 2048)
        self.height_spin.setValue(1024)
        self.height_spin.setFixedWidth(80)
        custom_layout.addWidget(self.height_spin)
        
        size_layout.addLayout(custom_layout)
        
        # 分辨率提示
        self.resolution_info = QLabel('')
        self.resolution_info.setStyleSheet('font-size: 10px; color: #666;')
        size_layout.addWidget(self.resolution_info)
        
        left_layout.addLayout(size_layout)
        
        # 模型与尺寸映射
        self.model_size_map = {
            # qwen-image-2.0 系列（支持自由设置，这里提供常用选项）
            'qwen-image': [
                '1024*1024', '1024*768', '768*1024', '1280*720', '720*1280',
                '1536*1024', '1024*1536', '1920*1080', '1080*1920'
            ],
            # qwen-image-max、qwen-image-plus 系列（仅支持固定分辨率）
            'qwen-image-plus': ['1664*928', '1472*1104', '1328*1328', '1104*1472', '928*1664'],
            'qwen-image-plus-2026-01-09': ['1664*928', '1472*1104', '1328*1328', '1104*1472', '928*1664'],
            'qwen-image-max': ['1664*928', '1472*1104', '1328*1328', '1104*1472', '928*1664'],
            'qwen-image-max-2025-12-30': ['1664*928', '1472*1104', '1328*1328', '1104*1472', '928*1664'],
            # 万相 V2 版模型 (2.0 及以上版本)
            'wanx2.0-t2i-turbo': ['1024*1024', '1440*810', '810*1440', '1440*1080', '1080*1440', '1024*768', '768*1024'],
            'wanx2.1-t2i-plus': ['1024*1024', '1440*810', '810*1440', '1440*1080', '1080*1440', '1024*768', '768*1024'],
            'wanx2.1-t2i-turbo': ['1024*1024', '1440*810', '810*1440', '1440*1080', '1080*1440', '1024*768', '768*1024'],
            'wan2.2-t2i-flash': ['1024*1024', '1440*810', '810*1440', '1440*1080', '1080*1440', '1024*768', '768*1024'],
            'wan2.2-t2i-plus': ['1024*1024', '1440*810', '810*1440', '1440*1080', '1080*1440', '1024*768', '768*1024'],
            'wan2.5-t2i-preview': ['1024*1024', '1440*810', '810*1440', '1440*1080', '1080*1440', '1024*768', '768*1024'],
            'wan2.6-t2i': ['1024*1024', '1440*810', '810*1440', '1440*1080', '1080*1440', '1024*768', '768*1024'],
            # 其他模型（默认选项）
            'wanx-v1': ['1024*1024', '768*768', '576*1024', '1024*576', '720*1280', '1280*720', '864*1152', '1152*864'],
            'z-image-turbo': ['1024*1024', '768*768', '576*1024', '1024*576', '720*1280', '1280*720', '864*1152', '1152*864']
        }
        
        # 连接模型选择信号
        self.model_combo.currentTextChanged.connect(self._update_size_options)
        
        # 初始化尺寸选项
        self._update_size_options(self.model_combo.currentText())
        
        # 按钮
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton('生成图片')
        self.generate_button.setStyleSheet('background-color: #4CAF50; color: white; padding: 8px 20px;')
        self.generate_button.clicked.connect(self._generate_image)
        button_layout.addWidget(self.generate_button)
        
        self.clear_button = QPushButton('清空')
        self.clear_button.clicked.connect(self._clear_prompt)
        button_layout.addWidget(self.clear_button)
        left_layout.addLayout(button_layout)
        
        # 进度标签
        self.progress_label = QLabel('就绪')
        left_layout.addWidget(self.progress_label)
        
        left_layout.addStretch()
        
        # 右侧图片显示区域
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel('生成结果:'))
        self.image_label = QLabel('生成的图片将显示在这里')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet('border: 1px solid #ddd; background-color: #f9f9f9;')
        right_layout.addWidget(self.image_label)
        
        # 结果信息
        self.result_info = QLabel('')
        right_layout.addWidget(self.result_info)
        
        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        self.close_button = QPushButton('关闭')
        self.close_button.clicked.connect(self.accept)
        close_layout.addWidget(self.close_button)
        right_layout.addLayout(close_layout)
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)
        
        layout.addLayout(main_layout)
    
    def closeEvent(self, event):
        """处理对话框关闭事件，确保正确清理线程"""
        self._cleanup_workers()
        event.accept()
    
    def _cleanup_workers(self):
        """清理所有工作线程"""
        # 清理主工作线程
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(1000)
        
        # 清理上传工作线程
        if self.upload_worker and self.upload_worker.isRunning():
            self.upload_worker.quit()
            self.upload_worker.wait(1000)
        
        # 清理预览工作线程
        for worker in self.preview_workers:
            if worker and worker.isRunning():
                worker.quit()
                worker.wait(1000)
        
        self.preview_workers.clear()
    
    def _update_size_options(self, model):
        """根据选择的模型更新尺寸选项"""
        self.size_combo.clear()
        
        # 添加自定义选项
        self.size_combo.addItem('自定义')
        
        if model in self.model_size_map:
            sizes = self.model_size_map[model]
            self.size_combo.addItems(sizes)
            # 设置默认值
            if sizes:
                self.size_combo.setCurrentIndex(1)  # 默认选择第一个预设尺寸
        else:
            # 默认尺寸选项
            default_sizes = ['1024*1024', '768*768', '576*1024', '1024*576']
            self.size_combo.addItems(default_sizes)
            self.size_combo.setCurrentIndex(1)  # 默认选择第一个预设尺寸
        
        # 更新分辨率提示信息
        self._update_resolution_info(model)
        
        # 连接尺寸选择变化信号
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        
        # 初始状态
        self._on_size_changed(self.size_combo.currentIndex())
    
    def _update_resolution_info(self, model):
        """根据模型类型更新分辨率提示信息"""
        if model == 'qwen-image':
            # qwen-image-2.0 系列
            self.resolution_info.setText('支持自由设置宽高，总像素需在512*512至2048*2048之间')
            # 更新范围
            self.width_spin.setRange(512, 2048)
            self.height_spin.setRange(512, 2048)
        elif model in ['qwen-image-plus', 'qwen-image-plus-2026-01-09', 'qwen-image-max', 'qwen-image-max-2025-12-30']:
            # qwen-image-max、qwen-image-plus 系列
            self.resolution_info.setText('仅支持固定分辨率，自定义输入将被忽略')
            # 禁用自定义输入
            self.width_spin.setEnabled(False)
            self.height_spin.setEnabled(False)
        elif model in ['wanx2.0-t2i-turbo', 'wanx2.1-t2i-plus', 'wanx2.1-t2i-turbo', 
                     'wan2.2-t2i-flash', 'wan2.2-t2i-plus', 'wan2.5-t2i-preview', 'wan2.6-t2i']:
            # 万相 V2 版模型
            self.resolution_info.setText('支持在 [512, 1440] 像素范围内任意组合宽高，总像素不超过 1440*1440')
            # 更新范围
            self.width_spin.setRange(512, 1440)
            self.height_spin.setRange(512, 1440)
        else:
            # 其他模型
            self.resolution_info.setText('支持常用分辨率设置')
            # 默认范围
            self.width_spin.setRange(512, 2048)
            self.height_spin.setRange(512, 2048)
    
    def _on_size_changed(self, index):
        """处理尺寸选择变化"""
        if self.size_combo.currentText() == '自定义':
            # 启用自定义输入
            self.width_spin.setEnabled(True)
            self.height_spin.setEnabled(True)
        else:
            # 禁用自定义输入
            self.width_spin.setEnabled(False)
            self.height_spin.setEnabled(False)
            # 从预设尺寸中提取宽高
            size_text = self.size_combo.currentText()
            if '*' in size_text:
                try:
                    width, height = map(int, size_text.split('*'))
                    self.width_spin.setValue(width)
                    self.height_spin.setValue(height)
                except ValueError:
                    pass
    
    def _clear_prompt(self):
        self.prompt_text.clear()
        self.image_label.setText('生成的图片将显示在这里')
        self.result_info.setText('')
        self.progress_label.setText('就绪')
        self.current_image_url = None
        self.local_image_path = None
    
    def _display_local_image(self, file_path):
        """直接显示本地图片"""
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(
                400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
    
    def _generate_image(self):
        prompt = self.prompt_text.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, '提示', '请输入提示词')
            return
        
        model = self.model_combo.currentText()
        
        # 获取分辨率
        if self.size_combo.currentText() == '自定义':
            # 对于不支持自定义分辨率的模型，使用第一个预设尺寸
            if model in ['qwen-image-plus', 'qwen-image-plus-2026-01-09', 'qwen-image-max', 'qwen-image-max-2025-12-30']:
                size = self.size_combo.itemText(1)  # 使用第一个预设尺寸
            else:
                # 检查总像素限制
                width = self.width_spin.value()
                height = self.height_spin.value()
                
                # 检查万相 V2 版模型的限制
                if model in ['wanx2.0-t2i-turbo', 'wanx2.1-t2i-plus', 'wanx2.1-t2i-turbo', 
                           'wan2.2-t2i-flash', 'wan2.2-t2i-plus', 'wan2.5-t2i-preview', 'wan2.6-t2i']:
                    if width * height > 1440 * 1440:
                        QMessageBox.warning(self, '提示', '万相 V2 版模型总像素不能超过 1440*1440')
                        return
                # 检查 qwen-image-2.0 系列的限制
                elif model == 'qwen-image':
                    if width < 512 or width > 2048 or height < 512 or height > 2048:
                        QMessageBox.warning(self, '提示', 'qwen-image-2.0 系列分辨率需在 512-2048 之间')
                        return
                
                size = f'{width}*{height}'
        else:
            size = self.size_combo.currentText()
        
        self.generate_button.setEnabled(False)
        self.progress_label.setText('生成中...')
        
        # 先清理之前的 worker
        self._cleanup_workers()
        
        self.worker = AIImageWorker(self.ai_client, prompt, model, size)
        
        def on_progress(message):
            self.progress_label.setText(message)
        
        def on_completed(success, message, data):
            if success:
                self.local_image_path = data.get('local_path')
                self.progress_label.setText('图片下载完成，正在展示并上传...')
                self.result_info.setText(message)
                
                # 先显示本地图片
                if self.local_image_path and os.path.exists(self.local_image_path):
                    self._display_local_image(self.local_image_path)
                
                # 使用 ImageUploadWorker 上传图片
                self._upload_image(self.local_image_path)
            else:
                self.generate_button.setEnabled(True)
                self.progress_label.setText('失败')
                self.result_info.setText(message)
                QMessageBox.warning(self, '错误', message)
                print(f"上传失败: {message}")
        
        self.worker.progress.connect(on_progress)
        self.worker.completed.connect(on_completed)
        self.worker.start()
    
    def _upload_image(self, file_path):
        """使用 ImageUploadWorker 上传图片"""
        # 创建上传进度对话框
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle('上传中')
        progress_dialog.setGeometry(300, 200, 300, 100)
        progress_layout = QVBoxLayout(progress_dialog)
        
        progress_label = QLabel('正在上传图片，请稍候...')
        progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(progress_label)
        
        self.upload_worker = ImageUploadWorker(self.image_manager, file_path)
        
        def on_upload_completed(success, message, image_data):
            progress_dialog.accept()
            self.generate_button.setEnabled(True)
            if success:
                self.progress_label.setText('完成')
                self.result_info.setText(message)
                self.current_image_url = image_data.get('links', {}).get('url', '')
                QMessageBox.information(self, '成功', message)
            else:
                self.progress_label.setText('上传失败，但本地图片已保存')
                self.result_info.setText(message)
                QMessageBox.warning(self, '警告', f'图片生成成功，但上传失败：{message}')
        
        self.upload_worker.upload_completed.connect(on_upload_completed)
        self.upload_worker.start()
        
        # 显示进度对话框
        progress_dialog.exec_()


class ImageSettingsDialog(QDialog):
    
    def __init__(self, parent=None, image_manager=None):
        super().__init__(parent)
        self.image_manager = image_manager or ImageManager()
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle('图片设置')
        self.setGeometry(300, 200, 450, 300)
        layout = QVBoxLayout(self)
        
        # API Token设置
        layout.addWidget(QLabel('请输入图片API的token:'))
        
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText('在这键入你的图片API token，不用包含Bearer前缀')
        
        saved_token = self.image_manager.load_image_api_token()
        if saved_token:
            self.token_input.setText(saved_token)
        
        layout.addWidget(self.token_input)
        
        # 添加PICUI图床链接
        from PyQt5.QtCore import Qt
        
        picui_label = QLabel()
        picui_label.setText('图片存储服务由PICUI公益图床提供，<a href="https://picui.cn/user/tokens">点击这里</a>申请API Token')
        picui_label.setOpenExternalLinks(True)
        picui_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        layout.addWidget(picui_label)
        
        # 缓存设置
        layout.addWidget(QLabel('\n缓存设置:'))
        
        cache_layout = QHBoxLayout()
        cache_label = QLabel('清理图片缓存:')
        cache_button = QPushButton('清理缓存')
        cache_button.setStyleSheet('background-color: #ff9800; color: white; padding: 5px 15px;')
        cache_button.clicked.connect(self._clear_image_cache)
        cache_layout.addWidget(cache_label)
        cache_layout.addWidget(cache_button)
        cache_layout.addStretch()
        layout.addLayout(cache_layout)
        
        # 删除设置
        layout.addWidget(QLabel('\n删除设置:'))
        
        self.delete_cloud_checkbox = QCheckBox('删除时同时删除云端资源')
        # 默认勾选
        self.delete_cloud_checkbox.setChecked(True)
        layout.addWidget(self.delete_cloud_checkbox)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        save_button = QPushButton('保存')
        cancel_button = QPushButton('取消')
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        save_button.clicked.connect(self._save_settings)
        cancel_button.clicked.connect(self.reject)
    
    def _save_settings(self):
        token = self.token_input.text().strip()
        self.image_manager.save_image_api_token(token)
        QMessageBox.information(self, '成功', '设置已保存')
        self.accept()
    
    def _clear_image_cache(self):
        # 添加确认对话框
        reply = QMessageBox.question(
            self, 
            '确认清理缓存', 
            '确定要清理所有图片缓存吗？',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        cache_dir = get_cache_dir()
        cache_count = 0
        cache_size = 0
        
        if os.path.exists(cache_dir):
            for filename in os.listdir(cache_dir):
                if filename.endswith('.cache'):
                    file_path = os.path.join(cache_dir, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cache_count += 1
                        cache_size += file_size
                    except Exception:
                        pass
        
        cache_size_mb = cache_size / (1024 * 1024) if cache_size > 0 else 0
        QMessageBox.information(
            self, 
            '缓存清理完成', 
            f'已清理 {cache_count} 个缓存文件\n释放空间: {cache_size_mb:.2f} MB'
        )


class ImageManagementDialog(QDialog):
    
    THUMBNAIL_SIZE = QSize(120, 120)
    GRID_SIZE = QSize(150, 180)
    PREVIEW_WIDTH = 780
    PREVIEW_HEIGHT = 560
    REQUEST_TIMEOUT = 10
    
    def __init__(self, parent=None, image_manager=None):
        super().__init__(parent)
        self.image_manager = image_manager or ImageManager()
        self.current_selected_item = None
        self.image_load_workers = []
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle('图片管理')
        self.setGeometry(200, 100, 800, 600)
        layout = QVBoxLayout(self)
        
        self._setup_top_buttons(layout)
        self._setup_action_buttons(layout)
        self._setup_image_list(layout)
        self._connect_signals()
        self._load_images()
    
    def _setup_top_buttons(self, layout):
        top_layout = QHBoxLayout()
        self.refresh_button = QPushButton('刷新图片列表')
        self.upload_button = QPushButton('上传图片')
        self.upload_button.setStyleSheet('background-color: #4CAF50; color: white; padding: 5px 15px;')
        self.close_button = QPushButton('关闭')
        top_layout.addWidget(self.refresh_button)
        top_layout.addWidget(self.upload_button)
        top_layout.addStretch()
        top_layout.addWidget(self.close_button)
        layout.addLayout(top_layout)
    
    def _setup_action_buttons(self, layout):
        self.button_layout = QHBoxLayout()
        
        self.delete_button = QPushButton('删除')
        self.delete_button.setStyleSheet('background-color: #ff4444; color: white; padding: 5px 15px;')
        self.delete_button.hide()
        
        self.copy_button = QPushButton('复制链接')
        self.copy_button.setStyleSheet('background-color: #4CAF50; color: white; padding: 5px 15px;')
        self.copy_button.hide()
        
        self.preview_button = QPushButton('预览')
        self.preview_button.setStyleSheet('background-color: #2196F3; color: white; padding: 5px 15px;')
        self.preview_button.hide()
        
        # 删除设置
        self.delete_cloud_checkbox = QCheckBox('同时删除云端资源')
        self.delete_cloud_checkbox.setChecked(True)
        self.delete_cloud_checkbox.hide()
        
        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.delete_cloud_checkbox)
        self.button_layout.addWidget(self.copy_button)
        self.button_layout.addWidget(self.preview_button)
        self.button_layout.addStretch()
        layout.addLayout(self.button_layout)
    
    def _setup_image_list(self, layout):
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(self.THUMBNAIL_SIZE)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setGridSize(self.GRID_SIZE)
        self.image_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.image_list)
    
    def _connect_signals(self):
        self.refresh_button.clicked.connect(self._load_images)
        self.upload_button.clicked.connect(self._upload_image)
        self.close_button.clicked.connect(self.reject)
        self.image_list.itemClicked.connect(self._on_item_clicked)
        self.image_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.delete_button.clicked.connect(self._delete_selected_image)
        self.copy_button.clicked.connect(self._copy_selected_image_url)
        self.preview_button.clicked.connect(self._preview_selected_image)
    
    @staticmethod
    def _get_thumbnail_url(image_data: Dict[str, Any]) -> Optional[str]:
        links = image_data.get('links', {})
        return links.get('thumbnail_url') or links.get('url')
    
    @staticmethod
    def _get_image_url(image_data: Dict[str, Any]) -> Optional[str]:
        return image_data.get('links', {}).get('url')
    
    def _load_images(self):
        for worker in self.image_load_workers:
            worker.quit()
            worker.wait()
        self.image_load_workers.clear()
        
        self.image_list.clear()
        self.current_selected_item = None
        self._hide_action_buttons()
        
        images = self.image_manager.get_all_images()
        
        for image_data in images:
            thumbnail_url = self._get_thumbnail_url(image_data)
            if thumbnail_url:
                item = QListWidgetItem()
                item.setText(os.path.basename(image_data.get('file_path', '')).split('.')[0])
                item.setData(Qt.UserRole, image_data)
                item.setData(Qt.UserRole + 1, image_data.get('file_path'))
                self.image_list.addItem(item)
        
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            image_data = item.data(Qt.UserRole)
            thumbnail_url = self._get_thumbnail_url(image_data)
            if thumbnail_url:
                worker = ImageLoadWorker(i, thumbnail_url)
                worker.image_loaded.connect(self._on_image_loaded)
                self.image_load_workers.append(worker)
                worker.start()
    
    def _on_image_loaded(self, row: int, icon: QIcon):
        if row < self.image_list.count():
            item = self.image_list.item(row)
            if item:
                item.setIcon(icon)
    
    def _on_item_clicked(self, item):
        self.current_selected_item = item
        self._show_action_buttons()
    
    def _on_item_double_clicked(self, item):
        self.current_selected_item = item
        self._preview_selected_image()
    
    def _show_action_buttons(self):
        self.delete_button.show()
        self.delete_cloud_checkbox.show()
        self.copy_button.show()
        self.preview_button.show()
    
    def _hide_action_buttons(self):
        self.delete_button.hide()
        self.delete_cloud_checkbox.hide()
        self.copy_button.hide()
        self.preview_button.hide()
    
    def _clear_image_cache(self):
        cache_dir = get_cache_dir()
        cache_count = 0
        cache_size = 0
        
        if os.path.exists(cache_dir):
            for filename in os.listdir(cache_dir):
                if filename.endswith('.cache'):
                    file_path = os.path.join(cache_dir, filename)
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cache_count += 1
                        cache_size += file_size
                    except Exception:
                        pass
        
        cache_size_mb = cache_size / (1024 * 1024) if cache_size > 0 else 0
        QMessageBox.information(
            self, 
            '缓存清理完成', 
            f'已清理 {cache_count} 个缓存文件\n'
            f'释放空间: {cache_size_mb:.2f} MB'
        )
    
    def _delete_selected_image(self):
        if not self.current_selected_item:
            return
        
        if QMessageBox.question(self, '确认删除', '确定要删除这张图片吗？', 
                             QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            image_data = self.current_selected_item.data(Qt.UserRole)
            file_path = self.current_selected_item.data(Qt.UserRole + 1)
            
            # 根据复选框状态决定是否同时删除云端资源
            delete_cloud = self.delete_cloud_checkbox.isChecked()
            if delete_cloud:
                if self.image_manager.delete_image(file_path, image_data):
                    row = self.image_list.row(self.current_selected_item)
                    self.image_list.takeItem(row)
                    self.current_selected_item = None
                    self._hide_action_buttons()
                    QMessageBox.information(self, '成功', '图片已删除')
                else:
                    QMessageBox.warning(self, '错误', '删除图片失败')
            else:
                if self.image_manager.delete_image(file_path):
                    row = self.image_list.row(self.current_selected_item)
                    self.image_list.takeItem(row)
                    self.current_selected_item = None
                    self._hide_action_buttons()
                    QMessageBox.information(self, '成功', '图片已删除')
                else:
                    QMessageBox.warning(self, '错误', '删除图片失败')
    
    def _copy_selected_image_url(self):
        if not self.current_selected_item:
            return
        
        image_data = self.current_selected_item.data(Qt.UserRole)
        image_url = self._get_image_url(image_data)
        if image_url:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(image_url)
                QMessageBox.information(self, '成功', '链接已复制到剪贴板')
    
    def _upload_image(self):
        from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton
        
        file_path, _ = QFileDialog.getOpenFileName(self, '选择图片', '', '图片文件 (*.jpg *.jpeg *.png *.gif *.webp)')
        if not file_path:
            return
        
        # 创建上传进度对话框
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle('上传中')
        progress_dialog.setGeometry(300, 200, 300, 100)
        progress_layout = QVBoxLayout(progress_dialog)
        
        progress_label = QLabel('正在上传图片，请稍候...')
        progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(progress_label)
        
        # 创建并启动上传线程
        upload_worker = ImageUploadWorker(self.image_manager, file_path)
        
        def on_upload_completed(success, message, image_data):
            progress_dialog.accept()
            if success:
                QMessageBox.information(self, '成功', message)
                # 刷新图片列表
                self._load_images()
            else:
                QMessageBox.warning(self, '警告', message)
        
        upload_worker.upload_completed.connect(on_upload_completed)
        upload_worker.start()
        
        # 显示进度对话框
        progress_dialog.exec_()
    
    def _preview_selected_image(self):
        if not self.current_selected_item:
            return
        
        image_data = self.current_selected_item.data(Qt.UserRole)
        image_url = self._get_image_url(image_data)
        thumbnail_url = self._get_thumbnail_url(image_data)
        if image_url:
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle('图片预览')
            preview_dialog.setGeometry(300, 200, 800, 600)
            preview_layout = QVBoxLayout(preview_dialog)
            
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            preview_layout.addWidget(image_label)
            
            preview_close_btn = QPushButton('关闭')
            preview_close_btn.clicked.connect(preview_dialog.reject)
            preview_layout.addWidget(preview_close_btn)
            
            def update_preview_image(pixmap):
                image_label.setPixmap(pixmap.scaled(
                    self.PREVIEW_WIDTH, 
                    self.PREVIEW_HEIGHT, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
            
            if thumbnail_url:
                try:
                    cache_path = get_cache_path(thumbnail_url)
                    if os.path.exists(cache_path):
                        thumb_pixmap = QPixmap(cache_path)
                        if thumb_pixmap and not thumb_pixmap.isNull():
                            update_preview_image(thumb_pixmap)
                except Exception:
                    pass
            
            preview_worker = PreviewImageLoadWorker(image_url)
            preview_worker.image_loaded.connect(update_preview_image)
            preview_worker.start()
            
            preview_dialog.exec_()
