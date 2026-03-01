from src.core import Project, ComponentLoader
from src.utils import get_components_dir
import os

# 初始化组件加载器
loader = ComponentLoader(str(get_components_dir()))
loader.load_builtin_components()

# 创建测试项目
proj = Project('Test')

# 添加一个组件
comp = loader.create_instance('headline')
if comp:
    proj.add_component(comp)
    print(f'Added component: {comp.name}')
else:
    print('Failed to create component')

# 保存项目
save_path = 'test.pyhtml'
proj.save(save_path)
print(f'Project saved to {save_path}')

# 查看保存的文件内容
with open(save_path, 'r', encoding='utf-8') as f:
    content = f.read()
print('Saved file content:')
print(content)

# 加载项目
loaded_proj = Project.load(save_path, loader)
print('\nLoaded project:')
print(f'Name: {loaded_proj.name}')
print(f'Components: {[c.name for c in loaded_proj.components]}')

# 清理测试文件
os.remove(save_path)
print('\nTest completed successfully!')
