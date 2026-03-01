import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import requests


class AIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = 'qwen-max'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
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
                    return config.get('api_key')
            except Exception as e:
                print(f'Failed to load API key: {e}')
        return None
    
    def save_config(self, api_key: str, model: str = 'qwen-max'):
        self.api_key = api_key
        self.model = model
        config = {'api_key': api_key, 'model': model}
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
        
        if max_tokens:
            data['max_tokens'] = max_tokens
        
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
