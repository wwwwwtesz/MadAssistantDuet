"""
PostMessage 自定义动作
基于 PostMessage + 扫描码实现的游戏控制动作
"""

import json
import logging
import time
from maa.custom_action import CustomAction
from maa.context import Context
from .input_helper import PostMessageInputHelper
import win32con
import win32gui
import sys
import os

# 导入主模块来访问全局配置
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main

logger = logging.getLogger(__name__)

# 注意：闪避键现在直接使用虚拟键码(int),无需映射


class GameWindowAction(CustomAction):
    """
    游戏窗口操作基类
    提供通用的窗口句柄获取方法
    """
    
    # 目标窗口标题关键字列表
    WINDOW_TITLE_KEYWORDS = ["二重螺旋", "Duet Night Abyss"]
    
    def _get_window_handle(self, context: Context) -> int:
        """
        获取窗口句柄（通用方法）
        
        优先查找包含 WINDOW_TITLE_KEYWORDS 中任一关键字的窗口
        
        Args:
            context: MaaFramework 上下文
            
        Returns:
            窗口句柄，如果获取失败返回 0
        """
        try:
            # 方法 1: 精确匹配 - 遍历所有关键字
            for keyword in self.WINDOW_TITLE_KEYWORDS:
                hwnd = win32gui.FindWindow(None, keyword)
                if hwnd and win32gui.IsWindow(hwnd):
                    logger.info(f"[_get_window_handle] [OK] 找到「{keyword}」窗口: {hwnd} (0x{hwnd:08X})")
                    return hwnd
            
            # 方法 2: 模糊匹配 - 枚举所有窗口查找包含任一关键字的
            def find_window_callback(hwnd, param):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    for keyword in self.WINDOW_TITLE_KEYWORDS:
                        if keyword in title:
                            param.append((hwnd, keyword, title))
                            return
            
            found_windows = []
            win32gui.EnumWindows(find_window_callback, found_windows)
            
            if found_windows:
                hwnd, keyword, title = found_windows[0]
                logger.info(f"[_get_window_handle] [OK] 找到包含「{keyword}」的窗口: {hwnd} (0x{hwnd:08X})")
                logger.info(f"[_get_window_handle] 窗口标题: '{title}'")
                return hwnd
            
            logger.error(f"[_get_window_handle] 未找到包含 {self.WINDOW_TITLE_KEYWORDS} 中任一关键字的窗口")
            return 0
            
        except Exception as e:
            logger.error(f"[_get_window_handle] 获取窗口句柄失败: {e}", exc_info=True)
            return 0


def debug_controller_attributes(ctrl, logger_instance=None):
    """
    调试工具：打印控制器对象的所有属性
    
    Args:
        ctrl: 控制器对象
        logger_instance: 日志记录器，如果为 None 则使用 print
    """
    log_func = logger_instance.debug if logger_instance else print
    
    log_func("=" * 60)
    log_func(f"[DEBUG] 控制器对象类型: {type(ctrl)}")
    log_func(f"[DEBUG] 控制器对象: {ctrl}")
    log_func("=" * 60)
    
    # 列出所有属性
    attrs = dir(ctrl)
    log_func(f"[DEBUG] 控制器属性列表 ({len(attrs)} 个):")
    
    for attr in attrs:
        if not attr.startswith('_'):  # 先显示公开属性
            try:
                value = getattr(ctrl, attr)
                value_type = type(value).__name__
                
                # 对于整数类型，同时显示十六进制
                if isinstance(value, int):
                    if 0 < value <= 0xFFFFFFFF:
                        log_func(f"  {attr}: {value} (0x{value:08X}) [{value_type}] ← 可能是窗口句柄")
                    else:
                        log_func(f"  {attr}: {value} [{value_type}]")
                elif callable(value):
                    log_func(f"  {attr}: <method/function> [{value_type}]")
                elif len(str(value)) < 100:
                    log_func(f"  {attr}: {value} [{value_type}]")
                else:
                    log_func(f"  {attr}: <large object> [{value_type}]")
            except Exception as e:
                log_func(f"  {attr}: <无法访问: {e}>")
    
    # 再显示私有属性
    log_func("\n[DEBUG] 私有属性:")
    for attr in attrs:
        if attr.startswith('_') and not attr.startswith('__'):
            try:
                value = getattr(ctrl, attr)
                value_type = type(value).__name__
                
                if isinstance(value, int):
                    if 0 < value <= 0xFFFFFFFF:
                        log_func(f"  {attr}: {value} (0x{value:08X}) [{value_type}] ← 可能是窗口句柄")
                    else:
                        log_func(f"  {attr}: {value} [{value_type}]")
                elif callable(value):
                    log_func(f"  {attr}: <method/function> [{value_type}]")
                elif len(str(value)) < 100:
                    log_func(f"  {attr}: {value} [{value_type}]")
                else:
                    log_func(f"  {attr}: <large object> [{value_type}]")
            except Exception as e:
                log_func(f"  {attr}: <无法访问: {e}>")
    
    log_func("=" * 60)


