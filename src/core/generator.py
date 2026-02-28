import os
from pathlib import Path
from typing import List, Optional
from .component import Component

try:
    from jinja2 import Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
    print('Warning: Jinja2 not installed. Using simple string replacement.')


class HTMLGenerator:
    def __init__(self):
        pass
    
    def _render_template(self, template: str, values: dict) -> str:
        if HAS_JINJA2:
            try:
                jinja_template = Template(template)
                return jinja_template.render(**values)
            except Exception as e:
                print(f'Jinja2 rendering failed: {e}, falling back to simple replacement')
        
        result = template
        for key, value in values.items():
            result = result.replace(f'{{{{ {key} }}}}', str(value))
            result = result.replace(f'{{{{{key}}}}}', str(value))
        return result
    
    def generate_html(self, components: List[Component], title: str = 'pyHTML Page') -> str:
        all_styles = []
        all_scripts = []
        all_html = []
        
        for component in components:
            style = component.get_style()
            if style:
                rendered_style = self._render_template(style, component.values)
                all_styles.append(rendered_style)
            
            script = component.get_script()
            if script:
                all_scripts.append(script)
            
            template = component.get_template()
            if template:
                rendered_html = self._render_template(template, component.values)
                all_html.append(rendered_html)
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="zh-CN">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'    <title>{title}</title>',
        ]
        
        if all_styles:
            html_parts.append('    <style>')
            html_parts.extend(['        ' + line for style in all_styles for line in style.split('\n')])
            html_parts.append('    </style>')
        
        html_parts.extend([
            '</head>',
            '<body>',
        ])
        
        html_parts.extend(all_html)
        
        if all_scripts:
            html_parts.append('    <script>')
            html_parts.extend(['        ' + line for script in all_scripts for line in script.split('\n')])
            html_parts.append('    </script>')
        
        html_parts.extend([
            '</body>',
            '</html>',
        ])
        
        return '\n'.join(html_parts)
    
    def save_html(self, components: List[Component], output_path: str, title: str = 'pyHTML Page'):
        html_content = self.generate_html(components, title)
        output_file = Path(output_path)
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return str(output_file)
        except PermissionError:
            raise PermissionError(f'没有权限写入文件: {output_file}')
        except Exception as e:
            raise Exception(f'保存文件失败: {str(e)}')
