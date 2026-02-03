"""
ADS Python 环境一键诊断脚本（兼容版）
运行环境：ADS Python Console / 标准 Python 3.8+
功能：1. 控制台输出清晰报告 2. 生成本地 txt 报告文件 3. 自动适配新版 Python
"""

import sys
import os
import platform
import importlib.metadata  # 替代 pkg_resources
from datetime import datetime

# 全局变量：存储报告内容
report_content = []

def print_separator(title):
    """打印分隔线（控制台+报告内容），让格式更清晰"""
    separator_line = "=" * 80
    title_line = f"【{title}】"
    dash_line = "-" * 80
    
    print(separator_line)
    print(title_line)
    print(dash_line)
    
    report_content.append(separator_line)
    report_content.append(title_line)
    report_content.append(dash_line)

def add_to_report(content):
    """将内容同时输出到控制台和报告列表"""
    print(content)
    if isinstance(content, str) and "\n" in content:
        report_content.extend(content.split("\n"))
    else:
        report_content.append(str(content))

def main():
    global report_content
    # 1. 生成报告文件名
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"ads_env_diagnosis_{current_time}.txt"
    report_path = os.path.join(os.getcwd(), report_filename)

    # 2. 系统与 Python 核心信息
    print_separator("系统与 Python 核心信息")
    add_to_report(f"Python 解释器路径：{sys.executable}")
    add_to_report(f"Python 版本号：\n{sys.version}")
    add_to_report(f"系统平台信息：{platform.platform()}")
    add_to_report(f"当前工作目录：{os.getcwd()}")
    add_to_report(f"报告保存路径：{report_path}")

    # 3. Python 路径相关
    print_separator("Python 路径相关信息")
    add_to_report("Python 模块搜索路径（sys.path）：")
    for idx, path in enumerate(sys.path, 1):
        add_to_report(f"  {idx}. {path}")

    # 4. 环境变量
    print_separator("关键环境变量信息")
    key_env_vars = ["PATH", "PYTHONPATH", "HOME", "USER", "USERNAME"]
    for var in key_env_vars:
        value = os.environ.get(var, "未设置")
        add_to_report(f"{var}：{value}")

    # 5. 已安装的第三方包列表 (使用 importlib.metadata 适配 Python 3.12)
    print_separator("已安装第三方包（名称==版本）")
    try:
        dists = importlib.metadata.distributions()
        # 按照包名（不区分大小写）排序
        sorted_packages = sorted(dists, key=lambda x: x.metadata['Name'].lower())
        
        for idx, dist in enumerate(sorted_packages, 1):
            name = dist.metadata['Name']
            version = dist.version
            add_to_report(f"  {idx:3d}. {name}=={version}")
    except Exception as e:
        add_to_report(f"获取包列表失败：{str(e)}")

    # 6. ADS 常用组件检查
    print_separator("ADS 常用组件可用性检查")
    # 检查 cx_Oracle
    try:
        import cx_Oracle
        add_to_report(f"✅ cx_Oracle 已安装，版本：{cx_Oracle.version}")
    except ImportError:
        add_to_report("❌ cx_Oracle 未安装（ADS 数据库连接可能受影响）")
    
    # 检查 pandas
    try:
        import pandas
        add_to_report(f"✅ pandas 已安装，版本：{pandas.__version__}")
    except ImportError:
        add_to_report("❌ pandas 未安装（数据处理常用库）")

    # 7. 补充信息
    print_separator("诊断完成 - 补充信息")
    add_to_report(f"当前已加载的模块数量：{len(sys.modules.keys())}")
    add_to_report("=" * 80)
    add_to_report("环境诊断报告生成完毕！")

    # 8. 写入文件
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_content))
        print(f"\n✅ 报告已保存至：{report_path}")
    except Exception as e:
        print(f"\n❌ 报告保存失败：{str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"脚本运行严重出错：{str(e)}")