class RunWithShift(GameWindowAction):
    """
    奔跑动作：先按下方向键,再按下闪避键(可配置),保持指定时长
    
    参数说明：
    {
        "direction": "w",      // 方向键：'w', 'a', 's', 'd' 或 'up', 'down', 'left', 'right'
        "duration": 2.0,       // 持续时长（秒）
        "dodge_delay": 0.05    // 按下方向键后,多久按下闪避键（秒）,默认 0.05
    }
    
    注意：使用的闪避键从全局配置 main.GAME_CONFIG["dodge_key"] 中读取
    """
    
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        # 解析参数
        try:
            if isinstance(argv.custom_action_param, str):
                params = json.loads(argv.custom_action_param)
            elif isinstance(argv.custom_action_param, dict):
                params = argv.custom_action_param
            else:
                logger.error(f"[RunWithShift] 参数类型错误: {type(argv.custom_action_param)}")
                return False
        except json.JSONDecodeError as e:
            logger.error(f"[RunWithShift] JSON 解析失败: {e}")
            logger.error(f"  参数内容: {argv.custom_action_param}")
            return False
        
        # 获取参数
        direction = params.get("direction", "w")
        duration = params.get("duration", 2.0)
        dodge_delay = params.get("dodge_delay", 0.05)
        
        # 从全局配置获取闪避键(现在是虚拟键码 int)
        dodge_vk = main.GAME_CONFIG.get("dodge_key", win32con.VK_SHIFT)
        
        logger.info("=" * 60)
        logger.info(f"[RunWithShift] 开始奔跑")
        logger.info(f"  方向: {direction}")
        logger.info(f"  持续时长: {duration:.2f}秒")
        logger.info(f"  闪避键延迟: {dodge_delay:.3f}秒")
        logger.info(f"  使用闪避键: VK={dodge_vk} (0x{dodge_vk:02X})")
        
        try:
            # DEBUG: 打印控制器信息（仅在 DEBUG 级别）
            if logger.isEnabledFor(logging.DEBUG):
                debug_controller_attributes(context.tasker.controller, logger)
            
            # 获取窗口句柄
            hwnd = self._get_window_handle(context)
            if not hwnd:
                logger.error("[RunWithShift] 无法获取窗口句柄")
                # 在失败时强制打印控制器信息
                debug_controller_attributes(context.tasker.controller, logger)
                return False
            
            # 创建输入辅助对象
            input_helper = PostMessageInputHelper(hwnd)
            
            # 获取方向键的虚拟键码
            direction_vk = input_helper.get_direction_vk(direction)
            
            logger.info(f"[RunWithShift] 方向键 VK={direction_vk}, 闪避键 VK={dodge_vk}")
            
            # 1. 按下方向键
            logger.info(f"[RunWithShift] 步骤 1: 按下方向键 '{direction}'")
            input_helper.key_down(direction_vk, activate=True)
            
            # 2. 短暂延迟
            if dodge_delay > 0:
                logger.debug(f"[RunWithShift] 等待 {dodge_delay:.3f}秒...")
                time.sleep(dodge_delay)
            
            # 3. 按下闪避键
            logger.info(f"[RunWithShift] 步骤 2: 按下闪避键 (VK=0x{dodge_vk:02X})")
            input_helper.key_down(dodge_vk, activate=False)
            
            # 4. 保持按下状态
            logger.info(f"[RunWithShift] 步骤 3: 保持 {duration:.2f}秒...")
            time.sleep(duration)
            
            # 5. 释放闪避键
            logger.info(f"[RunWithShift] 步骤 4: 释放闪避键")
            input_helper.key_up(dodge_vk)
            
            # 6. 释放方向键
            logger.info(f"[RunWithShift] 步骤 5: 释放方向键")
            input_helper.key_up(direction_vk)
            
            logger.info(f"[RunWithShift] [OK] 完成奔跑 {duration:.2f}秒")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"[RunWithShift] 发生异常: {e}", exc_info=True)
            return False


