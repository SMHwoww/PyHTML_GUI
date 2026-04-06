using Python.Runtime;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;

namespace PyHTML.WPF.Services
{
    public class PythonEngineService : IDisposable
    {
        private static PythonEngineService? _instance;
        private static readonly object _lock = new();
        private bool _initialized = false;
        private dynamic? _projectModule;
        private dynamic? _componentModule;
        private dynamic? _generatorModule;
        private dynamic? _aiClientModule;
        private dynamic? _imageManagerModule;
        private dynamic? _cloudflareModule;
        private dynamic? _previewServerModule;

        public static PythonEngineService Instance
        {
            get
            {
                if (_instance == null)
                {
                    lock (_lock)
                    {
                        _instance ??= new PythonEngineService();
                    }
                }
                return _instance;
            }
        }

        private PythonEngineService() { }

        public void Initialize()
        {
            if (_initialized) return;

            try
            {
                string exePath = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
                
                // 尝试多个可能的路径
                string[] possiblePaths = new[]
                {
                    // 1. 发布后的路径
                    Path.Combine(exePath, "PyHTML.Core"),
                    // 2. 开发时从 bin/Debug/net8.0-windows 返回项目根目录
                    Path.GetFullPath(Path.Combine(exePath, "..", "..", "..", "src", "core")),
                    // 3. 从项目根目录直接运行
                    Path.Combine(exePath, "src", "core"),
                    // 4. 当前工作目录
                    Path.Combine(Directory.GetCurrentDirectory(), "src", "core")
                };
                
                string? pythonPath = null;
                foreach (var path in possiblePaths)
                {
                    if (Directory.Exists(path) && File.Exists(Path.Combine(path, "project.py")))
                    {
                        pythonPath = path;
                        Debug.WriteLine($"Found Python core at: {path}");
                        break;
                    }
                }
                
                if (pythonPath == null)
                {
                    throw new DirectoryNotFoundException(
                        $"Could not find Python core modules. Searched paths:\n" +
                        string.Join("\n", possiblePaths.Select(p => $"  - {p}")));
                }

                // 设置 Python DLL
                string pythonDll = FindPythonDLL();
                
                // 检查 Python DLL 位数是否与当前应用程序匹配
                CheckPythonArchitecture(pythonDll);
                
                // 设置 Python DLL 路径 - 必须在任何 Python 操作之前设置
                Runtime.PythonDLL = pythonDll;
                
                // 设置 Python 主目录（包含 python.exe 的目录）
                string pythonHome = Path.GetDirectoryName(pythonDll)!;
                Environment.SetEnvironmentVariable("PYTHONNET_PYDLL", pythonDll);
                Environment.SetEnvironmentVariable("PYTHONHOME", pythonHome);
                Environment.SetEnvironmentVariable("PYTHONPATH", $"{pythonHome};{pythonPath}");
                
                // 初始化 Python 引擎
                PythonEngine.Initialize();
                PythonEngine.BeginAllowThreads();

                using (Py.GIL())
                {
                    dynamic sys = Py.Import("sys");
                    
                    // 添加 src 目录到路径，这样可以将 core 作为包导入
                    string srcPath = Path.GetDirectoryName(pythonPath)!;
                    sys.path.append(srcPath);
                    sys.path.append(Path.Combine(exePath, "PyHTML.Components"));
                    sys.path.append(Path.Combine(exePath, "PyHTML.Themes"));

                    // 使用绝对导入：从 core 包导入模块
                    try
                    {
                        _componentModule = Py.Import("core.component");
                    }
                    catch (Exception compEx)
                    {
                        throw new InvalidOperationException($"Failed to import core.component: {compEx.Message}", compEx);
                    }
                    
                    try
                    {
                        _projectModule = Py.Import("core.project");
                    }
                    catch (Exception projEx)
                    {
                        throw new InvalidOperationException($"Failed to import core.project: {projEx.Message}", projEx);
                    }
                    
                    try
                    {
                        _generatorModule = Py.Import("core.generator");
                    }
                    catch (Exception genEx)
                    {
                        throw new InvalidOperationException($"Failed to import core.generator: {genEx.Message}", genEx);
                    }
                    
                    try { _aiClientModule = Py.Import("core.ai_client"); } catch { }
                    try { _imageManagerModule = Py.Import("core.image_manager"); } catch { }
                    try { _cloudflareModule = Py.Import("core.cloudflare_worker"); } catch { }
                    try { _previewServerModule = Py.Import("core.preview_server"); } catch { }
                }

                _initialized = true;
            }
            catch (Exception ex)
            {
                var innerMsg = ex.InnerException?.Message ?? "无内部异常";
                var errorMsg = ex.Message;
                
                // 检查是否是 Python 3.14 不支持的错误
                if (errorMsg.Contains("3.14") || errorMsg.Contains("TypeOffset314"))
                {
                    throw new InvalidOperationException(
                        $"Python 3.14 暂不受支持!\n\n" +
                        $"当前 pythonnet 3.0.5 最高只支持 Python 3.13。\n\n" +
                        $"解决方案:\n" +
                        $"1. 【推荐】安装 Python 3.11 或 3.13 (最稳定兼容)\n" +
                        $"   下载地址: https://www.python.org/downloads/\n" +
                        $"2. 安装后设置环境变量:\n" +
                        $"   $env:PYTHONNET_PYDLL = \"C:\\Python311\\python311.dll\"\n" +
                        $"3. 或者等待 pythonnet 更新支持 Python 3.14", ex);
                }
                
                throw new InvalidOperationException(
                    $"Failed to initialize Python engine: {ex.Message}\n\n" +
                    $"内部异常: {innerMsg}\n\n" +
                    $"可能的解决方案:\n" +
                    $"1. 确保 Python 3.8-3.13 已安装 (当前使用 pythonnet 3.0.5)\n" +
                    $"   注意: Python 3.14 暂不受支持!\n" +
                    $"2. 确保 Python 位数与应用程序匹配 (当前: {(Environment.Is64BitProcess ? "64位" : "32位")})\n" +
                    $"3. 设置环境变量 PYTHONNET_PYDLL 指向 python3x.dll\n" +
                    $"   例如: $env:PYTHONNET_PYDLL = \"C:\\Python311\\python311.dll\"", ex);
            }
        }

