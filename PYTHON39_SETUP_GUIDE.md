# Python 3.9 安装和运行指南

## 前置要求
- Python 3.9 或更高版本
- pip 包管理工具

## 快速开始

### 步骤 1: 准备 Python 3.9 环境

#### Windows
```bash
# 使用 python3.9 或 python（如果系统默认是 3.9）
python --version    # 确认版本为 3.9.x

# 创建虚拟环境
python -m venv venv_py39

# 激活虚拟环境
venv_py39\Scripts\activate
```

#### macOS/Linux
```bash
python3.9 --version    # 确认版本为 3.9.x

# 创建虚拟环境
python3.9 -m venv venv_py39

# 激活虚拟环境
source venv_py39/bin/activate
```

### 步骤 2: 安装依赖包

```bash
# 确保已激活虚拟环境
pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt
```

### 步骤 3: 运行 GUI 应用

```bash
# 简单运行
python main.py

# 或指定工作空间和设计（来自 ADS）
python main.py "design_name:cell_name:view" "/path/to/workspace"
```

## 验证安装

运行以下命令验证所有依赖已正确安装：

```bash
python -c "
import sys
import numpy as np
import pandas as pd
import matplotlib
from PyQt5 import QtWidgets, QtCore

print(f'Python {sys.version}')
print(f'NumPy {np.__version__}')
print(f'Pandas {pd.__version__}')
print(f'Matplotlib {matplotlib.__version__}')
print('PyQt5 imports OK')
print('✅ All dependencies installed successfully!')
"
```

## 常见问题解决

### 问题 1: "ModuleNotFoundError: No module named 'PyQt5'"
**解决方案**：
```bash
# 确保虚拟环境已激活
pip install PyQt5>=5.15.0
```

### 问题 2: "Could not find a version that satisfies the requirement"
**解决方案**：
```bash
# 更新 pip 到最新版本
pip install --upgrade pip setuptools wheel

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 问题 3: GUI 启动缓慢或有渲染问题
**解决方案**：
- 更新显卡驱动程序
- 如果在虚拟机中运行，确保硬件加速已启用
- 检查 matplotlib 的显示后端：`python -c "import matplotlib; print(matplotlib.get_backend())"`

### 问题 4: CSV 加载失败
**解决方案**：
- 确保 CSV 文件包含 'time' 列（大小写敏感）
- 检查 CSV 编码为 UTF-8
- 查看日志文件：`ads_soa_gui.log`

## 项目结构说明

```
.
├── main.py                 # GUI 主入口点
├── soa_gui.py             # 备用入口点（兼容性保留）
├── requirements.txt       # Python 3.9 依赖列表（已更新）
├── core/                  # 核心分析模块
│   ├── models.py          # 数据模型定义
│   ├── analysis.py        # SOA 分析算法
│   ├── parser.py          # CSV 解析器
│   ├── config.py          # 配置加载
│   └── ads_sim.py         # ADS 集成（可选）
├── gui/                   # GUI 相关模块
│   ├── main_window.py     # 主窗口（已升级 PyQt5）
│   └── mpl_canvas.py      # Matplotlib 画布集成
└── PythonAdsAddons/       # ADS 插件脚本（可选）
```

## 下一步

详见 [PYTHON39_COMPATIBILITY.md](./PYTHON39_COMPATIBILITY.md) 了解：
- 完整的兼容性验证报告
- 依赖版本详情
- ADS 集成说明
