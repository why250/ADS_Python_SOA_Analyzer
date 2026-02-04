这是一份经过整合、去重并优化逻辑的最终版本需求文档。它包含了从数据解析、配置管理到界面交互的所有核心细节。

---

# ADS Simulation Data SOA Analyzer - 软件需求文档 (Final v1.0, PySide2 版本)

## 1. 项目概述
**目标**：开发一个基于 Python 的桌面 GUI 应用程序，用于处理 ADS (Advanced Design System) 瞬态仿真导出的 CSV 数据。
**核心功能**：软件需**自动扫描**数据文件，识别其中的所有三极管（BJT）和电阻（Resistor），并依据外部 JSON 配置文件中的阈值，批量检查所有器件是否工作在安全工作区（SOA）内。

**技术栈要求**：
*   **语言**：Python 3.x
*   **GUI 框架**：PySide2（当前实现）或 PySide6 或  Tkinter
*   **数据处理**：Pandas, NumPy
*   **绘图**：Matplotlib

## 2. 核心功能逻辑

### 2.1 智能数据解析与自动发现 (Auto-Discovery Parser)
软件不应依赖硬编码的列名，必须通过解析 CSV 列头（Header）来自动发现器件。
导出的 CSV 数据例子 “test_tran_ex,csv”
*   **基本列识别**：
    *   `time`: 仿真时间轴（必须存在）。

*   **BJT（三极管）识别逻辑**：
    *   **分组依据**：寻找共享相同前缀的列。
    *   **关键后缀匹配**（支持 ADS 层级命名，如 `Subckt1.Q1.Q1.c`）：
        *   `.c`: 内部集电极电压节点 (Collector Node Voltage)
        *   `.b`: 内部基极电压节点 (Base Node Voltage)
        *   `.e`: 内部发射极电压节点 (Emitter Node Voltage)
        *   `.bi`: 基极电流 (Base Current)
        *   `.ci` (可选): 集电极电流。如果未直接提供，需检查是否存在发射极电流或其他方式推算，或者仅使用基极电流进行部分检查（视数据而定）。*注：通常 ADS 会输出各端口电流，需优先寻找集电极电流列。*
        *   `.t`: 器件结温 (Junction Temperature)
    *   **有效性判定**：只有同时找到 C, B, E 三个电压节点的组，才被视为一个有效的 BJT 对象。

*   **Resistor（电阻）识别逻辑**：
    *   **后缀匹配**：查找以 `.R_contact.i` 结尾的列。
    *   **命名提取**：例如列名为 `R2.R_contact.i`，则识别出器件名为 `R2`，属性为 `Current`。

### 2.2 多层级配置管理 (Configuration)
使用 JSON 文件定义 SOA 限制。系统需支持“默认类型限制”和“特定实例覆盖”两级策略。

*   **JSON 结构要求**：
    *   `defaults`: 定义 BJT 和 RESISTOR 的通用限制。
    *   `overrides`: 针对特定器件名称（如 "Q2" 或 "R_Sense"）的特殊限制。
    *   **单位标准**：所有数值均使用标准国际单位（Volts, Amperes, Watts, Celsius）。

### 2.3 物理量计算与检查 (Math & Validation)
对于每一个识别到的器件，按时间步逐行计算：

*   **BJT 检查项**：
    1.  **$V_{CE}$ (差分电压)**：$V_{CE} = V_{\text{node\_c}} - V_{\text{node\_e}}$。检查 $|V_{CE}| \le \text{MAX\_VCE}$。
    2.  **$V_{BE}$ (差分电压)**：$V_{BE} = V_{\text{node\_b}} - V_{\text{node\_e}}$。检查 $|V_{BE}| \le \text{MAX\_VBE}$。
    3.  **$I_C$ (集电极电流)**：检查 $|I_C| \le \text{MAX\_IC}$。
    4.  **$P_{diss}$ (瞬时功率)**：$P = |V_{CE} \cdot I_C| + |V_{BE} \cdot I_B|$。检查 $P \le \text{MAX\_POWER}$。
    5.  **Temperature (结温)**：直接读取 `.t` 列。检查 $T \le \text{MAX\_TEMP}$。

*   **Resistor 检查项**：
    1.  **$I_R$ (电流)**：直接读取 `.R_contact.i` 列。检查 $|I_R| \le \text{MAX\_RES\_CURRENT}$。

