from data.appInfo import game_exe_name
from lib.core import *


class CheckGame(QThread):
    run_stat = pyqtSignal(bool)

    def __init__(self):
        super(CheckGame, self).__init__()
        self._is_running = True  # 添加运行控制标志

    def run(self):
        old_stat = None
        while self._is_running:  # 使用运行控制标志
            stat = checkRun(f"{game_exe_name}.exe")
            if stat != old_stat:
                if stat:
                    self.send(True)
                else:
                    self.send(False)
                old_stat = stat

    def send(self, run_stat: bool):
        self.run_stat.emit(run_stat)

    def stop_checking(self):
        """安全停止线程的方法"""
        self._is_running = False
        if self.isRunning():
            self.wait(1000)  # 等待最多3秒线程结束


class Clear(QThread):
    c_ok = pyqtSignal(bool)
    c_progress = pyqtSignal(str)

    def __init__(self, dicts: dict):
        super(Clear, self).__init__()
        self.versions = readJson(os.path.join(run_path, "version.json"))
        self.dicts = dicts

    def run(self):
        try:
            del_key = []
            self.sendProgress("开始清理")
            for key in self.versions.keys():
                if key not in self.dicts.keys():
                    self.sendProgress(f"清理：{key}")
                    if os.path.exists(os.path.join(run_path, key)):
                        os.remove(os.path.join(run_path, key))
                    del_key.append(key)
            for key in del_key:
                self.versions.pop(key)
                writeJson(os.path.join(run_path, "version.json"), self.versions)
            r = self.remove_empty_folders(run_path)
            if r > 0:
                self.sendProgress(f"已删除 {r} 个空文件夹")
            self.sendOk(True)
        except Exception as e:
            logging.error(e)

    def sendOk(self, run_stat: bool):
        self.c_ok.emit(run_stat)

    def sendProgress(self, key: str):
        self.c_progress.emit(key)

    def remove_empty_folders(self, path):
        """删除空文件夹（包括嵌套的空文件夹）"""
        removed_count = 0

        # 自底向上遍历，确保先处理子文件夹
        for root, dirs, files in os.walk(path, topdown=False):
            # 如果当前文件夹为空
            if not dirs and not files:
                try:
                    os.rmdir(root)
                    del_dir = os.path.basename(root)
                    self.sendProgress(f"已删除空文件夹: {del_dir}")
                    logging.info(f"[清理模块] 已删除空文件夹: {root}")
                    removed_count += 1
                except OSError as e:
                    logging.debug(f"[清理模块] 删除失败 {root}: {e}")

        return removed_count
