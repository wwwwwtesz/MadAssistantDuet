# 测试 PyInstaller spec 文件中的变量
import os
import sys

print(f"Current directory: {os.getcwd()}")
print(f"sys.argv: {sys.argv}")

# 模拟 PyInstaller 设置 SPECPATH
SPECPATH = r"d:\WorkSpace\MdaDuetAssistant\tools\MaaAgent.spec"

print(f"\nSPECPATH: {SPECPATH}")
print(f"os.path.dirname(SPECPATH): {os.path.dirname(SPECPATH)}")
print(f"os.path.abspath(SPECPATH): {os.path.abspath(SPECPATH)}")
print(f"os.path.dirname(os.path.abspath(SPECPATH)): {os.path.dirname(os.path.abspath(SPECPATH))}")

spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
spec_root = os.path.dirname(spec_dir)

print(f"\nspec_dir: {spec_dir}")
print(f"spec_root: {spec_root}")
print(f"agent/main.py: {os.path.join(spec_root, 'agent', 'main.py')}")
print(f"exists: {os.path.exists(os.path.join(spec_root, 'agent', 'main.py'))}")
