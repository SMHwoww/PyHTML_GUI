from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication
import os
import requests
import hashlib
from typing import Dict, Any, Optional
from core.image_manager import ImageManager


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
    upload_completed = pyqtSignal(bool, str)
    
    def __init__(self, image_manager, file_path):
        super().__init__()
        self.image_manager = image_manager
        self.file_path = file_path
    
    def run(self):
        try:
            # 检查是否设置了API token
            api_token = self.image_manager.load_image_api_token()
            if not api_token:
                self.upload_completed.emit(False, '请先在图片设置中设置API token')
                return
            
            # 检查API token是否有效（尝试获取临时token）
            temp_token = self.image_manager.get_temp_token()
            if not temp_token:
                # 强制获取新的临时token
                temp_token = self.image_manager.get_temp_token(force_refresh=True)
                if not temp_token:
                    self.upload_completed.emit(False, 'API token 无效或已过期，请在图片设置中检查并更新')
                    return
            
            # 使用ImageManager上传图片
            image_data = self.image_manager.upload_image(self.file_path)
            if image_data:
                self.upload_completed.emit(True, '图片上传成功')
            else:
                # 再次尝试上传
                temp_token = self.image_manager.get_temp_token(force_refresh=True)
                if temp_token:
                    image_data = self.image_manager.upload_image(self.file_path)
                    if image_data:
                        self.upload_completed.emit(True, '图片上传成功')
                    else:
                        self.upload_completed.emit(False, '上传失败: 可能是临时token过期或网络问题')
                else:
                    self.upload_completed.emit(False, '上传失败: 无法获取临时token')
        except Exception as e:
            self.upload_completed.emit(False, f'上传失败: {str(e)}')


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
        
        def on_upload_completed(success, message):
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
