import shutil
import subprocess

from PyQt6.QtGui import *
from lib.aria2c import Aria2cDownload, Aria2cManager
from lib.core import *
from lib.cos import COS
from data.api_setting import TencentCloud
from lib.game import CheckGame, Clear

from ui.download import DownloadWindow
from ui.fileCheck import fileCheckWindow
from ui.messageBoxies import *
from ui.saveManager import SaveManagerWindow


class mainWindow(QMainWindow):

    def __init__(self):
        super(mainWindow, self).__init__()
        logging.info("[主窗口] 初始化窗口中")
        logging.info(run_path)
        # 初始化图片资源=============================================
        self.Icon = QIcon(os.path.join(source_path, "repo.ico"))
        self.checkIcon = QIcon(os.path.join(source_path, "check.png"))
        self.emptyIcon = QIcon()
        # 初始化变量=================================================
        self.supported_update_channel = getCOSConfJsonObject(TencentCloud.Update.self_update_channel_list_url)
        self.down = None
        self.clear = None
        self.aria2c_manager = None
        self.chkUp = None
        self.cleanup_thread = None
        self.run_once = False  # 首次运行 Flag
        self._isUpdate = False
        self.dev_flag = 0
        self.notification = {}
        # 初始化aria2c================================================
        self.setup_aria2c()
        # 设置窗口标题和大小============================================
        self.setWindowTitle(app_name)
        self.setWindowIcon(self.Icon)
        self.resize(300, 224)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        # 初始化托盘图标================================================
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.Icon)
        # 窗口组件=====================================================
        self.image_label = QLabel(self)
        self.image_label.setGeometry(5, 0, 295, 171)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                qproperty-alignment: AlignCenter;
            }
        """)
        self.image_label.mousePressEvent = self.clickImage

        self.button_start = QPushButton(self)
        self.button_start.setGeometry(10, 176, 280, 24)
        self.button_start.setText("启动游戏")
        self.button_start.clicked.connect(self.gameStart_onClick)
        self.button_start.setEnabled(False)

        self.button_close = QPushButton(self)
        self.button_close.setGeometry(220, 176, 70, 24)
        self.button_close.setText("结束")
        self.button_close.clicked.connect(self.buttonClose_onClick)
        self.button_close.setHidden(True)
        # 托盘右键菜单=====================================================
        self.trayMenu = QMenu(self)

        self.showAction = QAction(self)
        self.showAction.setText("隐藏")
        self.showAction.triggered.connect(self.show_tray_menu)
        self.trayMenu.addAction(self.showAction)

        self.trayMenu.addSeparator()

        self.startAction = QAction(self)
        self.startAction.setText("启动游戏")
        self.startAction.triggered.connect(self.gameStart_onClick)
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

        # 设置菜单-开始==========================================
        self.optionMenu = QMenu(self)
        self.optionMenu.setTitle("选项")

        self.clearMenu = QMenu(self)
        self.clearMenu.setTitle("清除记住")

        self.rememberAction = QAction(self)
        self.rememberAction.setText("关闭选项")
        self.rememberAction.triggered.connect(self.clear_remember)
        self.clearMenu.addAction(self.rememberAction)

        self.posAction = QAction(self)
        self.posAction.setText("窗口位置")
        self.posAction.triggered.connect(self.clear_pos)
        self.clearMenu.addAction(self.posAction)

        self.optionMenu.addMenu(self.clearMenu)
        self.trayMenu.addMenu(self.optionMenu)
        # 设置菜单-结束===========================================
        # 开发菜单-开始==========================================
        self.devMenu = QMenu(self)
        self.devMenu.setTitle("开发")

        self.logDirAction = QAction(self)
        self.logDirAction.setText("日志目录")
        self.logDirAction.triggered.connect(self.openLogDir)
        self.devMenu.addAction(self.logDirAction)

        self.gameDirAction = QAction(self)
        self.gameDirAction.setText("游戏目录")
        self.gameDirAction.triggered.connect(self.openGameDir)
        self.devMenu.addAction(self.gameDirAction)

        self.saveDirAction = QAction(self)
        self.saveDirAction.setText("存档目录")
        self.saveDirAction.triggered.connect(self.openSaveDir)
        self.devMenu.addAction(self.saveDirAction)

        self.trayMenu.addMenu(self.devMenu)
        # 开发菜单-结束===========================================

        self.aboutAction = QAction(self)
        self.aboutAction.setText("关于")
        self.aboutAction.triggered.connect(self.buttonAbout_onClick)
        self.trayMenu.addAction(self.aboutAction)

        self.trayMenu.addSeparator()

        self.quitAction = QAction(self)
        self.quitAction.setText("退出")
        self.quitAction.triggered.connect(lambda: self.tray_close())
        self.trayMenu.addAction(self.quitAction)

        self.tray.setContextMenu(self.trayMenu)
        self.tray.activated.connect(self._tray)
        self.tray.setToolTip(f"{app_name}\n双击：显示/隐藏")
        self.tray.messageClicked.connect(self.on_notification_clicked)
        self.tray.show()
        # 游戏检测=====================================================
        self.chkGame = CheckGame()
        self.chkGame.run_stat.connect(self.gameCheck)
        self.chkGame.start()
        # 初始化状态栏==================================================
        self.statusBar = QStatusBar(self)
        self.statusBar.setGeometry(0, 202, 300, 22)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.showMessage("程序准备中")
        logging.info("[主窗口] 窗口初始化结束")
        # 初始化更新通道================================================
        curr_channel = "release"
        if config.read("gui.json", "update", "channel", "release") in self.channelActions.keys():
            curr_channel = config.read("gui.json", "update", "channel", "release")
        # 初始化界面中的配置=============================================
        self.changeChannel(curr_channel)
        self.load_image(os.path.join(source_path, "logo.png"))
        self.devMenu.menuAction().setVisible(False)
        # 初始化界面位置配置=============================================
        self.init_pos()

    def init_pos(self):
        win_x = config.read("gui.json", "position", "x")
        win_y = config.read("gui.json", "position", "y")
        screen_w = self.window().screen().geometry().width()
        screen_h = self.window().screen().geometry().height()
        screens = len(QApplication.screens())
        screen = config.read("gui.json", "screen", "geometry", "0x0,0")
        if win_x and screen == f"{screen_w}x{screen_h}, {screens}":
            self.move(win_x, win_y)
        config.write("gui.json", "screen", "geometry", f"{screen_w}x{screen_h}, {screens}")

    def clear_pos(self):
        config.write("gui.json", "screen", "geometry")
        self.send_notification("选项", "记住的窗口位置已清除，下次启动生效", 3000)

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
                logging.info("[主窗口] 主图成功加载")
            else:
                self.image_label.setText(app_name)
                logging.error("[主窗口] 错误：主图加载失败，对象为空")
        except Exception as e:
            self.image_label.setText(app_name)
            logging.error(f"[主窗口] 错误，主图加载失败: {str(e)}")

    # 发送系统通知
    def send_notification(self, _title: str, _message: str, _showTime=5000, _noticeLevel="Info", _event=None):
        """
        发送系统通知
        :param _title: 通知标题
        :param _message: 通知内容
        :param _showTime: 显示时间（ms）
        :param _noticeLevel: 通知类型（Info | Warn | Error）
        :param _event: 通知点击事件执行函数
        """
        if _noticeLevel == "Warn":
            _sys_msg_icon = QSystemTrayIcon.MessageIcon.Warning
        elif _noticeLevel == "Error":
            _sys_msg_icon = QSystemTrayIcon.MessageIcon.Critical
        else:
            _sys_msg_icon = QSystemTrayIcon.MessageIcon.Information
        self.notification = {
            "title": _title,
            "msg": _message,
            "event": _event
        }
        logging.info(f"[通知模块] 发送系统通知 {_title}: {_message} | {_noticeLevel}")
        self.tray.showMessage(
            _title,
            _message,
            _sys_msg_icon,
            _showTime  # 显示时长（毫秒）
        )

    # 通知点击事件
    def on_notification_clicked(self):
        def _example():
            pass
        if self.notification:
            logging.info(f"[通知模块] 用户点击通知 {self.notification.get('title')}: {self.notification.get('msg')}")
            func = self.notification.get("event", None)
            if type(func) == type(_example):
                logging.info("[通知模块] 此通知存在事件函数，开始执行")
                try:
                    func()
                except Exception as e:
                    logging.error(f"[通知模块] 执行事件函数出错：{e}")
        self.notification = {}
        logging.info("[通知模块] 通知事件处理结束")

    # 开发入口
    def clickImage(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dev_flag >= 9:
                if self.dev_flag == 9:
                    self.statusBar.showMessage("开发菜单已启用，下次启动失效", 3*1000)
                    self.send_notification(app_name, "开发菜单已启用，下次启动失效", 3000)
                    self.devMenu.menuAction().setVisible(True)
                    self.dev_flag += 1
            else:
                if self.dev_flag >= 3:
                    self.statusBar.showMessage(f"再点击 {9 - self.dev_flag} 次，启用开发菜单", 3 * 1000)
                self.dev_flag += 1

    def openLogDir(self):
        logging.info(f"[DEV] 打开日志目录: {log_path} | {self.dev_flag == 9}")
        try:
            os.startfile(log_path)
        except Exception as e:
            logging.debug(f"[DEV] {e}")

    def openSaveDir(self):
        logging.info(f"[DEV] 打开存档目录: {game_save_path} | {self.dev_flag == 9}")
        try:
            os.startfile(game_save_path)
        except Exception as e:
            logging.debug(f"[DEV] {e}")

    def openGameDir(self):
        logging.info(f"[DEV] 打开游戏目录: {run_path} | {self.dev_flag == 9}")
        try:
            os.startfile(run_path)
        except Exception as e:
            logging.debug(f"[DEV] {e}")

    # 存档管理器按钮事件
    def buttonSaveManager_onClick(self):
        try:
            logging.info("[主窗口] 开始启动存档管理器窗口")
            saveWin = SaveManagerWindow(parent=self)
            saveWin.show()
            saveWin.exec()
        except Exception as e:
            logging.error(f"[主窗口] 打开存档管理器窗口失败: {e}")
            import traceback
            traceback.print_exc()

    # 切换更新通道
    def changeChannel(self, channel):
        logging.debug(channel)
        for key in self.channelActions:
            if key == channel:
                self.channelActions[key].setIcon(self.checkIcon)
            else:
                self.channelActions[key].setIcon(self.emptyIcon)
        config.write("gui.json", "update", "channel", channel)

    # 验证部分事件
    # 验证按钮按下，拉起验证窗口
    def buttonCheck_onClick(self):
        self.chkAction.setEnabled(False)
        if not os.path.exists(os.path.join(run_path, f"{game_exe_name}.exe")):
            QMessageBox.warning(self, "警告", "请确保启动器已在游戏目录中，且目录中包含游戏主程序", QMessageBox.StandardButton.Yes)
            self.chkAction.setEnabled(True)
            return
        if not network_check():
            QMessageBox.warning(self, "验证完整性", "网络错误，请检查网络设置", QMessageBox.StandardButton.Yes)
            self.chkAction.setEnabled(True)
            return
        logging.info("[主窗口] 开始启动验证窗口")
        try:
            chkWin = fileCheckWindow(parent=self)
            # 返回验证状态 isOk: bool, restore_list: list, dicts: dict
            chkWin.file_check.connect(self.file_check)
            chkWin.show()
            chkWin.exec()
        except Exception as e:
            logging.error(f"[主窗口] 打开验证窗口失败: {e}")
            import traceback
            traceback.print_exc()

    # 检查流程结束
    def file_check(self, isOk: bool, restore_list: list, dicts: dict):
        if isOk:
            # 验证通过，直接拉起验证下载结束
            self.chkDownEnd(event=isOk, dicts=dicts)
        else:
            # 启动下载窗口
            logging.info("[主窗口] 开始重新下载")
            try:
                # versions 改为函数内部获取
                d = DownloadWindow(keyList=restore_list, dicts=dicts, parent=self)
                d.download_signal.connect(self.chkDownEnd)
                d.show()
                d.exec()
            except Exception as e:
                logging.error(f"[主窗口] 打开下载窗口失败: {e}")
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
        self.chkAction.setEnabled(True)
        self.send_notification("验证模组内容完整性", "验证已完成")
        self.statusBar.showMessage("验证完整性完成", 3 * 1000)

    # 检查更新按钮事件
    def buttonUpdate_onClick(self):
        self.checkSelfUpdate(showTip=True)

    # 检查更新
    def checkSelfUpdate(self, showTip=False):
        self.chkUp = checkUpdate(showTip=showTip)
        self.chkUp.newLog.connect(self.updateLog)
        self.chkUp.noUpdate.connect(self.noUpdate)
        self.chkUp.start()

    def noUpdate(self, show):
        if show:
            self.send_notification(app_name, "已是最新版本")
            # QMessageBox.information(self, "更新", '已是最新版本')

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
                self.startAction.setEnabled(True)
            # 更新检查
            self.checkSelfUpdate()

    # 游戏运行状态检查回调
    def gameCheck(self, run_stat: bool):
        logging.info(f"[主窗口] 游戏运行状态：{run_stat}")
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
        if channel == "release":
            buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        else:
            buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Ignore
        box = QMessageBox.question(
            self,
            "更新",
            "<p>发现新版本："f"{version}""</p><p>"f"{log}"'</p><p><a href="https://docs.qq.com/markdown/DZE1ycUZjdk1mV2RX">完整更新日志</a></p><p>要现在进行更新吗？</p>',
            buttons
        )
        if box == QMessageBox.StandardButton.Yes:
            self.do_update(version)
        elif box == QMessageBox.StandardButton.Ignore:
            config.write("gui.json", "update", "skip_version", version)

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
                    logging.error(f"[主窗口] {e}")
                    QMessageBox.question(self, "更新", "更新文件解压失败，请稍后重新检查更新尝试", QMessageBox.StandardButton.Yes)
                    return
            if os.path.exists(os.path.join(run_path, f"{k}")):
                os.remove(os.path.join(run_path, f"{k}"))
            subprocess.Popen(
                f'start "{app_name} | 更新" update.exe -n {k.replace("_update.data", "")}',
                shell=True,
                startupinfo=subprocess.STARTUPINFO(
                    dwFlags=subprocess.STARTF_USESHOWWINDOW,
                    wShowWindow=0
                )
            )
            self._isUpdate = True
            self.close()

    # 托盘退出
    def tray_close(self):
        self._isUpdate = True
        self.close()

    # 清除记住选项
    def clear_remember(self):
        config.write("gui.json", "exit", "remember")
        self.send_notification("选项", "记住的关闭选项已清除", 3000)

    # 重写关闭事件
    def closeEvent(self, event):
        if not self._isUpdate:
            _type = config.read("gui.json", "exit", "remember", 999)
            if _type == 999:
                _type, remember = MessageBox_Exit(self).exec()
                if remember:
                    config.write("gui.json", "exit", "remember", _type)
            if _type == MessageBox_ButtonType.No:
                event.ignore()
                return
            elif _type == MessageBox_ButtonType.Hidden:
                if not self.isHidden():
                    self.show_tray_menu()
                event.ignore()
                return
        self.statusBar.showMessage("正在结束程序")
        pos = self.pos()
        config.write("gui.json", "position", "x", pos.x())
        config.write("gui.json", "position", "y", pos.y())
        logging.info("[主窗口] 准备结束程序")
        self.button_start.setEnabled(False)
        self.tray = None
        self.cleanup_thread = CleanupThread(self)
        self.cleanup_thread.finished.connect(lambda: self.finalClose(event))
        self.cleanup_thread.start()
        event.ignore()

    def finalClose(self, event):
        logging.info("[主窗口] 主窗口关闭")
        logging.debug(f"[主窗口] 清理后台进程结果：{not self.cleanup_thread.isRunning()}")
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
    def gameStart_onClick(self):
        if not self.chkAction.isEnabled():
            self.send_notification(app_name, "验证完整性未完成，请等待验证完成后再启动游戏")
            return
        self.button_start.setEnabled(False)
        self.button_start.setText("准备启动游戏...")
        self.startAction.setEnabled(False)
        self.startAction.setText("准备启动...")
        if self.isHidden():
            self.show()
        QTimer(self).singleShot(500, lambda: self.gameStart())

    # 启动游戏流程
    def gameStart(self):
        if not os.path.exists(os.path.join(run_path, f"{game_exe_name}.exe")):
            if not self.button_start.isEnabled():
                self.button_start.setEnabled(True)
                self.button_start.setText("启动游戏")
                self.startAction.setEnabled(True)
                self.startAction.setText("启动游戏")
            QMessageBox.warning(self, "警告", "请确保启动器已在游戏目录中，且目录中包含游戏主程序", QMessageBox.StandardButton.Yes)
            return
        net = network_check()
        logging.info(f"[主窗口] 网络连接: {net}")
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
                logging.info("[主窗口] 开始启动下载窗口")
                try:
                    d = DownloadWindow(keyList=keyList, dicts=dicts, parent=self)
                    d.download_signal.connect(self.downloadEnd)
                    d.show()
                    d.exec()
                except Exception as e:
                    logging.error(f"[主窗口] 打开下载窗口失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # 没有更新
                self.downloadEnd(True, dicts=dicts)
                return
        else:
            if not self.button_start.isEnabled():
                self.button_start.setEnabled(True)
                self.button_start.setText("启动游戏")
                self.startAction.setEnabled(True)
                self.startAction.setText("启动游戏")
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
        QTimer(self).singleShot(3000, lambda: self.startGame())

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
        QMessageBox.information(self, "关于", '<p>版本: 'f'{ver}''</p><p><a href="https://docs.qq.com/markdown/DZE1ycUZjdk1mV2RX">更新日志</a></p>'
                                            '<p>服务器赞助</p><p><a href="https://www.mailx.top/images/wxpay/wxpay.jpeg">微信支付</a> | <a href="https://afdian.com/a/xingKongVersionRX">爱发电</a></p>')
