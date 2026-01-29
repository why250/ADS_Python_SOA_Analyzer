好的，根据您的要求，我们需要将仿真（Run Simulation）和数据转换（Convert）解耦，允许用户分步操作。

以下是 **v1.2 补充需求文档**，请发送给 Cursor。

---

# ADS SOA GUI - 补充需求文档 v1.2 (Decoupled Simulation Flow)

## 1. 变更概述

**核心变更**：**新增功能** ：用户可以直接在 GUI 中配置 ADS 原理图信息，点击按钮即可调用 Keysight Python API 运行 Tran 仿真，将生成的 `.ds` 数据集自动转换为 `.csv`，并自动加载到 SOA 分析模块中。

1. **Run Simulation**: 仅执行 ADS Netlist 仿真，生成 `.ds` 文件。
2. **Convert DS to CSV**: 选择 `.ds` 文件，将其转换为 DataFrame/CSV 并自动加载到 GUI 进行分析。

**UI 位置调整**：这两个新功能需放置在左侧面板的最顶部（在现有的 "Load CSV Data" 按钮上方）。

## 2. 用户界面 (UI) 布局更新

请在左侧控制面板（Left Dock/Panel）的**最上方**添加一个名为 **"ADS Simulation & Data"** 的分组框 (Group Box)，包含以下控件：

### 2.1 输入区 (Input Fields)

* **Workspace**: [文本框] + [浏览按钮] (默认为当前路径)。
* **Lib Name**: [文本框] (例如 `SOA_Tran_Check.lib`)。
* **Cell Name**: [文本框] (例如 `TB_EF_Tran`)。

### 2.2 独立操作按钮

* **按钮 A: "Run Simulation"**
  * 功能：仅运行仿真，生成 dataset。
  * 位置：第一排按钮。
* **按钮 B: "Convert .ds to Dataframe"**
  * 功能：选择 `.ds` 文件转换为 CSV 并加载。
  * 位置：第二排按钮。

---

*(分割线)*

* **现有按钮: "Load CSV Data"** (保持在下方，用于直接加载已有的 CSV)。

## 3. 功能逻辑详解

### 3.1 功能 A: Run Simulation (仅仿真)

**触发逻辑**：

1. 读取 UI 中的 Workspace, Lib, Cell 信息。
2. 调用后台线程执行 ADS Netlist 仿真（参考用户提供的脚本）。
3. **输出**：在 workspace/data 目录下生成 `.ds` 文件。
4. **结束状态**：
   * 仿真完成后，**不要**自动转换，**不要**自动加载。
   * 仅弹窗或在状态栏提示：“Simulation Finished. Dataset saved at: [Path]”。
   * *可选优化*：将生成的 `.ds` 文件路径临时存储在内存变量中，方便下一步转换使用。

### 3.2 功能 B: Convert .ds to Dataframe (转换并加载)

**触发逻辑**：

1. 点击按钮后，弹出一个**文件选择对话框** (File Dialog)，过滤器设置为 `ADS Dataset (*.ds)`。
   * *默认路径*：如果刚刚运行过仿真，默认打开该目录；否则默认为 workspace/data。
2. **转换过程** (调用用户提供的逻辑)：
   * 使用 `dataset.open()` 打开选中的 `.ds` 文件。
   * 查找包含 `time` 变量的 Block。
   * 执行 `to_dataframe().reset_index()`。
   * 将 DataFrame 保存为同名的 `.csv` 文件 (例如 `TB_EF_Tran.csv`)。
3. **自动加载**：
   * CSV 生成后，**直接调用** GUI 现有的“CSV 加载与器件扫描”流程（即复用 Load CSV Data 的后端逻辑）。
   * 界面更新显示器件树（BJTs/Resistors）。

## 4. 后端代码逻辑参考 (Split Logic)

请将用户的脚本拆解为两个函数，并放入工作线程中：

```python
# --- Part 1: Simulation Only ---
def run_simulation_task(workspace, lib, cell):
    # Setup
    design_str = f"{lib}:{cell}:schematic"
    target_output_dir = os.path.join(workspace, "data")
  
    # Execution
    design = db.open_design(design_str)
    netlist = design.generate_netlist()
    simulator = ads.CircuitSimulator()
    simulator.run_netlist(netlist, output_dir=target_output_dir)
  
    ds_path = os.path.join(target_output_dir, f"{cell}.ds")
    return ds_path

# --- Part 2: Conversion ---
def convert_ds_task(ds_file_path):
    # Open Dataset
    output_data = dataset.open(Path(ds_file_path))
  
    # Find Time Block
    time_block_name = None
    for data_block in output_data.find_varblocks_with_var_name("time"):
        time_block_name = data_block.name
        break
      
    if not time_block_name:
        raise ValueError("No transient data found.")
      
    # Convert
    df = output_data[time_block_name].to_dataframe().reset_index()
  
    # Save to CSV
    # Replace .ds extension with .csv
    base_name = os.path.splitext(ds_file_path)[0]
    csv_path = base_name + ".csv"
    df.to_csv(csv_path, index=False)
  
    return csv_path
```

## 5. 提示词 (Prompt for Cursor)

"Modify the GUI implementation to separate the Simulation and Conversion steps based on Requirement v1.2.

1. Update the Left Panel: Add 'Run Simulation' and 'Convert .ds to Dataframe' buttons **above** the 'Load CSV' button. Add input fields for Lib/Cell names.
2. Implement 'Run Simulation': executes the ADS netlist generation and simulation, generating a `.ds` file only.
3. Implement 'Convert .ds to Dataframe': Opens a file dialog to select a `.ds` file, converts it to CSV, and **automatically** triggers the `load_csv_data` method to update the UI."
