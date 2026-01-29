# ADS Python SOA Check

本项目实现一个桌面 GUI（PyQt6 + Matplotlib），用于读取 ADS 瞬态仿真导出的 CSV，并依据 JSON 限值配置检查器件 SOA。

## 目录结构

- `core/`: 与 GUI 无关的核心逻辑（配置加载、CSV 自动发现、SOA 分析）
- `gui/`: GUI 代码（主窗口、Matplotlib 画布封装）
- `main.py`: 应用入口
- `soa_gui.py`: 兼容入口（内部转到 `main.py`）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 使用

1. 点击 `Load CSV Data` 选择待处理 CSV（例如 `test_tran_ex.csv`）
2. 点击 `Load Limit Config (JSON)` 选择 SOA 配置（例如 `soa_limits_ex.json`）
3. 左侧树点击器件，右侧查看 SOA 轨迹/时域波形/电阻电流曲线
4. 底部表格会列出所有超限记录，可导出 CSV

