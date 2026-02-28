import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    print('pyHTML - 报纸组件化HTML生成器')
    print('版本: 0.2.0')
    print()
    
    try:
        from gui import run_gui, HAS_GUI
        if HAS_GUI and run_gui:
            print('启动GUI...')
            run_gui()
        else:
            print('GUI不可用，请安装PyQt5: pip install PyQt5')
            print()
            print('使用命令行模式...')
            run_cli()
    except ImportError as e:
        print(f'导入错误: {e}')
        print('使用命令行模式...')
        run_cli()


def run_cli():
    print('命令行模式正在开发中...')
    print('请先安装PyQt5以使用GUI: pip install PyQt5')


if __name__ == '__main__':
    main()
