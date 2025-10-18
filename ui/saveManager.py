import shutil

from PyQt6.QtWidgets import *

from lib.es3Editer import Es3Editer
from lib.core import *


class SaveManagerWindow(QDialog):
    def __init__(self, parent=None):
        super(SaveManagerWindow, self).__init__(parent=parent)
        self.setWindowTitle("存档管理器")
        # self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.resize(300, 200)
        # 初始化列表
        self.listWidget = QListWidget(self)
        self.listWidget.setGeometry(0, 0, 100, 200)
        self.listWidget.setStyleSheet("QListWidget::item { height: 40px; font-size: 11px; text-overflow: clip; }")
        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.listWidget.clicked.connect(self.listWidget_onClicked)

        self.saveInfoLabel = QLabel(self)
        self.saveInfoLabel.setGeometry(110, 5, 180, 144)
        self.saveInfoLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.saveInfoLabel.setWordWrap(True)

        self.save_backup = QPushButton(self)
        self.save_backup.setText("备份存档")
        self.save_backup.clicked.connect(self.buttonBackup)
        self.save_backup.setGeometry(105, 149, 80, 24)
        self.save_backup.setEnabled(False)

        self.save_delete = QPushButton(self)
        self.save_delete.setText("删除存档")
        self.save_delete.clicked.connect(self.buttonDelete)
        self.save_delete.setGeometry(215, 149, 80, 24)
        self.save_delete.setEnabled(False)

        self.save_restore = QPushButton(self)
        self.save_restore.setText("从备份文件还原存档")
        self.save_restore.clicked.connect(self.buttonRestore)
        self.save_restore.setGeometry(105, 173, 190, 24)

        self.loadList()

    def listWidget_onClicked(self):
        item = self.listWidget.currentItem()
        current_save = f'{item.statusTip()}'
        data = Es3Editer(os.path.join(game_save_path, rf"{current_save}\{current_save}.es3")).read_es3()
        run_stats = data.get("dictionaryOfDictionaries", {}).get("value", {}).get("runStats", {})
        level = run_stats.get("level", 0)
        money = run_stats.get("currency", 0)
        player_list = data.get("playerNames", {}).get("value", {})
        player_name_list = "玩家："
        for player_id in player_list.keys():
            player_name_list += f'{player_list.get(player_id, "Err: None")}''; '
        self.saveInfoLabel.setText(f"关卡：{level}\n赚取：{money}K\n{player_name_list}")

    def loadList(self):
        self.listWidget.clear()
        save_list = os.listdir(game_save_path)
        for save in save_list:
            data = Es3Editer(os.path.join(game_save_path, rf"{save}\{save}.es3")).read_es3()
            save_name = data.get("teamName", {}).get("value", "R.E.P.O.")
            save_time = data.get("dateAndTime", {}).get("value", "1970-01-01")
            item = QListWidgetItem()
            item.setText(f"{save_name}\n{save_time}")
            item.setStatusTip(f'{save}')
            self.listWidget.addItem(item)
        if save_list:
            self.listWidget.setCurrentRow(0)
            self.listWidget_onClicked()
            self.save_delete.setEnabled(True)
            self.save_backup.setEnabled(True)

    def buttonDelete(self):
        item = self.listWidget.currentItem()
        current_save = f'{item.statusTip()}'
        if QMessageBox.warning(self, "警告", "删除后不可恢复，确定要删除吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if QMessageBox.warning(self, "警告", "真的想好了吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                shutil.rmtree(os.path.join(game_save_path, current_save))
                self.loadList()
                QMessageBox.information(self, "删除", "存档已删除")

    def buttonBackup(self):
        item = self.listWidget.currentItem()
        current_save = f'{item.statusTip()}'
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        file_path, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="保存备份",
            directory=backup_path,
            filter="备份文件 (*.save.zip)"
        )
        logging.info(f"选择备份文件位置：{file_path}")
        if file_path:
            cache = os.path.join(run_path, "backup_cache")
            cache_filename = generateFilenameWithDatetime(prefix="backup_")
            if not os.path.exists(cache):
                os.makedirs(cache)
            writeJson(os.path.join(cache, "manifest.json"), {
                "save": current_save,
                "name": cache_filename
            })
            shutil.make_archive(os.path.join(cache, cache_filename), 'zip', os.path.join(game_save_path, current_save))
            shutil.make_archive(file_path.replace(".zip", ""), 'zip', cache)
            shutil.rmtree(cache)
            QMessageBox.information(self, "备份", "备份完成")

    def buttonRestore(self):
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="恢复备份",
            directory=backup_path,
            filter="备份文件 (*.save.zip)"
        )
        if file_path:
            cache = os.path.join(run_path, "restore_cache")
            if not os.path.exists(cache):
                os.makedirs(cache)
            shutil.unpack_archive(file_path, cache, 'zip')
            info = readJson(os.path.join(cache, "manifest.json"))
            logging.info(f"备份数据：{info}")
            save = info.get("save")
            filename = info.get("name")
            shutil.unpack_archive(os.path.join(cache, f"{filename}.zip"), os.path.join(game_save_path, save), 'zip')
            shutil.rmtree(cache)
            self.loadList()
            QMessageBox.information(self, "还原", "还原完成")
