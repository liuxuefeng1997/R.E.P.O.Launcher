import getopt
import os
import shutil
import sys
import time

import psutil

from data.appInfo import app_name

EXE_NAME = "R.E.P.O.Launcher.exe"


def checkRun(process_name):
    for process in psutil.process_iter(['name']):
        if process.info['name'] == process_name:
            return True
    return False


if __name__ == '__main__':
    # 以脚本所在目录为基准，避免 cwd 不对导致删错/写错位置
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    target_exe = os.path.join(base_dir, EXE_NAME)
    backup_exe = f"{target_exe}.bak"

    opts = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:", ["new"])
    except getopt.GetoptError:
        print()
    if opts:
        for opt, arg in opts:
            if opt in ("-n", "--new"):
                if os.path.exists(arg):
                    print(f"[{app_name} | 更新] 准备开始更新")
                    # 等待旧进程退出；超时则中止，避免强删被占用的 exe
                    for s in range(1, 60):
                        if checkRun(EXE_NAME):
                            print(f"[{app_name} | 更新] 等待程序结束 {s}")
                        else:
                            break
                        time.sleep(1)
                    else:
                        print(f"[{app_name} | 更新] 等待超时，{EXE_NAME} 仍在运行，更新已取消")
                        sys.exit(1)
                    print(f"[{app_name} | 更新] 正在更新至版本：{arg}")
                    # 安全替换：旧文件先改名为 .bak，成功后再删除；失败则回滚
                    try:
                        if os.path.exists(target_exe):
                            if os.path.exists(backup_exe):
                                os.remove(backup_exe)
                            os.rename(target_exe, backup_exe)
                        shutil.move(arg, target_exe)
                    except Exception as e:
                        print(f"[{app_name} | 更新] 更新失败：{e}")
                        if not os.path.exists(target_exe) and os.path.exists(backup_exe):
                            os.rename(backup_exe, target_exe)
                            print(f"[{app_name} | 更新] 已回滚旧版本")
                        sys.exit(1)
                    if os.path.exists(backup_exe):
                        os.remove(backup_exe)
                    print(f"[{app_name} | 更新] 更新完成，准备重启")
                    for s in reversed(range(1, 60)):
                        print(f"[{app_name} | 更新] 准备重启 {s}")
                        time.sleep(1)
                    os.startfile(target_exe)
                else:
                    print("更新数据未找到")
            else:
                print("参数错误")
    else:
        print("至少包含 -n, --new 参数")
