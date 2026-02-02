#!/bin/bash

# 1. Define Paths (根据你的实际 Linux 安装路径修改)
ADS_PATH="/usr/local/Keysight/ADS2025_Update2/tools/python" 
ADS_PYTHON="$ADS_PATH/python"
WHEEL_DIR="$ADS_PATH/wheelhouse"
VENV_NAME="ads_venv"

echo -e "\033[36m--- Starting ADS Python Environment Setup ---\033[0m"

# 2. Environment Check
if [ ! -f "$ADS_PYTHON" ]; then
    echo -e "\033[31mERROR: ADS Python not found at: $ADS_PYTHON\033[0m"
    exit 1
fi

# 3. Create Virtual Environment
echo -e "\033[33mCreating virtual environment [$VENV_NAME]...\033[0m"
"$ADS_PYTHON" -m venv "$VENV_NAME"

# 4. Install ADS Libraries
echo -e "\033[33mInstalling compatible wheels from wheelhouse directory...\033[0m"
LOCAL_PIP="./$VENV_NAME/bin/python"

# 遍历安装 wheel
cd "$WHEEL_DIR" || exit
for wheel in *.whl; do
    echo -n "Attempting to install: $wheel..."
    # 使用全路径调用 pip
    "$OLDPWD/$LOCAL_PIP" -m pip install "$wheel" --find-links . --no-index > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e " \033[32m[SUCCESS]\033[0m"
    else
        echo -e " \033[90m[SKIPPED]\033[0m"
    fi
done
cd "$OLDPWD"

# 5. Verification
echo -e "\n\033[32m--- Setup Complete! ---\033[0m"
echo "To activate this environment, run:"
echo "source ./$VENV_NAME/bin/activate"