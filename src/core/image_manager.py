import os
import json
import time
import requests
from typing import Dict, Any, Tuple, Optional

class ImageManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser('~'), '.pyhtml')
        self.picture_dir = os.path.join(self.config_dir, 'picturestemp')
        os.makedirs(self.picture_dir, exist_ok=True)
    
    def save_image_api_token(self, token: str) -> None:
        """保存图片API token"""
        config_path = os.path.join(self.config_dir, 'image_api_config.json')
        config = {'api_token': token}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def load_image_api_token(self) -> str:
        """加载图片API token"""
        config_path = os.path.join(self.config_dir, 'image_api_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('api_token', '')
            except Exception:
                return ''
        return ''
    
    def save_temp_token(self, token: str, expiration: int) -> None:
        """保存临时token"""
        config_path = os.path.join(self.config_dir, 'temp_token.json')
        config = {
            'token': token,
            'expiration': expiration
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def load_temp_token(self) -> Tuple[str, int]:
        """加载临时token"""
        config_path = os.path.join(self.config_dir, 'temp_token.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('token', ''), config.get('expiration', 0)
            except Exception:
                return '', 0
        return '', 0
    
    def get_temp_token(self, force_refresh: bool = False) -> str:
        """获取有效的临时token
        
        Args:
            force_refresh: 是否强制刷新临时token
        """
        import time
        temp_token, expiration = self.load_temp_token()
        current_time = int(time.time())
        
        if force_refresh or not temp_token or current_time >= expiration:
            # 申请新的临时token
            api_token = self.load_image_api_token()
            if not api_token:
                return ''
            
            token_url = 'https://picui.cn/api/v1/images/tokens'
            token_payload = {'num': 1, 'seconds': 3600}
            token_headers = {'Accept': 'application/json', 'Authorization': f'Bearer {api_token}'}
            
            try:
                token_response = requests.post(token_url, json=token_payload, headers=token_headers)
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    if token_data.get('status'):
                        tokens = token_data.get('data', {}).get('tokens', [])
                        if tokens:
                            temp_token = tokens[0].get('token')
                            if temp_token:
                                expiration = current_time + 3600
                                self.save_temp_token(temp_token, expiration)
                                return temp_token
            except Exception:
                pass
        
        return temp_token
    
    def upload_image(self, file_path: str) -> Optional[Dict[str, Any]]:
        """上传图片"""
        temp_token = self.get_temp_token()
        if not temp_token:
            return None
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                data = {'token': temp_token, 'permission': 1}
                
                response = requests.post('https://picui.cn/api/v1/upload', files=files, data=data)
                
                if response.status_code == 401:
                    # 401错误，重新申请临时token
                    temp_token = self.get_temp_token()
                    if not temp_token:
                        return None
                    
                    data = {'token': temp_token, 'permission': 1}
                    response = requests.post('https://picui.cn/api/v1/upload', files=files, data=data)
                
                if response.status_code == 200:
                    data = response.json()
                    print(response.text)
                    if data.get('status'):
                        image_data = data.get('data', {})
                        self.save_picture_info(image_data)
                        return image_data
        except Exception:
            pass
        
        return None
    
    def save_picture_info(self, image_data: Dict[str, Any]) -> None:
        """保存图片信息"""
        timestamp = int(time.time() * 1000)
        file_name = f'picture_{timestamp}.json'
        file_path = os.path.join(self.picture_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(image_data, f, ensure_ascii=False, indent=2)
    
    def get_all_images(self) -> list:
        """获取所有图片信息"""
        images = []
        if os.path.exists(self.picture_dir):
            for file_name in os.listdir(self.picture_dir):
                if file_name.endswith('.json'):
                    file_path = os.path.join(self.picture_dir, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            image_data = json.load(f)
                            image_data['file_path'] = file_path
                            images.append(image_data)
                    except Exception:
                        pass
        return images
    
    def delete_image(self, file_path: str, image_data: Optional[Dict[str, Any]] = None) -> bool:
        """删除图片信息（同时删除云端图片）"""
        delete_success = True
        
        if image_data:
            delete_url = image_data.get('links', {}).get('delete_url')
            if delete_url:
                try:
                    requests.get(delete_url, timeout=10)
                except Exception:
                    delete_success = False
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                delete_success = False
        
        return delete_success
