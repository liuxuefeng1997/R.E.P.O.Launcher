from PyQt6.QtWidgets import *

from lib.aria2c import Aria2cDownload
from lib.core import *


class DownloadWindow(QDialog):
    download_signal = pyqtSignal(bool, dict)

    # 发送下载完成，event 固定为 true，同时传回完整文件清单以备其他功能使用
    def send(self, dicts: dict):
        self.download_signal.emit(True, dicts)

    def __init__(self, keyList, dicts, parent=None):
        super(DownloadWindow, self).__init__(parent)
        self.versions = readJson(os.path.join(run_path, "version.json"))
        self.dicts = dicts
        self.mod = None
        self.file_sum = 0
        self.file_key = ""
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
        self.mod.start()

    def onAdd(self, s):
        self.label.setText(s)

    def onMod(self, progress: dict):
        curr_key = progress.get('key')
        if self.file_key != curr_key:
            self.file_sum += 1
            self.progressBarB.setValue(self.file_sum)
            self.label.setText(curr_key)
        logging.debug(curr_key)
        self.versions[curr_key] = self.dicts.get(curr_key)
        writeJson(os.path.join(run_path, "version.json"), self.versions)
        comp = progress.get('complete')
        c = int(comp) if comp else 100
        self.progressBarA.setValue(c)

    def onModComplete(self, e, t, v):
        if e:
            self.versions = {}
            self.label.setText("下载完成")
        QTimer(self).singleShot(1000, lambda: self.close())

    def closeEvent(self, e):
        self.send(self.dicts)
        if self.mod.isRunning():
            self.mod.terminate()
        e.accept()
