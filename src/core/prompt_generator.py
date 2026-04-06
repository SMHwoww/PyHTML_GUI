import json
from pathlib import Path
from typing import Any, List, Optional
from .component import ComponentLoader, Component


class PromptGenerator:
    def __init__(self, component_loader: ComponentLoader):
        self.component_loader = component_loader
    
    def get_components_info(self) -> str:
        components = self.component_loader.get_all_components()
        info = []
        
        for comp in components:
            comp_info = {
                'name': comp.name,
                'display_name': comp.display_name,
                'description': comp.config.get('description', ''),
                'fields': []
            }
            
            for field in comp.fields:
                field_info = {
                    'name': field['name'],
                    'type': field['type'],
                    'label': field['label'],
                    'default': field.get('default')
                }
                if 'options' in field:
                    field_info['options'] = field['options']
                if 'min' in field:
                    field_info['min'] = field['min']
                if 'max' in field:
                    field_info['max'] = field['max']
                comp_info['fields'].append(field_info)
            
            info.append(comp_info)
        
        return json.dumps(info, ensure_ascii=False, indent=2)
    
    def generate_system_prompt(self) -> str:
        components_info = self.get_components_info()
        
        return f'''你是一个专业的网页生成助手，专门帮助用户生成 PyHTML 项目配置。

## PyHTML 项目格式规范 (.pyhtml)

```json
{{
  "name": "项目名称（英文，无空格）",
  "title": "页面标题",
  "head_config": {{
    "lang": "zh-CN",
    "meta_tags": [
      {{"name": "charset", "content": "UTF-8"}},
      {{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}}
    ],
    "links": [],
    "scripts": []
  }},
  "components": [
    {{
      "component_name": "组件名称",
      "values": {{
        "字段名": "字段值"
      }}
    }}
  ]
}}
```

## 可用组件列表

{components_info}

## 要求

1. 只返回 JSON 格式的 .pyhtml 配置，不要包含任何其他文本或 markdown 标记
2. 确保使用的组件名称与上面列表中的 name 完全一致
3. 组件字段值要合理且符合字段类型
4. components 数组包含页面所需的组件
5. 不要使用不存在的组件或字段
6. 确保 JSON 格式正确，可以被解析
7. 尽可能多的自定义内容而不是使用默认参数，例如自定义标题、自定义正文、自定义颜色等
8. 应具有大局意识，生成的宽高等参数最后要有较好的视觉效果和协调性
9. 应根据不同的组件类型，生成不同的文本体量，例如article组件需要更多的文本，而image组件则需要更少的文本



用户需求：'''
    
    def generate_component_selection_prompt(self) -> str:
        components_info = self.get_components_info()
        
        return f'''你是一个专业的网页规划助手，负责根据用户需求选择合适的组件。

## 可用组件列表

{components_info}

## 任务

用户会描述他们想要创建的网页需求，你需要：
1. 分析用户需求
2. 从上面的组件列表中选择**必要且充分**的组件
3. 以 JSON 格式返回选择的组件名称列表

## 要求

1. 只返回 JSON 格式，不要包含任何其他文本
2. JSON 格式如下：
   ```json
   {{"selected_components": ["component_name1", "component_name2", ...]}}
   ```
3. 只包含确实需要的组件，不要包含不需要的组件
4. 组件名称必须与上面列表中的 name 字段完全一致

用户需求：'''
    
    def parse_ai_response(self, response: str) -> Optional[dict[str, Any]]:
        try:
            response = response.strip()
            
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            response = response.strip()
            
            data = json.loads(response)
            
            if not isinstance(data, dict):
                raise ValueError('根元素必须是对象')
            
            if 'name' not in data:
                raise ValueError('缺少 name 字段')
            if 'title' not in data:
                raise ValueError('缺少 title 字段')
            if 'components' not in data:
                raise ValueError('缺少 components 字段')
            
            for comp_data in data.get('components', []):
                if 'component_name' not in comp_data:
                    raise ValueError('组件缺少 component_name 字段')
                if 'values' not in comp_data:
                    raise ValueError('组件缺少 values 字段')
                
                comp_name = comp_data['component_name']
                component = self.component_loader.get_component(comp_name)
                if not component:
                    raise ValueError(f'未知组件: {comp_name}')
            
            return data
        except json.JSONDecodeError as e:
            raise Exception(f'JSON 解析失败: {e}')
        except Exception as e:
            raise Exception(f'解析 AI 响应失败: {e}')
    
    def parse_component_selection(self, response: str) -> list:
        try:
            response = response.strip()
            
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            response = response.strip()
            
            data = json.loads(response)
            
            if not isinstance(data, dict):
                raise ValueError('根元素必须是对象')
            
            if 'selected_components' not in data:
                raise ValueError('缺少 selected_components 字段')
            
            selected_components = data['selected_components']
            if not isinstance(selected_components, list):
                raise ValueError('selected_components 必须是数组')
            
            for comp_name in selected_components:
                component = self.component_loader.get_component(comp_name)
                if not component:
                    raise ValueError(f'未知组件: {comp_name}')
            
            return selected_components
        except json.JSONDecodeError as e:
            raise Exception(f'JSON 解析失败: {e}')
        except Exception as e:
            raise Exception(f'解析组件选择失败: {e}')