class LongPressKey(GameWindowAction):
    """
    长按单个按键
    
    参数说明：
    {
        "key": "w",           // 按键：字符或虚拟键码
        "duration": 2.0       // 持续时长（秒）
    }
    """
    
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        # 解析参数
        try:
            if isinstance(argv.custom_action_param, str):
                params = json.loads(argv.custom_action_param)
            elif isinstance(argv.custom_action_param, dict):
                params = argv.custom_action_param
            else:
                logger.error(f"[LongPressKey] 参数类型错误: {type(argv.custom_action_param)}")
                return False
        except json.JSONDecodeError as e:
            logger.error(f"[LongPressKey] JSON 解析失败: {e}")
            return False
        
        # 获取参数
        key = params.get("key")
        duration = params.get("duration", 1.0)
        
        if not key:
            logger.error("[LongPressKey] 缺少参数 'key'")
            return False
        
        logger.info(f"[LongPressKey] 长按键 '{key}' 持续 {duration:.2f}秒")
        
        try:
            # 获取窗口句柄
            hwnd = self._get_window_handle(context)
            if not hwnd:
                logger.error("[LongPressKey] 无法获取窗口句柄")
                return False
            
            # 创建输入辅助对象
            input_helper = PostMessageInputHelper(hwnd)
            
            # 转换为虚拟键码
            if isinstance(key, str) and len(key) == 1:
                vk_code = input_helper.char_to_vk(key)
            elif isinstance(key, int):
                vk_code = key
            else:
                logger.error(f"[LongPressKey] 不支持的键类型: {key}")
                return False
            
            # 执行长按
            input_helper.long_press_key(vk_code, duration)
            
            logger.info(f"[LongPressKey] [OK] 完成长按")
            return True
            
        except Exception as e:
            logger.error(f"[LongPressKey] 发生异常: {e}", exc_info=True)
            return False


class PressMultipleKeys(GameWindowAction):
    """
    同时按下多个按键
    
    参数说明：
    {
        "keys": ["w", "shift"],  // 按键列表
        "duration": 2.0          // 持续时长（秒）
    }
    """
    
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        # 解析参数
        try:
            if isinstance(argv.custom_action_param, str):
                params = json.loads(argv.custom_action_param)
            elif isinstance(argv.custom_action_param, dict):
                params = argv.custom_action_param
            else:
                logger.error(f"[PressMultipleKeys] 参数类型错误")
                return False
        except json.JSONDecodeError as e:
            logger.error(f"[PressMultipleKeys] JSON 解析失败: {e}")
            return False
        
        # 获取参数
        keys = params.get("keys", [])
        duration = params.get("duration", 1.0)
        
        if not keys:
            logger.error("[PressMultipleKeys] 缺少参数 'keys'")
            return False
        
        logger.info(f"[PressMultipleKeys] 同时按下 {len(keys)} 个键，持续 {duration:.2f}秒")
        logger.info(f"  按键列表: {keys}")
        
        try:
            # 获取窗口句柄
            hwnd = self._get_window_handle(context)
            if not hwnd:
                logger.error("[PressMultipleKeys] 无法获取窗口句柄")
                return False
            
            # 创建输入辅助对象
            input_helper = PostMessageInputHelper(hwnd)
            
            # 转换为虚拟键码列表
            vk_codes = []
            for key in keys:
                if isinstance(key, str):
                    if len(key) == 1:
                        vk = input_helper.char_to_vk(key)
                    else:
                        # 特殊键名称
                        key_lower = key.lower()
                        if key_lower == 'shift':
                            vk = win32con.VK_SHIFT
                        elif key_lower == 'ctrl':
                            vk = win32con.VK_CONTROL
                        elif key_lower == 'alt':
                            vk = win32con.VK_MENU
                        elif key_lower == 'space':
                            vk = win32con.VK_SPACE
                        else:
                            logger.error(f"[PressMultipleKeys] 不支持的键名称: {key}")
                            return False
                elif isinstance(key, int):
                    vk = key
                else:
                    logger.error(f"[PressMultipleKeys] 不支持的键类型: {key}")
                    return False
                
                vk_codes.append(vk)
            
            # 执行同时按键
            input_helper.press_multiple_keys(vk_codes, duration)
            
            logger.info(f"[PressMultipleKeys] [OK] 完成同时按键")
            return True
            
        except Exception as e:
            logger.error(f"[PressMultipleKeys] 发生异常: {e}", exc_info=True)
            return False


