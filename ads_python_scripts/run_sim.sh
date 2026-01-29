#!/bin/bash

# ================= 核心配置 (根据你的截图) =================
# ADS 安装根目录
export HPEESOF_DIR="/eda/agilent/ADS2025"

# Python 解释器路径 (你之前截图里的那个)
PY_EXEC="$HPEESOF_DIR/tools/python/bin/python3"

# ================= 关键：手动注入环境变量 =================
# 1. 告诉系统 ADS 的命令在哪里
export PATH="$HPEESOF_DIR/bin:$PATH"

# 2. 告诉系统 ADS 的底层 C++ 库 (.so文件) 在哪里
# 没有这一步，仿真引擎启动时会报错找不到共享库
export LD_LIBRARY_PATH="$HPEESOF_DIR/lib/linux_x86_64:$LD_LIBRARY_PATH"

# 3. 告诉 Python 去哪里找 keysight.ads 模块
# 根据截图，Python版本是 3.12
export PYTHONPATH="$HPEESOF_DIR/tools/python/lib/python3.12/site-packages:$PYTHONPATH"

# ================= 运行设置 =================
# 工作目录 (必须进入这里，因为你的脚本用的是 Path.cwd)
WORK_DIR="/home/eda_grp/weihaoyu/ADS_Python_Tutorials/tutoriall_wrk"

# 你的 Python 脚本路径
SCRIPT_PATH="../Scripts/SOA_Tran_Check/tran_sim_and_data_convert.py"

# ================= 开始执行 =================
echo "正在配置 ADS 2025 环境..."
echo "HPEESOF_DIR: $HPEESOF_DIR"

# 检查 Python 是否存在
if [ ! -f "$PY_EXEC" ]; then
    echo "❌ 错误: 找不到 Python 解释器: $PY_EXEC"
    exit 1
fi

# 进入工作目录
echo "📂 进入工作目录: $WORK_DIR"
cd "$WORK_DIR" || { echo "❌ 无法进入目录"; exit 1; }

# 运行脚本
echo "🚀 开始运行仿真脚本..."
echo "---------------------------------------------------"

"$PY_EXEC" "$SCRIPT_PATH"

echo "---------------------------------------------------"
echo "✅ 运行结束"