这是一份基于你提供的详细流程总结并补充完善后的《ADS2025外部Python GUI程序开发与跨平台移植指导说明书》。

这份文档旨在规范化开发流程，确保后续维护或其他开发人员能够复现你的工作。

---

# ADS2025 Python GUI 扩展应用开发过程指导说明书

**项目名称：** ADS_SOA_Analyzer
**适用环境：** Windows / CentOS 7
**依赖核心：** Keysight ADS 2025, Python 3.12 (ADS Built-in)
**版本：** V1.0
**日期：** 2026-02-04

---

## 1. 概述

本指南记录了如何开发一个基于Python的GUI应用程序，并将其集成到ADS (Advanced Design System) 2025中。开发流程采用“Windows开发验证 -> Windows集成测试 -> CentOS服务器移植”的策略，利用ADS自带的Python环境确保跨平台兼容性。

## 2. 第一阶段：开发环境构建 (Windows)

**目标：** 在开发机上构建与目标运行环境（ADS 2025）完全一致的Python运行时环境。

### 2.1 环境克隆

由于ADS内置了特定的Python解释器及专用库，直接使用系统Python可能导致兼容性问题。

1. **提取源环境**：从安装了 `ADS2025_Update2`的机器中定位到 `ADS2025_Update2/tools/python` 文件夹。
2. **本地迁移**：将该文件夹完整拷贝至Windows开发机的指定目录（例如 `C:\Program Files\Keysight\ADS2025_Update2\tools\python`）。此文件夹包含Python 3.12及ADS依赖的所有第三方包。

### 2.2 虚拟环境配置

为了保持纯净并在开发中使用轻量级隔离：

1. **创建脚本**：编写 `install_ads_venv.ps1` 批处理脚本，指向 `ADS2025_Update2/tools/python` 中的 `python.exe`。
2. **初始化 ads_venv虚拟环境**：
   ```bat
   ./install_ads_venv.ps1
   ```
3. **激活发ads_venv虚拟环境**：在Cursor或IDE中配置解释器路径指向新创建的 `ads_venv`。
   * *补充说明：此步骤确保了开发时引用的库版本与ADS运行时完全一致，消除了“它在我机器上能跑”的DLL缺失或版本冲突风险。*

---

## 3. 第二阶段：需求分析与GUI开发

**目标：** 完成核心业务逻辑与图形界面的编码及单元测试。

### 3.1 需求定义

1. **文档编写**：编写《ADS_SOA_Analyzer软件需求文档》，明确软件的功能边界、输入输出格式及界面交互逻辑。
2. **AI辅助编程**：利用Cursor AI编辑器，基于需求文档和当前虚拟环境进行代码生成。

### 3.2 功能开发与验证

1. **GUI框架选择**：使用Python标准GUI库（如Tkinter）或ADS环境自带的PySide/PyQt（推荐检查ADS Python自带的UI库），确保无需额外安装依赖。
2. **模拟数据测试**：
   * 手动编写 `soa_limits_ex.json`,   `test_tran_ex.csv` 等测试用例文件。
   * 脱离ADS环境，直接运行Python GUI程序读取测试文件，验证解析算法与图表绘制功能。
3. **产出物**：完成且经过本地验证的 `main.py` 及相关模块。

---

## 4. 第三阶段：Windows端 ADS 集成验证

**目标：** 验证 AEL 与 Python 的交互链路。

### 4.1 AEL 脚本开发

1. **查阅文档**：参考 ADS 2025 帮助文档中的 `Help/AEL Python documentation` 章节，重点关注 AEL调用Python函数。
2. **编写 AEL 启动器** (`PythonAdsAddons/AEL_Scripts`)：
   * 定义菜单项或工具栏按钮。
   * 构建调用命令。注意处理 Windows 路径中的空格和转义字符。
   * *AEL调用Python函数，关键代码逻辑示例*：
     ```c
         // Launch GUI as a separate process (non-blocking)
         decl gui_script = "D:\Users\Administrator\Documents\GitHub\ADS_Python_SOA_Analyzer\main.py";

         // Build a short python snippet that uses subprocess to start the GUI
         decl cmd = "";
         cmd = strcat(cmd, "import subprocess, sys; ");
         cmd = strcat(cmd, "args = [sys.executable, r'", gui_script, "', '", design_name, "', r'", workspace_path, "']; ");
         cmd = strcat(cmd, "subprocess.Popen(args, close_fds=True)");

         de_info(strcat("Launching external GUI (non-blocking):", gui_script));
         python_exec(cmd);
     ```
3. **联调测试**：
   * 在 Windows 安装的 ADS 2025 主窗口加载 AEL 文件。
   * 点击触发，观察是否成功唤起 GUI 窗口。
   * 验证 GUI 生成的结果文件是否能反馈回 ADS（如数据回读）。

---

## 5. 第四阶段：CentOS 7 服务器移植与部署

**目标：** 在生产环境（Linux服务器）实现功能落地。

### 5.1 代码迁移

1. **文件上传**：将开发好的Python源码、输入示例文件通过 SFTP 上传至 CentOS 7 服务器指定的工作目录。
2. **权限管理**：
   * 确保 Python 脚本具有读取权限。
   * 如果脚本包含 Shell 头部 (`#!/usr/bin/env python`)，需赋予执行权限：`chmod +x main.py`。

### 5.2 路径与环境适配

1. **路径修正**：

   * 修改 AEL 脚本中的main.py路径，将windows下的路径更改为centos7下的路径。

### 5.3 最终验收

1. 在 CentOS 环境启动 ADS 2025。
2. 加载修改后的 AEL 脚本。
3. 执行调用，确认 GUI 界面顺利弹出，且功能逻辑与 Windows 端一致。

---

## 6. 开发注意事项与补充建议

1. **路径兼容性设计**：
   * 建议在 Python 代码中使用 `os.path.join` 处理路径，在 AEL 代码中尽量使用相对路径或通过环境变量获取 ADS 安装根目录 (`HPEESOF_DIR`)，减少硬编码，提高脚本的可移植性。
   * *AEL 优化建议*：
     ```c
     decl ads_home = getenv("HPEESOF_DIR");
     decl py_cmd = strcat(ads_home, "/tools/python/...");
     ```
2. **日志记录**：
   * 建议在 Python GUI 程序中增加 `logging` 模块，将运行日志输出到文件。因为在 ADS 调用 Python 时，控制台标准输出（stdout/stderr）可能不可见，日志文件是排查服务器端错误的唯一手段。
   * 在ADS调用GUI时，运行日志保存路径应为当前工作的workspace/data，避免写入main.py所在的目录，防止没有写权限。
3. **依赖库陷阱**：
   * 虽然使用了 ADS 自带 Python，但如果 GUI 用到了涉及底层系统调用的库（如 ctypes），需注意 Windows DLL 与 Linux SO 文件的差异。
4. **CentOS 7 特异性**：
   * CentOS 7 系统较老，若 GUI 依赖某些系统级图形库（如 GTK/Qt 的特定底层库），可能会遇到缺失情况。由于直接使用了 ADS 内置环境，通常 ADS 厂商已解决了大部分依赖，但如果遇到 `ImportError: libGL.so.1` 等错误，需联系服务器管理员安装对应系统库。
   * 在CentOS 7 系统终端，使用ADS2025自带的python建立虚拟环境，运行python main.py，仍然无法打开gui，可能是缺失某些系统级图形库。

---

**文档结束**
