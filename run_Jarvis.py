import sys
import os
import time
from typing import Optional

# --- 路径设置 ---
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# --- 导入 ---
try:
    from Agent.task_decompose_agent import TaskDecomposer
    from Agent.task_execution_agent import TaskExecutionAgent
    from Agent.task_roader import TaskData, read_task_data_from_json
    import config
except ImportError as e:
    print(f"错误：导入 Agent 或 config 模块失败：{e}")
    print("请确保您的项目结构正确，并检查 src/Agent 目录及 config.py 文件。")
    print(f"当前 Python 搜索路径: {sys.path}")
    exit(1)


# --- 分解函数 (保持不变) ---
def run_decomposition(
    decomposer: TaskDecomposer, task: str, task_id: str
) -> Optional[str]:
    """运行任务分解并返回日志目录路径"""
    print(f"\n--- [阶段 1: 任务分解] ---")
    print(f"开始分解任务 (ID: {task_id})...")
    log_dir_path = decomposer.decompose(task, task_id)
    if log_dir_path:
        print(f"[分解成功] 日志目录已创建: {log_dir_path}")
    else:
        print("[分解失败] 未能生成任务分解结果。")
    return log_dir_path


# --- 主程序入口 ---
def main():
    """主执行函数，协调分解和执行"""
    print("=" * 50)
    print("--- 开始运行 Jarvis (Refactored V2) ---")
    print("=" * 50)

    # 1. 加载原始任务数据 (包含基准答案)
    print(f"加载原始任务数据来源: {config.JSON_PATH}")
    original_task_data = read_task_data_from_json(config.JSON_PATH)
    if (
        not original_task_data
        or not original_task_data.Task
        or not original_task_data.Task_ID
    ):
        print("[运行失败] 未能从 JSON 文件加载有效的原始任务数据。")
        return

    initial_task_description = original_task_data.Task
    task_id_str = original_task_data.Task_ID
    print(f"原始任务加载成功: Task ID = {task_id_str}")

    # 2. 初始化并运行任务分解 Agent
    try:
        decomposer = TaskDecomposer(
            config.TD_API_URL, config.TD_API_KEY, config.TD_MODEL, config.GlOBAL_PROXY
        )
    except AttributeError as e:
        print(f"错误：初始化 TaskDecomposer 失败，配置缺失：{e}")
        return
    # task_time = time.strftime("%Y%m%d-%H%M%S")
    # decomposer = f"{decomposer}/{task_time}"
    log_directory = run_decomposition(decomposer, initial_task_description, task_id_str)

    # 3. 如果分解成功，则初始化并运行任务执行 Agent 的主流程
    if log_directory:
        print(f"\n--- [阶段 2: 任务执行 (由 Agent 内部驱动)] ---")
        try:
            # << 修改：在初始化时传入 original_task_data >>
            executor = TaskExecutionAgent(
                api_url=config.TE_API_URL,
                api_key=config.TE_API_KEY,
                original_task_data=original_task_data,  # 传递原始数据
                model=config.TE_MODEL,
                proxy=config.GlOBAL_PROXY,
                av_api_url=config.AV_API_URL,
                av_api_key=config.AV_API_KEY,
                av_model=config.AV_MODEL,
            )
        except AttributeError as e:
            print(f"错误：初始化 TaskExecutionAgent 失败，配置缺失：{e}")
            return
        except ImportError as e:
            print(f"错误：初始化 TaskExecutionAgent 失败，导入依赖项出错：{e}")
            return
        except TypeError as e:
            print(
                f"错误：初始化 TaskExecutionAgent 失败，参数类型错误（可能是 original_task_data 无效）：{e}"
            )
            return

        # << 修改：调用 execute_task_flow 时不再传递 original_task_data >>
        execution_success = executor.execute_task_flow(log_directory)

        # --- 报告最终结果 ---
        print("\n" + "=" * 50)
        if execution_success:
            print("--- Jarvis 任务执行流程成功完成 ---")
            print(
                f"最终结果已保存至日志目录: '{log_directory}' (Task_Split_Final.json)"
            )
        else:
            print("--- Jarvis 任务执行流程失败或中止 ---")
            print(f"请检查日志目录 '{log_directory}' 中的详细日志和中间文件。")
        print("=" * 50)

    else:
        # 分解失败
        print("\n" + "=" * 50)
        print("--- Jarvis 任务分解失败，无法继续执行 ---")
        print("=" * 50)


if __name__ == "__main__":
    # 检查配置和文件存在性
    required_configs = ["JSON_PATH", "TD_API_URL", "TD_API_KEY", "TD_MODEL"]
    missing_configs = [
        cfg
        for cfg in required_configs
        if not hasattr(config, cfg) or not getattr(config, cfg)
    ]
    if missing_configs:
        print(
            f"错误：config.py 文件不完整，缺少必要的配置项: {', '.join(missing_configs)}。"
        )
    elif not hasattr(config, "TD_API_KEY") or not config.TD_API_KEY:
        print("错误：API Key (TD_API_KEY) 未在 config.py 中配置。")
    elif not os.path.exists(config.JSON_PATH):
        print(f"错误：配置文件中指定的 JSON_PATH ('{config.JSON_PATH}') 不存在。")
    else:
        main()