## 3. 用户界面 (UI) 设计

### 3.1 左侧面板：控制与列表
1.  **File Operations**：
    *   "Load CSV Data" 按钮。
    *   "Load Limit Config (JSON)" 按钮（加载后显示简要状态）。
2.  **Device Tree (核心交互)**：
    *   加载 CSV 后，自动生成树状列表：
        *   📂 **BJTs**
            *   📄 Q1 (Status: OK)
            *   📄 Q2 (Status: FAIL)
        *   📂 **Resistors**
            *   📄 R1
            *   📄 R2
    *   用户点击某个器件，右侧绘图区刷新为该器件的数据。

### 3.2 右侧面板：可视化 (Visualization)
根据左侧选择的器件类型，动态切换显示内容。

*   **若选择 BJT**：
    *   **Tab 1: SOA Trajectory (安全工作区轨迹)**
        *   X轴: $V_{CE}$, Y轴: $I_C$。
        *   绘制红色矩形框（基于配置文件中的 limit）。
        *   绘制仿真数据的散点轨迹，违规点用不同颜色标记。
    *   **Tab 2: Time Domain (时域波形)**
        *   Plot 1: $V_{CE}(t)$ & $V_{BE}(t)$ with limit lines.
        *   Plot 2: $I_C(t)$ & $I_B(t)$ with limit lines.
        *   Plot 3: $P_{diss}(t)$ & $Temp(t)$ with limit lines.

*   **若选择 Resistor**：
    *   **Tab 1: Current Check**
        *   Plot: $I_R(t)$ with $+I_{max}$ and $-I_{max}$ limit lines.

### 3.3 底部面板：结果报告
*   **Result Table**：显示所有违规记录。
    *   Columns: `Device Name` | `Time (ns)` | `Parameter (e.g. Vce)` | `Value` | `Limit` | `Violation Type`
*   **Export Button**：将表格内容导出为 CSV/Excel。

## 4. 配置文件示例 (config.json)
"soa_limits_ex.json"是一个配置文件示例
请使用此 JSON 结构作为项目的默认配置模板：

```json
{
  "description": "SOA Limits Configuration",
  "units": "SI (Volts, Amperes, Watts, Celsius)",
  "defaults": {
    "BJT": {
      "MAX_VCE": 3.0,      // 3 Volts
      "MAX_VBE": 1.2,      // 1.2 Volts
      "MAX_IC": 0.015,     // 15 mA (Converted to Amps)
      "MAX_POWER": 0.05,   // 50 mW
      "MAX_TEMP": 125.0    // 125 Celsius
    },
    "RESISTOR": {
      "MAX_RES_CURRENT": 0.01 // 10 mA
    }
  },
  "overrides": {
    "Q_PowerStage": {
      "MAX_IC": 0.5,       // This specific BJT handles 500mA
      "MAX_POWER": 1.0
    },
    "R_Shunt": {
      "MAX_RES_CURRENT": 0.1
    }
  }
}
```

## 5. 实现步骤 (Implementation Roadmap for Cursor)

1.  **Data Structure Setup**: 定义 `BJTDevice` 和 `ResistorDevice` 类，用于存储 DataFrame 中的列名映射（Column mapping）和限制值（Limits）。
2.  **Parser Implementation**: 编写 `scan_csv_columns(df)` 函数，实现 2.1 节中的正则匹配逻辑，返回器件对象列表。
3.  **GUI Layout**: 使用 PyQt6 搭建 Main Window (Left: Tree, Right: Tabs, Bottom: Log)。
4.  **Analysis Engine**: 实现 `check_soa()` 方法，利用 Pandas 的向量化运算（Vectorization）快速筛选出 `abs(col) > limit` 的行。
5.  **Visualization**: 集成 Matplotlib，实现动态根据选中的 Device 绘制对应的图表。
6.  **I/O**: 实现 CSV 导出和 JSON 加载功能。

## 6. 特别注意事项
*   **单位换算**：ADS 输出的电流通常为安培（e.g., `1.5E-02`），用户口头常说 mA。**必须**确保 JSON 中的数值与 CSV 数据单位一致（建议全部统一为基本单位 A, V, W）。
*   **正则健壮性**：ADS 的列名可能包含路径（如 `TestBench.Supply.R2.R_contact.i`），正则提取器件名时应保留足够的可识别信息，或仅提取最后一段有意义的名称。