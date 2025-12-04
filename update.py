import getopt
import os.path
import sys
import time

import psutil
from termcolor import colored


def checkRun(process_name):
    for process in psutil.process_iter(['name']):
        if process.info['name'] == process_name:
            return True
    return False


if __name__ == '__main__':
    opts = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "n:", ["new"])
    except getopt.GetoptError:
        print()
    if opts:
        for opt, arg in opts:
            if opt in ("-n", "--new"):
                if os.path.exists(arg):
                    print(f"[{colored('本体更新', 'cyan')}] 准备开始更新")
                    for s in range(1, 60):
                        if checkRun("R.E.P.O.Launcher.exe"):
                            print(f"[{colored('本体更新', 'cyan')}] 等待程序结束 {s}")
                        else:
                            break
                        time.sleep(1)
                    print(f"[{colored('本体更新', 'cyan')}] 正在更新至版本：{arg}")
                    if os.path.exists("R.E.P.O.Launcher.exe"):
                        os.remove("R.E.P.O.Launcher.exe")
                    os.rename(arg, "R.E.P.O.Launcher.exe")
                    print(f"[{colored('本体更新', 'green')}] 更新完成，准备重启")
                    for s in reversed(range(1, 3)):
                        print(f"[{colored('本体更新', 'cyan')}] 准备重启 {s}")
                        time.sleep(1)
                    os.system('start R.E.P.O.Launcher.exe')
                else:
                    print("更新数据未找到")
            else:
                print("参数错误")
    else:
        print("至少包含 -n, --new 参数")