        private void CheckPythonArchitecture(string pythonDll)
        {
            try
            {
                // 检查 DLL 是否为 64 位
                using var fs = new FileStream(pythonDll, FileMode.Open, FileAccess.Read);
                using var br = new BinaryReader(fs);
                
                fs.Seek(0x3C, SeekOrigin.Begin);
                int peOffset = br.ReadInt32();
                
                fs.Seek(peOffset + 4, SeekOrigin.Begin);
                ushort machine = br.ReadUInt16();
                
                // 0x8664 = x64, 0x14c = x86
                bool isPython64Bit = machine == 0x8664;
                bool isApp64Bit = Environment.Is64BitProcess;
                
                if (isPython64Bit != isApp64Bit)
                {
                    throw new InvalidOperationException(
                        $"Python DLL 位数不匹配! Python DLL: {(isPython64Bit ? "64位" : "32位")}, " +
                        $"应用程序: {(isApp64Bit ? "64位" : "32位")}");
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"无法检查 Python 架构: {ex.Message}");
            }
        }

        private string FindPythonDLL()
        {
            // 首先检查环境变量
            var envPath = Environment.GetEnvironmentVariable("PYTHONNET_PYDLL");
            if (!string.IsNullOrEmpty(envPath) && File.Exists(envPath))
                return envPath;

            // 获取用户目录
            string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
            string programFilesX86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);

            // 构建搜索路径列表
            var possiblePaths = new List<string>();

            // 常见安装路径 - 从最新版本到旧版本
            // 注意: pythonnet 3.0.5 最高只支持 Python 3.13，不支持 3.14
            var pythonVersions = new[] { "313", "312", "311", "310", "39", "38" };
            var pythonNames = new[] { "Python", "python" };

            foreach (var version in pythonVersions)
            {
                foreach (var name in pythonNames)
                {
                    // C:\PythonXX
                    possiblePaths.Add($@"C:\{name}{version}\python{version}.dll");

                    // C:\Users\XXX\AppData\Local\Programs\Python\PythonXX
                    possiblePaths.Add($@"{localAppData}\Programs\Python\{name}{version}\python{version}.dll");

                    // Program Files
                    possiblePaths.Add($@"{programFiles}\{name}{version}\python{version}.dll");
                    possiblePaths.Add($@"{programFiles}\Python\{name}{version}\python{version}.dll");

                    // Program Files (x86)
                    possiblePaths.Add($@"{programFilesX86}\{name}{version}\python{version}.dll");
                    possiblePaths.Add($@"{programFilesX86}\Python\{name}{version}\python{version}.dll");
                }
            }

            // 检查每个路径
            foreach (var path in possiblePaths)
            {
                if (File.Exists(path))
                    return path;
            }

            // 尝试从 PATH 环境变量中查找
            var pathEnv = Environment.GetEnvironmentVariable("PATH");
            if (!string.IsNullOrEmpty(pathEnv))
            {
                var pathDirs = pathEnv.Split(';');
                foreach (var dir in pathDirs)
                {
                    if (string.IsNullOrWhiteSpace(dir)) continue;

                    foreach (var version in pythonVersions)
                    {
                        var dllPath = Path.Combine(dir.Trim(), $"python{version}.dll");
                        if (File.Exists(dllPath))
                            return dllPath;
                    }

                    // 检查 python.exe 所在目录
                    var pythonExePath = Path.Combine(dir.Trim(), "python.exe");
                    if (File.Exists(pythonExePath))
                    {
                        var pythonDir = Path.GetDirectoryName(pythonExePath);
                        if (!string.IsNullOrEmpty(pythonDir))
                        {
                            foreach (var version in pythonVersions)
                            {
                                var dllPath = Path.Combine(pythonDir, $"python{version}.dll");
                                if (File.Exists(dllPath))
                                    return dllPath;
                            }
                        }
                    }
                }
            }

