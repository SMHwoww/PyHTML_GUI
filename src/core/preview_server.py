import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path
from typing import Optional
from .generator import HTMLGenerator
from .project import Project


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, html_content: str, *args, **kwargs):
        self.html_content = html_content
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.html_content.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


class PreviewServer:
    def __init__(self, port: int = 8000):
        self.port = port
        self.server: Optional[socketserver.TCPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.html_generator = HTMLGenerator()
        self.current_html: str = ''
    
    def update_html(self, project: Project):
        self.current_html = self.html_generator.generate_html(project.components, project.title)
    
    def _start_server(self):
        handler = lambda *args, **kwargs: PreviewHandler(self.current_html, *args, **kwargs)
        self.server = socketserver.TCPServer(('', self.port), handler)
        self.server.serve_forever()
    
    def start(self, project: Project):
        self.update_html(project)
        if self.thread and self.thread.is_alive():
            self.stop()
        self.thread = threading.Thread(target=self._start_server, daemon=True)
        self.thread.start()
        return f'http://localhost:{self.port}'
    
    def stop(self):
        if self.server:
            try:
                # 使用非阻塞方式关闭服务器
                import threading
                def shutdown_server():
                    try:
                        self.server.shutdown()
                        self.server.server_close()
                    except Exception:
                        pass
                # 在后台线程中执行关闭操作
                shutdown_thread = threading.Thread(target=shutdown_server, daemon=True)
                shutdown_thread.start()
            except Exception:
                pass
        # 不使用 join() 避免阻塞主线程
        # if self.thread:
        #     self.thread.join(timeout=1)
    
    def open_browser(self):
        webbrowser.open(f'http://localhost:{self.port}')
