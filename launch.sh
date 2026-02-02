#!/bin/bash

# 1. 获取脚本所在目录 (让脚本可以在任何位置运行)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 2. 配置 ADS 环境
export HPEESOF_DIR="/eda/agilent/ADS2025"
export ADS_PYTHON="$HPEESOF_DIR/tools/python/bin/python3"

# 配置库路径
export PATH="$HPEESOF_DIR/bin:$PATH"
export LD_LIBRARY_PATH="$HPEESOF_DIR/lib/linux_x86_64:$LD_LIBRARY_PATH"
export PYTHONPATH="$HPEESOF_DIR/tools/python/lib/python3.12/site-packages:$PYTHONPATH"

# 3. (可选) 自动检查并安装依赖
# 如果你把 .whl 文件放在了 packages 目录下
if ! "$ADS_PYTHON" -c "import PyQt5" &> /dev/null; then
    echo "正在首次安装依赖库..."
    "$ADS_PYTHON" -m pip install --user "$SCRIPT_DIR/ads_offline_packages/"*.whl
fi

# 4. 启动 GUI
# "$@" 把脚本接收到的参数 (DesignName, Workspace) 透传给 main.py
echo "正在启动 SOA 分析工具..."
cd "$SCRIPT_DIR"
"$ADS_PYTHON" "main.py" "$@"