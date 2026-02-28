import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core import Component, ComponentLoader, HTMLGenerator, Project
from src.utils import get_components_dir


def test_component_loader():
    print('=' * 60)
    print('测试组件加载器')
    print('=' * 60)
    
    loader = ComponentLoader(str(get_components_dir()))
    loader.load_builtin_components()
    
    components = loader.get_all_components()
    print(f'加载了 {len(components)} 个组件')
    
    for comp in components:
        print(f'  - {comp.display_name} ({comp.name})')
        print(f'    字段: {[f["name"] for f in comp.fields]}')
    
    print()
    return loader


def test_html_generation(loader):
    print('=' * 60)
    print('测试HTML生成')
    print('=' * 60)
    
    project = Project('测试项目')
    
    marquee = loader.create_instance('marquee')
    if marquee:
        marquee.set_value('text', '欢迎使用pyHTML！这是一个测试页面。')
        project.add_component(marquee)
        print('添加了走马灯组件')
    
    headline = loader.create_instance('headline')
    if headline:
        headline.set_value('text', '我的第一个报纸页面')
        project.add_component(headline)
        print('添加了标题组件')
    
    generator = HTMLGenerator()
    html = generator.generate_html(project.components, project.title)
    
    output_path = Path(__file__).parent / 'test_output.html'
    generator.save_html(project.components, str(output_path), project.title)
    
    print(f'HTML已生成: {output_path}')
    print()
    return output_path


def main():
    print('pyHTML 核心功能测试')
    print()
    
    try:
        loader = test_component_loader()
        test_html_generation(loader)
        print('测试完成！')
    except Exception as e:
        print(f'测试失败: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
