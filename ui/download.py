from PyQt6.QtWidgets import *

from lib.aria2c import Aria2cDownload
from lib.core import *


class DownloadWindow(QDialog):
    download_signal = pyqtSignal(bool, dict)

    # 发送下载结束事件，并传回完整文件清单以备其他功能使用
    def send(self, event: bool, dicts: dict):
        self.download_signal.emit(event, dicts)

    def __init__(self, keyList, dicts, parent=None):
        super(DownloadWindow, self).__init__(parent)
        self.versions = readJson(os.path.join(run_path, "version.json"))
        self.dicts = dicts
        self.mod = None
        self.file_sum = 0
        self.file_key = ""
        self.ok = False
        # 窗口组件
        self.setWindowTitle("更新")
        # self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.resize(220, 100)
        self.setFixedSize(self.width(), self.height())
        self.label = QLabel(self)
        self.label.setGeometry(10, 5, 200, 30)
        self.label.setWordWrap(True)  # 启用自动换行
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setText("正在准备更新...")
        self.progressBarA = QProgressBar(self)
        self.progressBarA.setGeometry(10, 40, 200, 25)
        self.progressBarA.setMinimum(0)
        self.progressBarA.setMaximum(100)
        self.progressBarA.setValue(0)
        self.progressBarB = QProgressBar(self)
        self.progressBarB.setGeometry(10, 70, 200, 25)
        self.progressBarB.setMinimum(0)
        self.progressBarB.setMaximum(len(keyList))
        self.progressBarB.setValue(0)
        # 初始化下载
        self.mod = Aria2cDownload(uri=TencentCloud.Update.mod_update_url, keys=keyList)
        # self.mod.isStart.connect(self.onModStart)
        self.mod.download.connect(self.onMod)
        self.mod.complete.connect(self.onModComplete)
        self.mod.add_status.connect(self.onAdd)
        self.mod.file_complete.connect(self.onFileComplete)
        self.mod.start()

    def onAdd(self, s):
        self.label.setText(s)

    def onMod(self, progress: dict):
        curr_key = progress.get('key')
        if self.file_key != curr_key:
            self.file_key = curr_key
            self.label.setText(curr_key)
        logging.debug(curr_key)
        comp = progress.get('complete')
        c = int(comp) if comp is not None else 100
        self.progressBarA.setValue(c)

    # 单文件下载结束：仅成功时写入版本标记，便于中断后跳过已更新文件
    def onFileComplete(self, key: str, ok: bool):
        if not ok:
            return
        self.file_sum += 1
        self.progressBarB.setValue(self.file_sum)
        etag = self.dicts.get(key)
        if etag is not None:
            self.versions[key] = etag
            writeJson(os.path.join(run_path, "version.json"), self.versions)

    def onModComplete(self, e, t, v):
        self.ok = bool(e)
        if self.ok:
            self.label.setText("下载完成")
        else:
            self.label.setText("下载失败")
        QTimer.singleShot(1000, self.close)

    def closeEvent(self, e):
        self.send(self.ok, self.dicts)
        if self.mod is not None and self.mod.isRunning():
            self.mod.stop_download()
            if not self.mod.wait(5000):
                self.mod.terminate()
                self.mod.wait(1000)
        e.accept()
