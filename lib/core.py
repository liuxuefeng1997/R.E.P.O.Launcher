import datetime
import hashlib
import json
import logging
import time
import winreg
import psutil
import requests as requests
from PyQt6.QtCore import *

from data.api_setting import TencentCloud
from data.appInfo import ver, game_appId, game_name, patch_type
from lib.path import *

run_path = os.path.abspath('.')
config_path = os.path.join(run_path, "config")
backup_path = os.path.join(run_path, "backups")
plugin_path = resource_path("plugins")
source_path = resource_path("sources")
localLow_path = os.path.expandvars(r"%localappdata%Low")
game_save_path = os.path.join(localLow_path, r"semiwork\Repo\saves")
aria2_path = os.path.join(plugin_path, "aria2c.exe")
self_uuid = hashlib.md5(f"{game_name}{game_appId}{patch_type}{run_path}".encode("utf8")).hexdigest()


def init_log():
    NOW_TIME_WITH_NO_SPACE = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
    if getattr(sys, 'frozen', False):
        if not os.path.exists(r'.\logs'):
            os.mkdir(r'.\logs')
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s][%(levelname)s] %(message)s',
            handlers=[logging.FileHandler(filename=rf'.\logs\log_{NOW_TIME_WITH_NO_SPACE}.txt', mode='w', encoding='utf-8')]
        )
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s][%(levelname)s] %(message)s'
        )


def network_check():
    try:
        requests.get("https://test.ipw.cn")
        chk = True
    except Exception as e:
        logging.debug(e)
        chk = False
    return chk


def readJson(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf8") as f:
            r = json.loads(f.read())
            f.close()
    except FileNotFoundError:
        logging.debug(f"文件不存在 {path}")
        r = {}
    return r


def writeJson(path: str, json_object: dict) -> bool:
    try:
        with open(path, "w", encoding="utf8") as f:
            f.write(json.dumps(json_object, ensure_ascii=False, indent=4))
            f.close()
        r = True
    except Exception as e:
        logging.debug(e)
        r = False
    return r


def checkRun(process_name):
    for process in psutil.process_iter(['name', 'pid']):
        if process.info['name'] == process_name:
            return process.info['pid']
    return False


def get_path_as_reg(steamAppID):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App {steamAppID}')
        value_name = "InstallLocation"
        data, type_no = winreg.QueryValueEx(key, value_name)
        # print(data)  # 输出：no 1
        winreg.CloseKey(key)
        return f'{data}'
    except FileNotFoundError as e:
        print(f"\033[30m{e}\033[0m")
        return None


def getCOSConfJsonObject(uri: str) -> dict:
    try:
        jsonObject = requests.get(uri).json()
    except Exception as s:
        logging.error(s)
        jsonObject = {}
    return jsonObject


def remove_empty_folders(root_dir):
    for root, dirs, _ in os.walk(root_dir, topdown=False):  # 自底向上遍历
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                os.rmdir(dir_path)  # 尝试删除空文件夹
                # print(f"已删除空文件夹: {dir_path}")
            except Exception as e:
                if not run_path:
                    logging.debug(e)
                pass  # 忽略非空文件夹


def generateFilenameWithDatetime(prefix="", suffix="", extension="", include_time=True):
    """
    生成包含当前日期时间的文件名

    参数:
        prefix (str): 文件名前缀
        suffix (str): 文件名后缀
        extension (str): 文件扩展名(不需要加点)
        include_time (bool): 是否包含时间部分

    返回:
        str: 生成的完整文件名
    """
    # 获取当前日期时间
    now = datetime.datetime.now()
    # 格式化日期时间
    if include_time:
        datetime_str = now.strftime("%Y%m%d_%H%M%S")  # 格式: 20230805_143022
    else:
        datetime_str = now.strftime("%Y%m%d")  # 格式: 20230805
    # 构建文件名
    filename = f"{prefix}{datetime_str}{suffix}"
    # 添加扩展名
    if extension:
        filename = f"{filename}.{extension.lstrip('.')}"

    return filename


class checkUpdate(QThread):
    newLog = pyqtSignal(str, str, str)

    def __init__(self):
        super(checkUpdate, self).__init__()

    def run(self):
        version: dict = getCOSConfJsonObject(TencentCloud.Update.self_update_manifest_url)
        logging.debug(version)
        gui = readJson(os.path.join(config_path, "gui.json"))
        channel = gui.get("channel", "release")
        newVer = version.get(channel, "0")
        newInt = int(newVer.replace("v", "").replace(".", ""))
        oldInt = int(ver.replace("v", "").replace(".", ""))
        if newInt > oldInt:
            skip = gui.get("skip_version", "0")
            skipInt = int(skip.replace("v", "").replace(".", ""))
            show_upTip = False
            if channel == "release":
                show_upTip = True
            else:
                release = version.get("release", "0")
                releaseInt = int(release.replace("v", "").replace(".", ""))
                if newInt > skipInt:
                    show_upTip = True
                else:
                    if releaseInt > oldInt:
                        show_upTip = True
                        newVer = release
                        channel = "release"

            if show_upTip:
                self.sendLog(newVer, version.get(f"updateLog.{channel}", "无更新日志"), channel)
            else:
                logging.info(f"{newVer} 更新已跳过")

    def sendLog(self, version: str, log: str, channel: str):
        self.newLog.emit(version, log, channel)


class CleanupThread(QThread):
    def __init__(self, parent):
        super(CleanupThread, self).__init__()
        self.parent = parent

    def run(self):
        try:
            logging.info("进行后台执行清理线程")
            self.parent.chkGame.stop_checking()
            logging.info("正在关闭aria2c...")
            if self.parent.aria2c_manager:
                self.parent.aria2c_manager.stop_aria2c()
            pid = checkRun("aria2c.exe")
            if pid:
                psutil.Process(pid).kill()
            logging.info("程序已结束")
        except Exception as e:
            logging.error(e)
