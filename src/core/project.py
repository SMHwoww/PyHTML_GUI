import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from .component import Component


class Project:
    def __init__(self, name: str = 'Untitled'):
        self.name = name
        self.title = name
        self.components: List[Component] = []
        self.file_path: Optional[str] = None
        self.head_config = {
            'lang': 'zh-CN',
            'meta_tags': [
                {'name': 'charset', 'content': 'UTF-8'},
                {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}
            ],
            'links': [],
            'scripts': []
        }
    
    def add_component(self, component: Component, index: Optional[int] = None):
        if index is None:
            self.components.append(component)
        else:
            self.components.insert(index, component)
    
    def remove_component(self, index: int) -> Optional[Component]:
        if 0 <= index < len(self.components):
            return self.components.pop(index)
        return None
    
    def move_component(self, from_index: int, to_index: int):
        if 0 <= from_index < len(self.components) and 0 <= to_index < len(self.components):
            component = self.components.pop(from_index)
            self.components.insert(to_index, component)
    
    def get_component(self, index: int) -> Optional[Component]:
        if 0 <= index < len(self.components):
            return self.components[index]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'title': self.title,
            'head_config': self.head_config,
            'components': [comp.to_dict() for comp in self.components]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        project = cls(data.get('name', 'Untitled'))
        project.title = data.get('title', project.name)
        project.head_config = data.get('head_config', {
            'lang': 'zh-CN',
            'meta_tags': [
                {'name': 'charset', 'content': 'UTF-8'},
                {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}
            ],
            'links': [],
            'scripts': []
        })
        for comp_data in data.get('components', []):
            try:
                component = Component.from_dict(comp_data)
                project.components.append(component)
            except Exception as e:
                print(f'Failed to load component: {e}')
        return project
    
    def save(self, file_path: Optional[str] = None):
        if file_path:
            self.file_path = file_path
        if not self.file_path:
            raise ValueError('No file path specified')
        
        data = self.to_dict()
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return self.file_path
    
    @classmethod
    def load(cls, file_path: str) -> 'Project':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        project = cls.from_dict(data)
        project.file_path = file_path
        return project
