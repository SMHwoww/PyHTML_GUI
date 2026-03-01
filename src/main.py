import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    print('pyHTML - 组件化HTML生成器')
    print('版本: 0.3.1')
    print()
    
    try:
        from gui import run_gui, HAS_GUI
        if HAS_GUI and run_gui:
            print('启动GUI...')
            run_gui()
        else:
            print('GUI不可用，请安装PyQt5: pip install PyQt5')
    except ImportError as e:
        print(f'导入错误: {e}')



if __name__ == '__main__':
    main()
