"""
ADS Python 环境一键诊断脚本
运行环境：ADS Python Console
功能：输出完整的 Python 环境、依赖、路径等关键信息
"""

import sys
import os
import platform
import pkg_resources

def print_separator(title):
    """打印分隔线，让报告格式更清晰"""
    print("=" * 80)
    print(f"【{title}】")
    print("-" * 80)

def main():
    # 1. 系统与 Python 核心信息
    print_separator("系统与 Python 核心信息")
    print(f"Python 解释器路径：{sys.executable}")
    print(f"Python 版本号：\n{sys.version}")
    print(f"系统平台信息：{platform.platform()}")
    print(f"当前工作目录：{os.getcwd()}")

    # 2. Python 路径相关
    print_separator("Python 路径相关信息")
    print("Python 模块搜索路径（sys.path）：")
    for idx, path in enumerate(sys.path, 1):
        print(f"  {idx}. {path}")

    # 3. 环境变量（仅展示关键环境变量，避免输出过长）
    print_separator("关键环境变量信息")
    key_env_vars = ["PATH", "PYTHONPATH", "HOME", "USER"]
    for var in key_env_vars:
        value = os.environ.get(var, "未设置")
        print(f"{var}：{value}")

    # 4. 已安装的第三方包列表
    print_separator("已安装第三方包（名称==版本）")
    try:
        installed_packages = pkg_resources.working_set
        # 按包名排序，便于查找
        sorted_packages = sorted(installed_packages, key=lambda x: x.key)
        for idx, package in enumerate(sorted_packages, 1):
            print(f"  {idx:3d}. {package.key}=={package.version}")
    except Exception as e:
        print(f"获取包列表失败：{str(e)}")

    # 5. ADS 常用组件检查
    print_separator("ADS 常用组件可用性检查")
    # 检查 cx_Oracle（数据库驱动）
    try:
        import cx_Oracle
        print(f"✅ cx_Oracle 已安装，版本：{cx_Oracle.version}")
    except ImportError:
        print("❌ cx_Oracle 未安装（ADS 数据库连接可能受影响）")
    # 检查其他可选组件（可根据你的需求补充）
    try:
        import pandas
        print(f"✅ pandas 已安装，版本：{pandas.__version__}")
    except ImportError:
        print("❌ pandas 未安装（数据处理常用库）")

    # 6. 补充信息
    print_separator("诊断完成 - 补充信息")
    print(f"当前已加载的模块数量：{len(sys.modules.keys())}")
    print("=" * 80)
    print("环境诊断报告生成完毕，如有异常请对照上述信息排查～")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"脚本运行出错：{str(e)}")