            throw new FileNotFoundException(
                "Could not find Python DLL. Please install Python or set PYTHONNET_PYDLL environment variable to the path of python3x.dll (e.g., C:\\Python311\\python311.dll)");
        }

        public dynamic CreateProject(string name)
        {
            EnsureInitialized();
            using (Py.GIL())
            {
                return _projectModule!.Project(name);
            }
        }

        public dynamic LoadProject(string filePath)
        {
            EnsureInitialized();
            using (Py.GIL())
            {
                return _projectModule!.Project.load(filePath);
            }
        }

        public dynamic GetComponentLoader()
        {
            EnsureInitialized();
            using (Py.GIL())
            {
                // 获取组件目录路径
                string exePath = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
                string[] possibleComponentPaths = new[]
                {
                    // 1. 发布后的路径
                    Path.Combine(exePath, "PyHTML.Components"),
                    // 2. 开发时从 bin/Debug/net8.0-windows 返回项目根目录
                    Path.GetFullPath(Path.Combine(exePath, "..", "..", "..", "src", "components")),
                    // 3. 从项目根目录直接运行
                    Path.Combine(exePath, "src", "components"),
                    // 4. 当前工作目录
                    Path.Combine(Directory.GetCurrentDirectory(), "src", "components")
                };
                
                string? componentsPath = null;
                foreach (var path in possibleComponentPaths)
                {
                    if (Directory.Exists(path))
                    {
                        componentsPath = path;
                        Debug.WriteLine($"Found components at: {path}");
                        break;
                    }
                }
                
                dynamic loader;
                if (componentsPath != null)
                {
                    loader = _componentModule!.ComponentLoader(componentsPath);
                    loader.load_builtin_components();
                }
                else
                {
                    loader = _componentModule!.ComponentLoader();
                }
                
                return loader;
            }
        }

        public dynamic CreateHTMLGenerator()
        {
            EnsureInitialized();
            using (Py.GIL())
            {
                return _generatorModule!.HTMLGenerator();
            }
        }

        public string GenerateHTML(dynamic project)
        {
            System.Diagnostics.Debug.WriteLine("PythonEngineService.GenerateHTML: Starting...");
            EnsureInitialized();
            
            try
            {
                using (Py.GIL())
                {
                    System.Diagnostics.Debug.WriteLine("PythonEngineService.GenerateHTML: Got GIL, creating generator...");
                    var generator = _generatorModule!.HTMLGenerator();
                    System.Diagnostics.Debug.WriteLine("PythonEngineService.GenerateHTML: Calling generate_html...");
                    
                    System.Diagnostics.Debug.WriteLine($"PythonEngineService.GenerateHTML: project.components type: {project.components.GetType()}");
                    System.Diagnostics.Debug.WriteLine($"PythonEngineService.GenerateHTML: project.title: {project.title}");
                    System.Diagnostics.Debug.WriteLine($"PythonEngineService.GenerateHTML: project.head_config type: {project.head_config.GetType()}");
                    
                    var result = generator.generate_html(project.components, project.title, project.head_config);
                    System.Diagnostics.Debug.WriteLine("PythonEngineService.GenerateHTML: Success!");
                    return result;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"PythonEngineService.GenerateHTML: Exception - {ex.GetType().Name}: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"PythonEngineService.GenerateHTML: Stack trace: {ex.StackTrace}");
                if (ex.InnerException != null)
                {
                    System.Diagnostics.Debug.WriteLine($"PythonEngineService.GenerateHTML: Inner exception - {ex.InnerException.GetType().Name}: {ex.InnerException.Message}");
                    System.Diagnostics.Debug.WriteLine($"PythonEngineService.GenerateHTML: Inner stack trace: {ex.InnerException.StackTrace}");
                }
                throw;
            }
        }

        public void SaveHTML(dynamic project, string outputPath)
        {
            EnsureInitialized();
            using (Py.GIL())
            {
                var generator = _generatorModule!.HTMLGenerator();
                generator.save_html(project.components, outputPath, project.title, project.head_config);
            }
        }

        public dynamic? GetAIClient()
        {
            EnsureInitialized();
            return _aiClientModule;
        }

        public dynamic? GetImageManager()
        {
            EnsureInitialized();
            return _imageManagerModule;
        }

        public dynamic? GetCloudflareWorker()
        {
            EnsureInitialized();
            return _cloudflareModule;
        }

        public dynamic? GetPreviewServer()
        {
            EnsureInitialized();
            return _previewServerModule;
        }

        private void EnsureInitialized()
        {
            if (!_initialized)
                throw new InvalidOperationException("Python engine is not initialized. Call Initialize() first.");
        }

        public void Dispose()
        {
            if (_initialized)
            {
                PythonEngine.Shutdown();
                _initialized = false;
            }
            _instance = null;
        }
    }
}
