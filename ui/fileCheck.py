from PyQt6.QtWidgets import *
from lib.core import *
from lib.crc64 import CrcCheck


class fileCheckWindow(QDialog):
    file_check = pyqtSignal(bool, list, dict)

    def send(self, isOk: bool, restore_list: list, dicts: dict):
        self.file_check.emit(isOk, restore_list, dicts)

    def __init__(self, parent=None):
        super(fileCheckWindow, self).__init__(parent)
        # 窗口组件
        self.setWindowTitle(self.tr("验证完整性"))
        # self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.resize(220, 100)
        self.label = QLabel(self)
        self.label.setGeometry(10, 5, 200, 30)
        self.label.setWordWrap(True)  # 启用自动换行
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setText("正在准备验证...")
        self.progressBarA = QProgressBar(self)
        self.progressBarA.setGeometry(10, 40, 200, 25)
        self.progressBarA.setMinimum(0)
        self.progressBarA.setMaximum(100)
        self.progressBarA.setValue(0)
        self.progressBarB = QProgressBar(self)
        self.progressBarB.setGeometry(10, 70, 200, 25)
        self.progressBarB.setMinimum(0)
        self.progressBarB.setMaximum(100)
        self.progressBarB.setValue(0)
        # 初始化验证
        self.chk = CrcCheck()
        self.chk.progress_one.connect(self.onefileProgress)
        self.chk.progress_all.connect(self.allfileProgress)
        self.chk.complete_list.connect(self.onComplete)
        self.chk.start()

    # {
    #     "dir": hasdir,
    #     "file": filename,
    #     "complete": 0,
    #     "find": False
    # }
    def onefileProgress(self, data: dict):
        logging.debug(data)
        dir_name = data.get("dir")
        file_name = data.get("file")
        complete = data.get("complete")
        find = data.get("find")
        self.label.setText(f"正在验证 {dir_name}{file_name}{'' if find else '：失败'}")
        self.progressBarA.setValue(complete)

    # {
    #     "file_sum": file_sum,
    #     "file_max": file_maxsum,
    #     "complete": chk_complete
    # }
    def allfileProgress(self, data: dict):
        logging.debug(data)
        complete = data.get("complete")
        self.progressBarB.setValue(complete)

    # 校验结束回调 restore_list=需要恢复的文件列表，dicts=完整文件清单
    def onComplete(self, restore_list: list, dicts: dict):
        logging.debug(restore_list)
        if len(restore_list) > 0:
            self.label.setText(f"验证结束，其中 {len(restore_list)} 个文件验证失败，准备重新获取")
        else:
            self.label.setText(f"验证完成，文件没有问题")
        # 延迟 1 秒执行发送事件，解决检查窗口未关闭，下载窗口就已经出现的问题
        QTimer.singleShot(1000, lambda: self.do_send_complete(restore_list, dicts))

    def do_send_complete(self, restore_list: list, dicts: dict):
        self.send(not len(restore_list) > 0, restore_list, dicts)
        self.close()

    def closeEvent(self, e):
        if self.chk.isRunning():
            self.chk.terminate()
        e.accept()
