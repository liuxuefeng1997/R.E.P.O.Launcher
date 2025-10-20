import shutil
import subprocess

from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from data.appInfo import *
from lib.aria2c import Aria2cDownload, Aria2cManager
from lib.core import *
from lib.cos import COS
from data.api_setting import TencentCloud
from lib.game import CheckGame, Clear

from ui.download import DownloadWindow
from ui.fileCheck import fileCheckWindow
from ui.saveManager import SaveManagerWindow


class mainWindow(QMainWindow):

    def __init__(self):
        super(mainWindow, self).__init__()
        logging.info("初始化窗口中")
        logging.info(run_path)
        # 初始化图片资源
        self.Icon = QIcon(os.path.join(source_path, "repo.ico"))
        self.checkIcon = QIcon(os.path.join(source_path, "check.png"))
        self.emptyIcon = QIcon()
        # 初始化变量
        self.supported_update_channel = getCOSConfJsonObject(TencentCloud.Update.self_update_channel_list_url)
        self.down = None
        self.clear = None
        self.aria2c_manager = None
        self.chkUp = None
        self.cleanup_thread = None
        self.run_once = False  # 首次运行 Flag
        # 初始化aria2c
        self.setup_aria2c()
        # 设置窗口标题和大小
        self.setWindowTitle("R.E.P.O.启动器")
        self.setWindowIcon(self.Icon)
        self.resize(300, 224)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(self.width(), self.height())
        # 初始化托盘图标
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.Icon)
        # 窗口组件
        self.image_label = QLabel(self)
        self.image_label.setGeometry(5, 0, 295, 171)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                qproperty-alignment: AlignCenter;
            }
        """)

        self.button_start = QPushButton(self)
        self.button_start.setGeometry(10, 176, 280, 24)
        self.button_start.setText("启动游戏")
        self.button_start.clicked.connect(self.buttonStart_onClick)
        self.button_start.setEnabled(False)

        self.button_close = QPushButton(self)
        self.button_close.setGeometry(220, 176, 70, 24)
        self.button_close.setText("结束")
        self.button_close.clicked.connect(self.buttonClose_onClick)
        self.button_close.setHidden(True)
        # 托盘右键菜单
        self.trayMenu = QMenu(self)

        self.showAction = QAction(self)
        self.showAction.setText("隐藏")
        self.showAction.triggered.connect(self.show_tray_menu)
        self.trayMenu.addAction(self.showAction)

        self.trayMenu.addSeparator()

        self.startAction = QAction(self)
        self.startAction.setText("启动游戏")
        self.startAction.triggered.connect(self.trayStart_onClick)
        self.trayMenu.addAction(self.startAction)

        self.saveAction = QAction(self)
        self.saveAction.setText("存档管理器")
        self.saveAction.triggered.connect(self.buttonSaveManager_onClick)
        self.trayMenu.addAction(self.saveAction)

        self.trayMenu.addSeparator()

        self.channelMenu = QMenu(self)
        self.channelMenu.setTitle("切换更新通道")
        self.channelActions = {}
        if self.supported_update_channel:
            for channel, name, enable in self.supported_update_channel:
                self.channelActions[channel] = QAction(self)
                self.channelActions[channel].setText(name)
                self.channelActions[channel].triggered.connect(
                    lambda checked, ch=channel: self.changeChannel(ch)
                )
                self.channelActions[channel].setEnabled(enable)
                self.channelMenu.addAction(self.channelActions[channel])

        self.trayMenu.addMenu(self.channelMenu)

        self.chkAction = QAction(self)
        self.chkAction.setText("验证完整性")
        self.chkAction.triggered.connect(self.buttonCheck_onClick)
        self.trayMenu.addAction(self.chkAction)

        self.trayMenu.addSeparator()

        self.updateAction = QAction(self)
        self.updateAction.setText("检查更新")
        self.updateAction.triggered.connect(self.buttonUpdate_onClick)
        self.trayMenu.addAction(self.updateAction)

        self.aboutAction = QAction(self)
        self.aboutAction.setText("关于")
        self.aboutAction.triggered.connect(self.buttonAbout_onClick)
        self.trayMenu.addAction(self.aboutAction)

        self.trayMenu.addSeparator()

        self.quitAction = QAction(self)
        self.quitAction.setText("退出")
        self.quitAction.triggered.connect(lambda: self.close())
        self.trayMenu.addAction(self.quitAction)

        self.tray.setContextMenu(self.trayMenu)
        self.tray.activated.connect(self._tray)
        self.tray.setToolTip("R.E.P.O.启动器\n双击：显示/隐藏")
        self.tray.show()
        # 游戏检测
        self.chkGame = CheckGame()
        self.chkGame.run_stat.connect(self.gameCheck)
        self.chkGame.start()
        # 更新检查
        self.buttonUpdate_onClick()
        # 初始化状态栏
        self.statusBar = QStatusBar(self)
        self.statusBar.setGeometry(0, 202, 300, 22)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.showMessage("程序准备中")
        logging.info("窗口初始化结束")
        # 加载配置
        gui = readJson(os.path.join(config_path, "gui.json"))
        curr_channel = gui.get("channel", "release")
        # 初始化界面中的配置
        self.channelActions[curr_channel].setIcon(self.checkIcon)
        self.load_image(os.path.join(source_path, "logo.png"))

    # 加载主界面图片
    def load_image(self, image_path):
        """加载并显示图片"""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 缩放图片以适应标签大小
                self.image_label.setPixmap(
                    pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )
                logging.info("主图成功加载")
            else:
                self.image_label.setText("R.E.P.O. 启动器")
                logging.error("错误：主图加载失败，对象为空")
        except Exception as e:
            self.image_label.setText("R.E.P.O. 启动器")
            logging.error(f"错误，主图加载失败: {str(e)}")

    # 存档管理器按钮事件
    def buttonSaveManager_onClick(self):
        try:
            logging.info("开始启动存档管理器窗口")
            saveWin = SaveManagerWindow(parent=self)
            saveWin.show()
            saveWin.exec()
        except Exception as e:
            logging.error(f"打开存档管理器窗口失败: {e}")
            import traceback
            traceback.print_exc()

    # 切换更新通道
    def changeChannel(self, channel):
        logging.debug(channel)
        gui = readJson(os.path.join(config_path, "gui.json"))
        for key in self.channelActions:
            if key == channel:
                self.channelActions[key].setIcon(self.checkIcon)
            else:
                self.channelActions[key].setIcon(self.emptyIcon)
        gui["channel"] = channel
        writeJson(os.path.join(config_path, "gui.json"), gui)

    # 验证部分事件
    # 验证按钮按下，拉起验证窗口
    def buttonCheck_onClick(self):
        if not os.path.exists(os.path.join(run_path, f"{game_exe_name}.exe")):
            QMessageBox.warning(self, "警告", "请确保启动器已在游戏目录中，且目录中包含游戏主程序", QMessageBox.StandardButton.Yes)
            return
        if not network_check():
            QMessageBox.warning(self, "验证完整性", "网络错误，请检查网络设置", QMessageBox.StandardButton.Yes)
            return
        logging.info("开始启动验证窗口")
        try:
            chkWin = fileCheckWindow(parent=self)
            # 返回验证状态 isOk: bool, restore_list: list, dicts: dict
            chkWin.file_check.connect(self.file_check)
            chkWin.show()
            chkWin.exec()
        except Exception as e:
            logging.error(f"打开验证窗口失败: {e}")
            import traceback
            traceback.print_exc()

    # 检查流程结束
    def file_check(self, isOk: bool, restore_list: list, dicts: dict):
        if isOk:
            # 验证通过，直接拉起验证下载结束
            self.chkDownEnd(event=isOk, dicts=dicts)
        else:
            # 启动下载窗口
            logging.info("开始重新下载")
            try:
                # versions 改为函数内部获取
                d = DownloadWindow(keyList=restore_list, dicts=dicts, parent=self)
                d.download_signal.connect(self.chkDownEnd)
                d.show()
                d.exec()
            except Exception as e:
                logging.error(f"打开下载窗口失败: {e}")
                import traceback
                traceback.print_exc()

    # 验证下载结束回调 拉起清理，以清理空文件夹等
    def chkDownEnd(self, event, dicts):
        self.clear = Clear(dicts)
        self.clear.c_ok.connect(self.chkClrEnd)
        self.clear.c_progress.connect(self.clearProgress)
        self.clear.start()

    # 验证清理结束
    def chkClrEnd(self, event):
        self.statusBar.showMessage("验证完整性完成", 3*1000)

    # 检查更新按钮事件
    def buttonUpdate_onClick(self):
        # 更新检查
        self.chkUp = checkUpdate()
        self.chkUp.newLog.connect(self.updateLog)
        self.chkUp.start()

    # Aria2c 相关
    # 初始化 aria2c rpc
    def setup_aria2c(self):
        # 创建aria2c管理器
        self.aria2c_manager = Aria2cManager(
            rpc_port=6800
        )

        # 连接信号
        # self.aria2c_manager.status_changed.connect(self.on_aria2c_status_changed)
        self.aria2c_manager.rpc_ready.connect(self.on_rpc_ready)

        # 启动管理器
        self.aria2c_manager.start()

    # aria2c 就绪
    def on_rpc_ready(self, is_ready):
        if is_ready:
            self.statusBar.showMessage("下载引擎就绪", 3000)
            if self.button_close.isHidden():
                self.button_start.setEnabled(True)

    # 游戏运行状态检查回调
    def gameCheck(self, run_stat: bool):
        logging.info(f"游戏运行状态：{run_stat}")
        if run_stat:
            self.button_start.resize(210, 24)
            self.button_start.setEnabled(False)
            self.button_close.setHidden(False)
            self.chkAction.setEnabled(False)
            self.button_start.setText("游戏运行中...")
            self.startAction.setEnabled(False)
            self.startAction.setText("游戏运行中...")
        else:
            if self.run_once:
                self.button_start.resize(280, 24)
                self.button_start.setEnabled(True)
                self.button_close.setHidden(True)
                self.chkAction.setEnabled(True)
                self.button_start.setText("启动游戏")
                self.startAction.setEnabled(True)
                self.startAction.setText("启动游戏")
                if self.isHidden():
                    self.show_tray_menu()
        self.run_once = True

    # 更新检查回调
    def updateLog(self, version, log, channel):
        gui = readJson(os.path.join(config_path, "gui.json"))
        if channel == "release":
            buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        else:
            buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Ignore
        box = QMessageBox.question(self, "更新", f"发现新版本：{version}\n\n{log}\n\n要现在进行更新吗？", buttons)
        if box == QMessageBox.StandardButton.Yes:
            self.do_update(version)
        elif box == QMessageBox.StandardButton.Ignore:
            gui["skip_version"] = version
            writeJson(os.path.join(config_path, "gui.json"), gui)

    # 本体更新直接拉起 Aria2 下载
    def do_update(self, version):
        self.down = Aria2cDownload(uri=TencentCloud.Update.self_update_url, keys=f"{version}_update.data", isUpdate=True)
        self.down.isStart.connect(self.onUpdateStart)
        self.down.download.connect(self.onUpdate)
        self.down.complete.connect(self.onUpdateComplete)
        self.down.start()

    # 本体更新开始回调
    def onUpdateStart(self, event):
        self.statusBar.showMessage("开始下载更新")

    # 本体更新进度回调
    def onUpdate(self, progress: dict):
        self.statusBar.showMessage(f"下载：{progress.get('complete'): .2f} %")

    # 本体更新完成回调
    def onUpdateComplete(self, e, t, k: str):
        if e:
            self.statusBar.showMessage(f"更新文件下载完成，用时{t: .2f} 秒")
            if QMessageBox.question(self, "更新", "更新已下载，将自动重启完成更新", QMessageBox.StandardButton.Yes):
                try:
                    self.statusBar.showMessage("开始解压更新")
                    shutil.unpack_archive(os.path.join(run_path, f"{k}"), run_path, 'zip')
                    self.statusBar.showMessage("解压更新完成")
                except Exception as e:
                    logging.error(e)
                    QMessageBox.question(self, "更新", "更新文件解压失败，请稍后重新检查更新尝试", QMessageBox.StandardButton.Yes)
                    return
            if os.path.exists(os.path.join(run_path, f"{k}")):
                os.remove(os.path.join(run_path, f"{k}"))
            subprocess.Popen(
                f'start "R.E.P.O.启动器 | 更新" update.exe -n {k.replace("_update.data", "")}',
                shell=True,
                startupinfo=subprocess.STARTUPINFO(
                    dwFlags=subprocess.STARTF_USESHOWWINDOW,
                    wShowWindow=0
                )
            )
            self.close()

    # 重写关闭事件
    def closeEvent(self, event):
        self.statusBar.showMessage("正在结束程序")
        self.cleanup_thread = CleanupThread(self)
        self.cleanup_thread.finished.connect(lambda: self.finalClose(event))
        self.cleanup_thread.start()
        event.ignore()

    def finalClose(self, event):
        logging.debug(self.cleanup_thread.isRunning())
        event.accept()
        sys.exit(0)

    # 托盘菜单显示隐藏主程序功能
    def show_tray_menu(self):
        if self.isHidden():
            self.showAction.setText("隐藏")
            self.show()
        else:
            self.showAction.setText("显示")
            self.hide()

    # 托盘菜单鼠标事件
    def _tray(self, reason):
        logging.debug(f'tray-icon: {reason}')
        match f'{reason}':
            case "ActivationReason.DoubleClick":
                self.show_tray_menu()

    # 开始游戏按钮事件
    # 托盘
    def trayStart_onClick(self):
        if self.isHidden():
            self.show()
        QTimer.singleShot(500, lambda: self.buttonStart_onClick())

    # 主界面
    def buttonStart_onClick(self):
        if not os.path.exists(os.path.join(run_path, f"{game_exe_name}.exe")):
            QMessageBox.warning(self, "警告", "请确保启动器已在游戏目录中，且目录中包含游戏主程序", QMessageBox.StandardButton.Yes)
            return
        self.button_start.setEnabled(False)
        self.button_start.setText("准备启动游戏...")
        self.startAction.setEnabled(False)
        self.startAction.setText("准备启动...")
        net = network_check()
        logging.info(f"网络连接: {net}")
        if net:
            self.statusBar.showMessage("正在准备更新")
            file_list = COS(TencentCloud.Update.mod_bukkit, TencentCloud.Update.mod_region).get_file_list()
            # dicts 改为本地变量以保持获取清单最新
            dicts = {}
            # 去除文件夹，因为不需要下载
            for file_info in file_list:
                if file_info["Key"][-1] != "/":
                    dicts[file_info["Key"]] = file_info["ETag"]
            self.statusBar.showMessage("获取文件清单")
            # 读取本地缓存的文件校验值
            versions = readJson(os.path.join(run_path, "version.json"))
            # 生成更新 KeyList
            keyList = []
            for key in dicts.keys():
                if dicts.get(key, "") != versions.get(key, ""):
                    self.statusBar.showMessage(key)
                    keyList.append(key)
            self.statusBar.showMessage("正在准备下载", 3000)
            if len(keyList) > 0:
                # 启动下载窗口
                logging.info("开始启动下载窗口")
                try:
                    d = DownloadWindow(keyList=keyList, dicts=dicts, parent=self)
                    d.download_signal.connect(self.downloadEnd)
                    d.show()
                    d.exec()
                except Exception as e:
                    logging.error(f"打开下载窗口失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # 没有更新
                self.downloadEnd(True, dicts=dicts)
                return
        else:
            QMessageBox.warning(self, "启动", "网络错误，请检查网络设置", QMessageBox.StandardButton.Yes)

    # Mod 更新下载结束回调，由下载窗口拉起
    def downloadEnd(self, event, dicts):
        # 清理
        self.clear = Clear(dicts)
        self.clear.c_ok.connect(self.clearEnd)
        self.clear.c_progress.connect(self.clearProgress)
        self.clear.start()

    # 更新结束清理完成回调
    def clearEnd(self, e):
        self.statusBar.showMessage("更新清理完成，准备启动游戏", 3000)
        logging.debug(e)
        QTimer.singleShot(3000, lambda: self.startGame())

    # 清理进度回调（更新和验证完整性共用，因为状态栏只有一个）
    def clearProgress(self, e):
        self.statusBar.showMessage(e)

    # 通过协议启动游戏
    def startGame(self):
        # os.system("start steam://run/"f"{game_appId}")
        os.startfile("steam://run/"f"{game_appId}")
        if not self.isHidden():
            self.show_tray_menu()

    # 关闭按钮事件
    def buttonClose_onClick(self):
        if QMessageBox.question(self, "关闭", "确定要强制结束游戏吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            pid = checkRun(f"{game_exe_name}.exe")
            if pid:
                psutil.Process(pid).kill()

    # 关于按钮事件
    def buttonAbout_onClick(self):
        QMessageBox.information(self, "关于", f'版本: {ver}')
