
# ADS 2025 SOA Analysis GUI 使用说明书

**版本：** V1.0
**适用环境：** ADS 2025 (Linux CentOS 7 / Windows)
**更新日期：** 2026-02-05

---

## 1. 简介

**SOA Analysis GUI** 是一款集成在 ADS 2025 中的 Python 扩展工具，旨在帮助电路设计工程师快速验证器件的安全工作区（SOA）。该工具可以直接读取 ADS 仿真产生的 Dataset (`.ds`)，结合用户定义的 JSON 规则文件，自动分析 BJT、电阻等器件的电压、电流、功率及温度应力，并提供可视化的波形和超限报告。

---

## 2. 插件安装与加载

首次使用前，需要将插件加载到 ADS 环境中。

1. 启动 **ADS 2025**。
2. 在主窗口菜单栏点击 **Tools** -> **App Manager**。
3. 在弹出的窗口中点击 **Add User Addon...**。
4. 浏览并选择 `matlablink_addon.ael` 文件，点击 **Open** 完成加载。
   * *注意：加载成功后，主窗口菜单栏会出现 "MatlabLink" 菜单。*

---

## 3. 仿真前准备 (关键步骤)

为了确保 GUI 能获取到所有必要的数据，必须在 Schematic（原理图）中进行正确设置。

### 3.1 开启全节点数据保存

1. 打开待仿真的 Testbench 原理图。
2. 添加或编辑 **Options** 控件。
3. 切换到 **Output** 标签页，找到 **Output filters** 区域。
4. **务必勾选**以下两项：

   * [X] **Save branch currents** (保存支路电流)
   * [X] **Save internal node voltages** (保存内部节点电压)

   * *原因：默认设置可能不保存所有器件引脚的电流电压，会导致 SOA 分析失败。*

### 3.2 准备 SOA 规则文件

1. 将预定义的规则文件 `soa_limits_ex.json` 拷贝到当前工程的 **Workspace** 目录下。
2. GUI 启动时会默认寻找该文件。如果使用其他文件名的规则，可在 GUI 界面手动加载。

---

## 4. 启动工具

1. 在 Schematic 窗口中，点击菜单栏 **MatlabLink** -> **SOA Analysis**。
2. 等待片刻，将弹出 **ADS Simulation Data SOA Analyzer** 图形界面。

---

## 5. GUI 操作流程

工具支持“一键自动化”和“分步操作”两种模式。

### 界面功能区域说明

* **左上角 (Control Panel)**：显示当前 Workspace 和 Design 路径，包含主要操作按钮。
* **左下角 (Device Tree)**：显示所有被分析的器件列表及其状态（PASS/FAIL）。
* **右侧 (Visualization)**：数据可视化区域，包含 SOA 曲线、时域波形和结果表格。

### 操作步骤

#### 方式 A：一键运行 (推荐)

1. 在 GUI 中点击 **"Run Simulation"** 按钮。
   * 程序将自动执行 ADS 仿真 -> 生成 Dataset -> 转换为 DataFrame -> 加载 JSON 规则 -> 执行分析。
   * 分析完成后，界面会自动刷新结果。

#### 方式 B：分步操作 (用于调试或加载历史数据)

如果不希望重新仿真，可按以下顺序操作：

1. **Convert .ds to Dataframe**：选择已有的 `.ds` 文件，将其转换为 CSV 格式并加载到内存。
2. **Load CSV Data** (可选)：直接加载之前转换好的 CSV 数据。
3. **Load Limit Config (JSON)**：选择 SOA 限制规则文件 (默认加载 workspace 下的 `soa_limits_ex.json`)。
4. **Analyze**：执行 SOA 规则检查算法，刷新左侧列表和右侧图表。

---

## 6. 结果查看与分析

### 6.1 查看器件状态 (左侧列表)

分析完成后，左侧设备树会列出所有检测到的器件：

* **Resistors / BJTs**：按类型分类。
* **状态指示**：
  * **FAIL**：该器件在仿真时间内存在超出 SOA 规则的情况（列表中高亮显示）。
  * **OK**：该器件在安全范围内。
* **操作**：点击列表中的某个器件（如 `X1.Q1`），右侧图表将更新为该器件的数据。

### 6.2 数据可视化 (右侧标签页)

* **BJT SOA / Resistor SOA**：显示 V-I 轨迹图或功率曲线，直观判断轨迹是否超出安全边界。
* **V (Time) / I (Time) / P (Time) / T (Time)**：
  * 显示电压、电流、功率、温度随时间变化的波形。
  * **虚线**表示 Limit 限制线（例如 `Temp limit: 125.0°C`），实线为实际仿真波形。
  * *用途：快速定位违规发生的时间点。*

### 6.3 详细违规报告 (Result Table)

点击 **Result Table** 标签页，查看详细的数据表格：

* **内容**：包含 Device Name (器件名), Time (违规时刻), Parameter (参数类型 IE/VCE/P 等), Value (实测值), Limit (限制值), Violation Type (违规类型)。
* **导出报告**：点击表格下方的 **"Export Violations as CSV"** 按钮，可将所有违规记录保存为 Excel 可读的 CSV 文件，便于撰写报告。

---

## 7. 常见问题 (FAQ)

* **Q: 点击 Analyze 后左侧列表为空？**
  * A: 请检查原理图 Options 控件中是否勾选了 "Save branch currents"。
* **Q: 报错提示找不到 JSON 文件？**
  * A: 请确保 `soa_limits_ex.json` 在当前 Workspace 根目录下，或者使用 "Load Limit Config" 按钮手动指定路径。
