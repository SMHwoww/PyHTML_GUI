import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class Component:
    def __init__(self, component_dir: str):
        self.component_dir = Path(component_dir)
        self.config = self._load_config()
        self.name = self.config.get('name')
        self.display_name = self.config.get('display_name')
        self.fields = self.config.get('fields', [])
        self.values = self._get_default_values()
        
    def _load_config(self) -> Dict[str, Any]:
        config_path = self.component_dir / 'config.json'
        if not config_path.exists():
            raise FileNotFoundError(f'config.json not found in {self.component_dir}')
        
        # 尝试使用GBK编码读取
        try:
            with open(config_path, 'r', encoding='gbk') as f:
                return json.load(f)
        except Exception:
            # GBK失败，尝试使用UTF-8编码
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                raise Exception(f'Failed to load config.json with both GBK and UTF-8 encoding: {e}')
    
    def _get_default_values(self) -> Dict[str, Any]:
        values = {}
        for field in self.fields:
            values[field['name']] = field.get('default')
        return values
    
    def set_value(self, field_name: str, value: Any):
        if field_name in self.values:
            self.values[field_name] = value
    
    def get_value(self, field_name: str) -> Any:
        return self.values.get(field_name)
    
    def get_template(self) -> str:
        template_path = self.component_dir / 'template.html'
        if template_path.exists():
            return self._read_file_with_encoding(template_path)
        return ''
    
    def get_style(self) -> str:
        style_path = self.component_dir / 'style.css'
        if style_path.exists():
            return self._read_file_with_encoding(style_path)
        return ''
    
    def get_script(self) -> str:
        script_path = self.component_dir / 'script.js'
        if script_path.exists():
            return self._read_file_with_encoding(script_path)
        return ''
    
    def _read_file_with_encoding(self, file_path: Path) -> str:
        """读取文件，尝试使用GBK和UTF-8编码"""
        # 尝试使用GBK编码读取
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()
        except Exception:
            # GBK失败，尝试使用UTF-8编码
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f'Failed to read {file_path} with both GBK and UTF-8 encoding: {e}')
                return ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'component_name': self.name,
            'component_dir': str(self.component_dir),
            'values': self.values
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        component = cls(data['component_dir'])
        component.values = data['values']
        return component


class ComponentLoader:
    def __init__(self, components_dir: Optional[str] = None):
        self.components_dir = Path(components_dir) if components_dir else None
        self._components: Dict[str, Component] = {}
        
    def load_builtin_components(self):
        if self.components_dir and self.components_dir.exists():
            for item in self.components_dir.iterdir():
                if item.is_dir() and (item / 'config.json').exists():
                    try:
                        component = Component(str(item))
                        self._components[component.name] = component
                    except Exception as e:
                        print(f'Failed to load component {item}: {e}')
    
    def load_component(self, component_dir: str) -> Optional[Component]:
        try:
            component = Component(component_dir)
            self._components[component.name] = component
            return component
        except Exception as e:
            print(f'Failed to load component from {component_dir}: {e}')
            return None
    
    def get_component(self, name: str) -> Optional[Component]:
        return self._components.get(name)
    
    def get_all_components(self) -> List[Component]:
        return list(self._components.values())
    
    def create_instance(self, name: str) -> Optional[Component]:
        template = self.get_component(name)
        if template:
            return Component(str(template.component_dir))
        return None