class RunWithJump(GameWindowAction):
    """
    边跑边跳动作：先按下方向键，延迟后按下闪避键（奔跑），然后周期性短按空格键（跳跃）
    
    参数说明：
    {
        "direction": "w",        // 方向键：'w', 'a', 's', 'd' 或 'up', 'down', 'left', 'right'
        "duration": 3.0,         // 总持续时长（秒）
        "dodge_delay": 0.05,     // 按下方向键后，多久按下闪避键（秒），默认 0.05
        "jump_interval": 0.5,    // 跳跃间隔（秒），默认 0.5 秒跳一次
        "jump_press_time": 0.1   // 每次跳跃按键时长（秒），默认 0.1 秒
    }
    
    注意：使用的闪避键从全局配置 main.GAME_CONFIG["dodge_key"] 中读取
    """
    
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        # 解析参数
        try:
            if isinstance(argv.custom_action_param, str):
                params = json.loads(argv.custom_action_param)
            elif isinstance(argv.custom_action_param, dict):
                params = argv.custom_action_param
            else:
                logger.error(f"[RunWithJump] 参数类型错误: {type(argv.custom_action_param)}")
                return False
        except json.JSONDecodeError as e:
            logger.error(f"[RunWithJump] JSON 解析失败: {e}")
            logger.error(f"  参数内容: {argv.custom_action_param}")
            return False
        
        # 获取参数
        direction = params.get("direction", "w")
        duration = params.get("duration", 3.0)
        dodge_delay = params.get("dodge_delay", 0.05)
        jump_interval = params.get("jump_interval", 0.5)
        jump_press_time = params.get("jump_press_time", 0.1)
        
        # 从全局配置获取闪避键(现在是虚拟键码 int)
        dodge_vk = main.GAME_CONFIG.get("dodge_key", win32con.VK_SHIFT)
        
        logger.info("=" * 60)
        logger.info(f"[RunWithJump] 开始边跑边跳")
        logger.info(f"  方向: {direction}")
        logger.info(f"  总持续时长: {duration:.2f}秒")
        logger.info(f"  闪避键延迟: {dodge_delay:.3f}秒")
        logger.info(f"  跳跃间隔: {jump_interval:.2f}秒")
        logger.info(f"  跳跃按键时长: {jump_press_time:.3f}秒")
        logger.info(f"  使用闪避键: VK={dodge_vk} (0x{dodge_vk:02X})")
        
        try:
            # 获取窗口句柄
            hwnd = self._get_window_handle(context)
            if not hwnd:
                logger.error("[RunWithJump] 无法获取窗口句柄")
                return False
            
            # 创建输入辅助对象
            input_helper = PostMessageInputHelper(hwnd)
            
            # 获取方向键的虚拟键码
            direction_vk = input_helper.get_direction_vk(direction)
            
            logger.info(f"[RunWithJump] 方向键 VK={direction_vk}, 闪避键 VK={dodge_vk}")
            
            # 1. 按下方向键
            logger.info(f"[RunWithJump] 步骤 1: 按下方向键 '{direction}'")
            input_helper.key_down(direction_vk, activate=True)
            
            # 2. 短暂延迟后按下闪避键
            if dodge_delay > 0:
                logger.debug(f"[RunWithJump] 等待 {dodge_delay:.3f}秒...")
                time.sleep(dodge_delay)
            
            logger.info(f"[RunWithJump] 步骤 2: 按下闪避键 (VK=0x{dodge_vk:02X})")
            input_helper.key_down(dodge_vk, activate=False)
            
            # 3. 周期性跳跃，直到总时长结束
            logger.info(f"[RunWithJump] 步骤 3: 开始周期性跳跃...")
            start_time = time.time()
            jump_count = 0
            next_jump_time = start_time + jump_interval
            
            while True:
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                # 检查是否达到总时长
                if elapsed_time >= duration:
                    logger.info(f"[RunWithJump] 达到总时长 {duration:.2f}秒，停止跳跃")
                    break
                
                # 检查是否该跳跃了
                if current_time >= next_jump_time:
                    jump_count += 1
                    remaining_time = duration - elapsed_time
                    logger.info(f"[RunWithJump] -> 第 {jump_count} 次跳跃 (剩余: {remaining_time:.2f}秒)")
                    
                    # 按下空格键
                    input_helper.key_down(win32con.VK_SPACE, activate=False)
                    
                    # 保持按下状态
                    time.sleep(jump_press_time)
                    
                    # 释放空格键
                    input_helper.key_up(win32con.VK_SPACE)
                    
                    # 计算下一次跳跃时间
                    next_jump_time = current_time + jump_interval
                else:
                    # 短暂休眠，避免 CPU 占用过高
                    time.sleep(0.01)
            
            # 4. 释放闪避键
            logger.info(f"[RunWithJump] 步骤 4: 释放闪避键")
            input_helper.key_up(dodge_vk)
            
            # 5. 释放方向键
            logger.info(f"[RunWithJump] 步骤 5: 释放方向键")
            input_helper.key_up(direction_vk)
            
            logger.info(f"[RunWithJump] [OK] 完成边跑边跳 {duration:.2f}秒，共跳跃 {jump_count} 次")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"[RunWithJump] 发生异常: {e}", exc_info=True)
            # 尝试释放所有按键
            try:
                input_helper.key_up(win32con.VK_SPACE)
                input_helper.key_up(dodge_vk)
                input_helper.key_up(direction_vk)
            except:
                pass
            return False
