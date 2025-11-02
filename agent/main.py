import sys
import logging
import os
from datetime import datetime
from pathlib import Path

# 确保当前脚本所在目录在 Python 路径中
script_dir = Path(__file__).parent.absolute()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))
    
print(f"脚本目录: {script_dir}")
print(f"工作目录: {os.getcwd()}")
print(f"Python 路径: {sys.path[:3]}")  # 只打印前3个

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

# 重要：必须在 AgentServer.start_up() 之前导入，以便装饰器注册自定义 Action 和 Recognition
import my_action
import my_reco


def setup_logging():
    """配置日志系统，将日志输出到文件和控制台"""
    # 创建日志目录
    log_dir = r".\log"
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成日志文件名（按日期和时间）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"agent_{timestamp}.log")
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 文件处理器
            logging.FileHandler(log_file, encoding='utf-8'),
            # 控制台处理器
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已初始化，日志文件: {log_file}")
    
    return log_file


def main():
    # 初始化日志系统
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("MdaDuetAssistant Agent 启动")
    logger.info("=" * 60)
    logger.info(f"脚本目录: {script_dir}")
    logger.info(f"工作目录: {os.getcwd()}")
    
    # 输出已注册的自定义 Action 和 Recognition（用于调试）
    logger.info("已导入模块: my_action, my_reco")
    logger.info(f"my_action 模块位置: {my_action.__file__}")
    logger.info(f"my_action 自定义类:")
    logger.info(f"  - MyCustomAction: {my_action.MyCustomAction}")
    logger.info(f"  - LongPressWithTimeoutDetection: {my_action.LongPressWithTimeoutDetection}")
    
    Toolkit.init_option("./")

    if len(sys.argv) < 2:
        logger.error("缺少 socket_id 参数")
        print("Usage: python main.py <socket_id>")
        print("socket_id is provided by AgentIdentifier.")
        sys.exit(1)
        
    socket_id = sys.argv[-1]
    logger.info(f"Socket ID: {socket_id}")

    try:
        logger.info("启动 AgentServer...")
        AgentServer.start_up(socket_id)
        logger.info("AgentServer 已启动，等待任务...")
        AgentServer.join()
        logger.info("AgentServer 正常退出")
    except Exception as e:
        logger.error(f"AgentServer 运行出错: {e}", exc_info=True)
        raise
    finally:
        logger.info("关闭 AgentServer...")
        AgentServer.shut_down()
        logger.info("=" * 60)
        logger.info("MdaDuetAssistant Agent 已退出")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
