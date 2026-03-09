import os
import time
import threading
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from PIL import Image, ImageTk
import dashscope
from dashscope import MultiModalConversation
from dashscope import ImageSynthesis
from dashscope import VideoSynthesis
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message
from http import HTTPStatus


# 配置API URL
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

# API Key (用户已硬编码)


class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI创作工具 - 基于阿里云DashScope")
        self.root.geometry("1000x850")
        self.root.resizable(True, True)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题
        self.title_label = ttk.Label(self.main_frame, text="AI创作工具", font=("微软雅黑", 16, "bold"))
        self.title_label.pack(fill=tk.X, pady=10)
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建图片生成标签页
        self.image_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.image_tab, text="图片生成")
        
        # 创建视频生成标签页
        self.video_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.video_tab, text="视频生成")
        
        # 初始化图片生成界面
        self._init_image_tab()
        
        # 初始化视频生成界面
        self._init_video_tab()
        
        # 底部状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # 配置样式
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", font=("微软雅黑", 10, "bold"))
    
    def _init_image_tab(self):
        """初始化图片生成标签页"""
        # 中间内容框架
        content_frame = ttk.Frame(self.image_tab)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 左侧输入区域
        input_frame = ttk.LabelFrame(content_frame, text="提示词输入", padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 提示词文本框
        self.image_prompt_text = scrolledtext.ScrolledText(input_frame, height=12, width=50, font=("微软雅黑", 10))
        self.image_prompt_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 默认提示词
        default_prompt = "一间有着精致窗户的花店，漂亮的木质门，摆放着花朵"
        self.image_prompt_text.insert(tk.END, default_prompt)
        
        # 模型选择区域
        model_frame = ttk.LabelFrame(input_frame, text="模型选择", padding="10")
        model_frame.pack(fill=tk.X, pady=5)
        
        # 模型下拉框
        model_inner_frame = ttk.Frame(model_frame)
        model_inner_frame.pack(fill=tk.X)
        
        ttk.Label(model_inner_frame, text="模型:").pack(side=tk.LEFT, padx=5)
        self.image_model_var = tk.StringVar(value="wanx2.0-t2i-turbo")
        self.image_model_combobox = ttk.Combobox(model_inner_frame, textvariable=self.image_model_var, width=30)
        self.image_model_combobox['values'] = [
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
        ]
        self.image_model_combobox.pack(side=tk.LEFT, padx=5)
        self.image_model_combobox.config(state="readonly")
        
        # 宽高设置区域
        size_frame = ttk.LabelFrame(input_frame, text="图片尺寸", padding="10")
        size_frame.pack(fill=tk.X, pady=5)
        
        # 宽高输入控件
        size_inner_frame = ttk.Frame(size_frame)
        size_inner_frame.pack(fill=tk.X)
        
        # 宽度输入
        ttk.Label(size_inner_frame, text="宽度:").pack(side=tk.LEFT, padx=5)
        self.image_width_var = tk.StringVar(value="1280")
        self.image_width_entry = ttk.Entry(size_inner_frame, textvariable=self.image_width_var, width=10)
        self.image_width_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(size_inner_frame, text="px").pack(side=tk.LEFT, padx=5)
        
        # 分隔符
        ttk.Label(size_inner_frame, text="×").pack(side=tk.LEFT, padx=5)
        
        # 高度输入
        ttk.Label(size_inner_frame, text="高度:").pack(side=tk.LEFT, padx=5)
        self.image_height_var = tk.StringVar(value="720")
        self.image_height_entry = ttk.Entry(size_inner_frame, textvariable=self.image_height_var, width=10)
        self.image_height_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(size_inner_frame, text="px").pack(side=tk.LEFT, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 生成按钮
        self.image_generate_button = ttk.Button(button_frame, text="生成图片", command=self.generate_image, style="Accent.TButton")
        self.image_generate_button.pack(side=tk.LEFT, padx=5)
        
        # 清空按钮
        self.image_clear_button = ttk.Button(button_frame, text="清空", command=self.clear_image_prompt)
        self.image_clear_button.pack(side=tk.LEFT, padx=5)
        
        # 右侧图片显示区域
        image_frame = ttk.LabelFrame(content_frame, text="生成结果", padding="10")
        image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 图片显示标签
        self.image_label = ttk.Label(image_frame, text="生成的图片将显示在这里", anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # 线程控制
        self.image_is_generating = False
        self.image_current_thread = None
        
        # 当前显示的图片路径
        self.current_image_path = None
    
    def _init_video_tab(self):
        """初始化视频生成标签页"""
        # 中间内容框架
        content_frame = ttk.Frame(self.video_tab)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 左侧输入区域
        input_frame = ttk.LabelFrame(content_frame, text="提示词输入", padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 提示词文本框
        self.video_prompt_text = scrolledtext.ScrolledText(input_frame, height=8, width=50, font=("微软雅黑", 10))
        self.video_prompt_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 默认提示词
        default_video_prompt = "一幅史诗级可爱的场景。一只小巧可爱的卡通小猫将军，身穿细节精致的金色盔甲，头戴一个稍大的头盔，勇敢地站在悬崖上。"
        self.video_prompt_text.insert(tk.END, default_video_prompt)
        
        # 模型选择区域
        model_frame = ttk.LabelFrame(input_frame, text="模型选择", padding="10")
        model_frame.pack(fill=tk.X, pady=5)
        
        # 模型下拉框
        model_inner_frame = ttk.Frame(model_frame)
        model_inner_frame.pack(fill=tk.X)
        
        ttk.Label(model_inner_frame, text="模型:").pack(side=tk.LEFT, padx=5)
        self.video_model_var = tk.StringVar(value="wan2.6-t2v")
        self.video_model_combobox = ttk.Combobox(model_inner_frame, textvariable=self.video_model_var, width=30)
        self.video_model_combobox['values'] = [
            "wan2.6-t2v",
            "wan2.6-t2v-us",
            "wan2.5-t2v-preview",
            "wan2.2-t2v-plus",
            "wanx2.1-t2v-turbo",
            "wanx2.1-t2v-plus"
        ]
        self.video_model_combobox.pack(side=tk.LEFT, padx=5)
        self.video_model_combobox.config(state="readonly")
        
        # 尺寸设置区域
        size_frame = ttk.LabelFrame(input_frame, text="视频尺寸", padding="10")
        size_frame.pack(fill=tk.X, pady=5)
        
        size_inner_frame = ttk.Frame(size_frame)
        size_inner_frame.pack(fill=tk.X)
        
        self.video_size_var = tk.StringVar(value="1280*720")
        self.video_size_combobox = ttk.Combobox(size_inner_frame, textvariable=self.video_size_var, width=20)
        self.video_size_combobox['values'] = [
            "1280*720",
            "1920*1080",
            "720*1280",
            "1080*1920",
            "960*960",
            "1440*1440"
        ]
        self.video_size_combobox.pack(side=tk.LEFT, padx=5)
        self.video_size_combobox.config(state="readonly")
        
        # 时长设置区域
        duration_frame = ttk.LabelFrame(input_frame, text="视频时长", padding="10")
        duration_frame.pack(fill=tk.X, pady=5)
        
        duration_inner_frame = ttk.Frame(duration_frame)
        duration_inner_frame.pack(fill=tk.X)
        
        ttk.Label(duration_inner_frame, text="时长:").pack(side=tk.LEFT, padx=5)
        self.video_duration_var = tk.StringVar(value="10")
        self.video_duration_combobox = ttk.Combobox(duration_inner_frame, textvariable=self.video_duration_var, width=10)
        self.video_duration_combobox['values'] = ["5", "10", "15"]
        self.video_duration_combobox.pack(side=tk.LEFT, padx=5)
        self.video_duration_combobox.config(state="readonly")
        ttk.Label(duration_inner_frame, text="秒").pack(side=tk.LEFT, padx=5)
        
        # 音频URL区域
        audio_frame = ttk.LabelFrame(input_frame, text="音频URL (可选)", padding="10")
        audio_frame.pack(fill=tk.X, pady=5)
        
        audio_inner_frame = ttk.Frame(audio_frame)
        audio_inner_frame.pack(fill=tk.X)
        
        self.video_audio_url_var = tk.StringVar()
        self.video_audio_url_entry = ttk.Entry(audio_inner_frame, textvariable=self.video_audio_url_var)
        self.video_audio_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 按钮框架
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 生成按钮
        self.video_generate_button = ttk.Button(button_frame, text="生成视频", command=self.generate_video, style="Accent.TButton")
        self.video_generate_button.pack(side=tk.LEFT, padx=5)
        
        # 清空按钮
        self.video_clear_button = ttk.Button(button_frame, text="清空", command=self.clear_video_prompt)
        self.video_clear_button.pack(side=tk.LEFT, padx=5)
        
        # 右侧视频显示区域
        video_frame = ttk.LabelFrame(content_frame, text="生成结果", padding="10")
        video_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # 视频信息显示标签
        self.video_info_label = ttk.Label(video_frame, text="生成的视频信息将显示在这里", anchor=tk.CENTER, justify=tk.CENTER)
        self.video_info_label.pack(fill=tk.BOTH, expand=True)
        
        # 下载按钮
        self.video_download_button = ttk.Button(video_frame, text="下载视频", command=self.download_video, state=tk.DISABLED)
        self.video_download_button.pack(fill=tk.X, pady=5)
        
        # 线程控制
        self.video_is_generating = False
        self.video_current_thread = None
        
        # 当前视频URL
        self.current_video_url = None
    
    def clear_image_prompt(self):
        """清空图片提示词文本框"""
        self.image_prompt_text.delete(1.0, tk.END)
    
    def clear_video_prompt(self):
        """清空视频提示词文本框"""
        self.video_prompt_text.delete(1.0, tk.END)
    
    def generate_image(self):
        """生成图片（启动后台线程）"""
        if self.image_is_generating:
            return
        
        prompt = self.image_prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            self.status_var.set("错误：请输入提示词")
            return
        
        # 获取并验证宽高值
        try:
            width = int(self.image_width_var.get().strip())
            height = int(self.image_height_var.get().strip())
            
            if width <= 0 or height <= 0:
                self.status_var.set("错误：宽高值必须为正整数")
                return
            
            if width > 4096 or height > 4096:
                self.status_var.set("错误：宽高值不能超过4096")
                return
            
            size = f"{width}*{height}"
            
            # 对wan系列模型进行尺寸限制
            model = self.image_model_var.get()
            if model.startswith("wan"):
                allowed_sizes = ['768*768', '576*1024', '1024*576', '1024*1024', '720*1280', '1280*720', '864*1152', '1152*864']
                if size not in allowed_sizes:
                    self.status_var.set(f"错误：wan系列模型只支持以下尺寸：{', '.join(allowed_sizes)}")
                    return
        except ValueError:
            self.status_var.set("错误：宽高值必须为整数")
            return
        
        # 禁用生成按钮
        self.image_generate_button.config(state=tk.DISABLED)
        self.status_var.set("生成中...")
        self.image_is_generating = True
        
        # 获取选中的模型
        model = self.image_model_var.get()
        print(f"使用模型: {model}, 图片尺寸: {size}")
        
        # 启动后台线程
        self.image_current_thread = threading.Thread(target=self._generate_image_thread, args=(prompt, size, model))
        self.image_current_thread.daemon = True
        self.image_current_thread.start()
    
    def _generate_image_thread(self, prompt, size, model):
        """后台线程：生成图片"""
        sync_success = False
        
        try:
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"text": prompt}
                    ]
                }
            ]
            
            # 调用API
            self.root.after(0, lambda: self.status_var.set("调用API中..."))
            print(f"尝试同步调用模型 {model}")
            print(f"当前API URL: {dashscope.base_http_api_url}")
            
            # 根据模型类型选择合适的API调用方式
            if model.startswith("wan"):
                # 所有wan系列模型使用专门的图像生成API
                print(f"使用图像生成API调用wan系列模型 {model}")
                
                try:
                    if model.startswith("wan2.6"):
                        # wan2.6 使用 ImageGeneration
                        message_obj = Message(
                            role="user",
                            content=[
                                {'text': prompt}
                            ]
                        )
                        response = ImageGeneration.call(
                            api_key=api_key,
                            model=model,
                            messages=[message_obj],
                            negative_prompt="低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。",
                            prompt_extend=True,
                            watermark=False,
                            n=1,
                            size=size
                        )
                        
                        # 处理 wan2.6 响应
                        if response.status_code == 200:
                            # 提取图像URL
                            self.root.after(0, lambda: self.status_var.set("解析响应中..."))
                            image_url = self._extract_image_url_wan26(response)
                            if image_url:
                                # 下载图片
                                self.root.after(0, lambda: self.status_var.set("下载图片中..."))
                                success, result = self._download_image(image_url)
                                if success:
                                    # 显示图片
                                    self.root.after(0, lambda: self._display_image(result))
                                    self.root.after(0, lambda: self.status_var.set(f"生成完成！图片已保存到：{result}"))
                                    sync_success = True
                                else:
                                    self.root.after(0, lambda: self.status_var.set(f"下载失败：{result}"))
                            else:
                                self.root.after(0, lambda: self.status_var.set("错误：无法从响应中提取图像URL"))
                        else:
                            error_msg = f"API错误：{response.code} - {response.message}"
                            detailed_error = f"[wan2.6] API调用失败，状态码: {response.status_code} 错误信息: {error_msg}"
                            print(detailed_error)
                            self.root.after(0, lambda: self.status_var.set(error_msg))
                    else:
                        # wan2.5, wan2.2, wanx2.1, wanx2.0 及以下版本使用 ImageSynthesis
                        response = ImageSynthesis.call(
                            api_key=api_key,
                            model=model,
                            prompt=prompt,
                            negative_prompt="低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。",
                            n=1,
                            size=size,
                            prompt_extend=True,
                            watermark=False
                        )
                        
                        # 处理 ImageSynthesis 响应
                        if response.status_code == 200:
                            # 提取图像URL
                            self.root.after(0, lambda: self.status_var.set("解析响应中..."))
                            image_url = self._extract_image_url_imagesynthesis(response)
                            if image_url:
                                # 下载图片
                                self.root.after(0, lambda: self.status_var.set("下载图片中..."))
                                success, result = self._download_image(image_url)
                                if success:
                                    # 显示图片
                                    self.root.after(0, lambda: self._display_image(result))
                                    self.root.after(0, lambda: self.status_var.set(f"生成完成！图片已保存到：{result}"))
                                    sync_success = True
                                else:
                                    self.root.after(0, lambda: self.status_var.set(f"下载失败：{result}"))
                            else:
                                self.root.after(0, lambda: self.status_var.set("错误：无法从响应中提取图像URL"))
                        else:
                            error_msg = f"API错误：{response.code} - {response.message}"
                            detailed_error = f"[ImageSynthesis] API调用失败，状态码: {response.status_code} 错误信息: {error_msg}"
                            print(detailed_error)
                            self.root.after(0, lambda: self.status_var.set(error_msg))
                except Exception as e:
                    error_msg = f"图像生成API调用失败：{str(e)}"
                    detailed_error = f"[图像生成API] 异常：{str(e)}"
                    print(detailed_error)
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    sync_success = False
            
            else:
                # 非wan系列模型，根据类型选择合适的API
                print(f"使用MultiModalConversation调用非wan系列模型 {model}")
                
                try:
                    # 其他模型使用 MultiModalConversation
                    response = MultiModalConversation.call(
                        api_key=api_key,
                        model=model,
                        messages=messages,
                        result_format='message',
                        stream=False,
                        watermark=False,
                        prompt_extend=True,
                        negative_prompt="低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。",
                        size=size
                    )
                    
                    # 处理 MultiModalConversation 响应
                    if response.status_code == 200:
                        # 提取图像URL
                        self.root.after(0, lambda: self.status_var.set("解析响应中..."))
                        image_url = self._extract_image_url(response)
                        if image_url:
                            # 下载图片
                            self.root.after(0, lambda: self.status_var.set("下载图片中..."))
                            success, result = self._download_image(image_url)
                            if success:
                                # 显示图片
                                self.root.after(0, lambda: self._display_image(result))
                                self.root.after(0, lambda: self.status_var.set(f"生成完成！图片已保存到：{result}"))
                                sync_success = True
                            else:
                                self.root.after(0, lambda: self.status_var.set(f"下载失败：{result}"))
                        else:
                            self.root.after(0, lambda: self.status_var.set("错误：无法从响应中提取图像URL"))
                    else:
                        error_msg = f"API错误：{response.code} - {response.message}"
                        detailed_error = f"[MultiModal] API调用失败，状态码: {response.status_code} 错误信息: {error_msg}"
                        print(detailed_error)
                        self.root.after(0, lambda: self.status_var.set(error_msg))
                except Exception as e:
                    error_msg = f"MultiModalConversation调用失败：{str(e)}"
                    detailed_error = f"[MultiModalConversation] 异常：{str(e)}"
                    print(detailed_error)
                    self.root.after(0, lambda: self.status_var.set(error_msg))
                    sync_success = False
            
        except Exception as e:
            error_msg = f"生成失败：{str(e)}"
            detailed_error = f"[生成任务] 异常：{str(e)}"
            print(detailed_error)
            self.root.after(0, lambda: self.status_var.set(error_msg))
        
        # 重新启用按钮
        self.root.after(0, lambda: self.image_generate_button.config(state=tk.NORMAL))
        self.image_is_generating = False
    
    def generate_video(self):
        """生成视频（启动后台线程）"""
        if self.video_is_generating:
            return
        
        prompt = self.video_prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            self.status_var.set("错误：请输入提示词")
            return
        
        # 获取参数
        model = self.video_model_var.get()
        size = self.video_size_var.get()
        duration = int(self.video_duration_var.get())
        audio_url = self.video_audio_url_var.get().strip()
        
        # 禁用生成按钮
        self.video_generate_button.config(state=tk.DISABLED)
        self.video_download_button.config(state=tk.DISABLED)
        self.status_var.set("生成中...")
        self.video_is_generating = True
        
        # 启动后台线程
        self.video_current_thread = threading.Thread(target=self._generate_video_thread, args=(prompt, model, size, duration, audio_url))
        self.video_current_thread.daemon = True
        self.video_current_thread.start()
    
    def _generate_video_thread(self, prompt, model, size, duration, audio_url):
        """后台线程：生成视频"""
        try:
            self.root.after(0, lambda: self.status_var.set("提交任务中..."))
            print(f"提交视频生成任务，模型: {model}")
            
            # 准备参数
            params = {
                'api_key': api_key,
                'model': model,
                'prompt': prompt,
                'size': size,
                'duration': duration,
                'negative_prompt': '',
                'prompt_extend': True,
                'watermark': False,
                'seed': 12345
            }
            
            # 添加音频URL（如果有）
            if audio_url:
                params['audio_url'] = audio_url
            
            # 调用API
            rsp = VideoSynthesis.call(**params)
            print(rsp)
            
            if rsp.status_code == HTTPStatus.OK:
                # 提交成功，开始轮询任务状态
                task_id = rsp.output.task_id
                self.root.after(0, lambda: self.status_var.set(f"任务已提交，ID: {task_id[:10]}... 处理中"))
                print(f"任务ID: {task_id}")
                
                # 轮询任务状态
                while True:
                    time.sleep(5)  # 每5秒查询一次
                    task_rsp = VideoSynthesis.call(
                        api_key=api_key,
                        model=model,
                        task_id=task_id
                    )
                    print(f"任务状态查询结果: {task_rsp}")
                    task_status = task_rsp.output.task_status
                    
                    if task_status == 'SUCCEEDED':
                        video_url = task_rsp.output.video_url
                        self.current_video_url = video_url
                        
                        self.root.after(0, lambda: self._show_video_result(task_rsp))
                        self.root.after(0, lambda: self.status_var.set("视频生成完成！"))
                        self.root.after(0, lambda: self.video_download_button.config(state=tk.NORMAL))
                        break
                    elif task_status == 'FAILED':
                        error_msg = f"任务失败: {task_rsp.message}"
                        self.root.after(0, lambda: self.status_var.set(error_msg))
                        break
                    elif task_status == 'CANCELED':
                        self.root.after(0, lambda: self.status_var.set("任务已取消"))
                        break
                    else:
                        # PENDING 或 RUNNING
                        self.root.after(0, lambda: self.status_var.set(f"任务状态: {task_status}..."))
            else:
                error_msg = f"提交失败: {rsp.code} - {rsp.message}"
                self.root.after(0, lambda: self.status_var.set(error_msg))
        
        except Exception as e:
            error_msg = f"生成失败：{str(e)}"
            self.root.after(0, lambda: self.status_var.set(error_msg))
            print(f"视频生成异常: {str(e)}")
        
        # 重新启用按钮
        self.root.after(0, lambda: self.video_generate_button.config(state=tk.NORMAL))
        self.video_is_generating = False
    
    def _show_video_result(self, task_rsp):
        """显示视频生成结果"""
        video_url = task_rsp.output.video_url
        info_text = f"视频生成成功！\n\n任务ID: {task_rsp.output.task_id}\n视频URL:\n{video_url}\n\n(URL有效期24小时，请及时下载)"
        self.video_info_label.config(text=info_text)
    
    def download_video(self):
        """下载视频"""
        if not self.current_video_url:
            self.status_var.set("错误：没有可下载的视频")
            return
        
        try:
            # 让用户选择保存位置
            default_filename = f"generated_video_{int(time.time())}.mp4"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".mp4",
                initialfile=default_filename,
                filetypes=[("MP4视频", "*.mp4"), ("所有文件", "*.*")]
            )
            
            if not file_path:
                return
            
            self.status_var.set("下载中...")
            
            # 下载视频
            response = requests.get(self.current_video_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = int(downloaded_size / total_size * 100)
                            self.root.after(0, lambda p=progress: self.status_var.set(f"下载中... {p}%"))
            
            self.status_var.set(f"下载完成！视频已保存到：{file_path}")
        
        except Exception as e:
            self.status_var.set(f"下载失败：{str(e)}")
            print(f"下载视频异常: {str(e)}")
    
    def _extract_image_url(self, response):
        """从API响应中提取图像URL"""
        try:
            if hasattr(response, 'output') and response.output:
                choices = response.output.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    content = message.get('content', [])
                    if content:
                        image_item = content[0]
                        if 'image' in image_item:
                            return image_item['image']
            return None
        except Exception as e:
            print(f"提取URL失败：{e}")
            return None
    
    def _extract_image_url_wan26(self, response):
        """从wan2.6模型响应中提取图像URL"""
        try:
            if hasattr(response, 'output') and response.output:
                choices = response.output.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    content = message.get('content', [])
                    if content:
                        for item in content:
                            if 'image' in item:
                                return item['image']
            return None
        except Exception as e:
            print(f"提取wan2.6 URL失败：{e}")
            return None
    
    def _extract_image_url_imagesynthesis(self, response):
        """从ImageSynthesis响应中提取图像URL"""
        try:
            if hasattr(response, 'output') and response.output:
                results = response.output.get('results', [])
                if results:
                    for result in results:
                        if 'url' in result:
                            return result['url']
            return None
        except Exception as e:
            print(f"提取ImageSynthesis URL失败：{e}")
            return None
    
    def _download_image(self, image_url):
        """下载图片到当前文件夹"""
        try:
            # 生成文件名
            filename = f"generated_image_{int(time.time())}.png"
            save_path = os.path.join(os.getcwd(), filename)
            
            # 下载图片
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # 保存图片
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True, save_path
        except Exception as e:
            return False, str(e)
    
    def _display_image(self, image_path):
        """在界面中显示图片"""
        try:
            # 保存当前图片路径
            self.current_image_path = image_path
            
            # 打开图片
            image = Image.open(image_path)
            
            # 获取标签大小
            label_width = self.image_label.winfo_width() or 600
            label_height = self.image_label.winfo_height() or 500
            
            # 调整图片尺寸
            resized_image = self._resize_image(image, label_width, label_height)
            
            # 转换为Tkinter PhotoImage
            photo = ImageTk.PhotoImage(resized_image)
            
            # 显示图片
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # 保持引用，避免被垃圾回收
            
            # 绑定双击事件
            self.image_label.bind("<Double-1>", lambda e: self._show_fullscreen())
            
            return True
        except Exception as e:
            error_msg = f"显示图片失败：{str(e)}"
            self.status_var.set(error_msg)
            return False
    
    def _resize_image(self, image, max_width, max_height):
        """调整图片尺寸"""
        width, height = image.size
        ratio = min(max_width/width, max_height/height, 1)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        return image.resize((new_width, new_height), Image.LANCZOS)
    
    def _show_fullscreen(self):
        """全屏显示图片"""
        if not self.current_image_path:
            self.status_var.set("错误：没有可显示的图片")
            return
        
        try:
            # 创建全屏窗口
            fullscreen_window = tk.Toplevel(self.root)
            fullscreen_window.title("全屏图片")
            fullscreen_window.configure(bg='black')
            
            # 跨平台全屏实现
            try:
                # 设置全屏属性
                fullscreen_window.attributes('-fullscreen', True)
                # 对于Windows和Linux，去除窗口装饰
                if os.name in ('nt', 'posix'):
                    fullscreen_window.overrideredirect(True)
            except Exception as attr_error:
                # 某些平台可能不支持某些属性，使用替代方案
                print(f"设置全屏属性失败：{attr_error}，使用替代方案")
                # 获取屏幕尺寸并手动设置窗口大小
                screen_width = fullscreen_window.winfo_screenwidth()
                screen_height = fullscreen_window.winfo_screenheight()
                fullscreen_window.geometry(f"{screen_width}x{screen_height}+0+0")
                fullscreen_window.attributes('-topmost', True)
            
            # 绑定退出事件
            def exit_fullscreen(event=None):
                """退出全屏模式"""
                try:
                    fullscreen_window.destroy()
                except Exception as destroy_error:
                    print(f"销毁窗口失败：{destroy_error}")
            
            # 绑定ESC键和鼠标点击退出
            fullscreen_window.bind('<Escape>', exit_fullscreen)
            
            # 加载图片
            try:
                image = Image.open(self.current_image_path)
            except Exception as img_error:
                error_msg = f"加载图片失败：{str(img_error)}"
                self.status_var.set(error_msg)
                fullscreen_window.destroy()
                return
            
            # 获取屏幕尺寸
            try:
                screen_width = fullscreen_window.winfo_screenwidth()
                screen_height = fullscreen_window.winfo_screenheight()
            except Exception as screen_error:
                # 如果获取屏幕尺寸失败，使用默认值
                print(f"获取屏幕尺寸失败：{screen_error}，使用默认值")
                screen_width, screen_height = 1920, 1080
            
            # 优化图片尺寸调整
            try:
                # 调整图片尺寸，考虑性能和显示效果
                # 对于全屏显示，我们使用与桌面适应类似的策略：保持比例，填满屏幕，不裁剪
                width, height = image.size
                # 计算宽高比
                img_ratio = width / height
                screen_ratio = screen_width / screen_height
                
                # 确定调整方式
                if img_ratio > screen_ratio:
                    # 图片更宽，以宽度为基准
                    new_width = screen_width
                    new_height = int(new_width / img_ratio)
                else:
                    # 图片更高，以高度为基准
                    new_height = screen_height
                    new_width = int(new_height * img_ratio)
                
                # 调整图片尺寸
                resized_image = image.resize((new_width, new_height), Image.LANCZOS)
            except Exception as resize_error:
                error_msg = f"调整图片尺寸失败：{str(resize_error)}"
                self.status_var.set(error_msg)
                fullscreen_window.destroy()
                return
            
            # 转换为Tkinter PhotoImage
            try:
                photo = ImageTk.PhotoImage(resized_image)
            except Exception as photo_error:
                error_msg = f"创建图片对象失败：{str(photo_error)}"
                self.status_var.set(error_msg)
                fullscreen_window.destroy()
                return
            
            # 创建标签显示图片
            try:
                # 创建标签
                image_label = ttk.Label(fullscreen_window, image=photo, background='black')
                
                # 计算居中位置
                img_width, img_height = resized_image.size
                x = (screen_width - img_width) // 2
                y = (screen_height - img_height) // 2
                
                # 使用place布局实现居中显示
                image_label.place(x=x, y=y, width=img_width, height=img_height)
                image_label.image = photo  # 保持引用，避免被垃圾回收
                
                # 绑定鼠标点击退出
                image_label.bind('<Button-1>', exit_fullscreen)
                
                # 确保窗口获得焦点
                fullscreen_window.focus_set()
            except Exception as label_error:
                error_msg = f"创建显示标签失败：{str(label_error)}"
                self.status_var.set(error_msg)
                fullscreen_window.destroy()
                return
            
        except Exception as e:
            error_msg = f"全屏显示失败：{str(e)}"
            self.status_var.set(error_msg)
            # 确保窗口被销毁
            try:
                if 'fullscreen_window' in locals():
                    fullscreen_window.destroy()
            except:
                pass

if __name__ == "__main__":
    # 创建并运行应用
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
