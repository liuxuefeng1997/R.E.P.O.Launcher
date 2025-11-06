from lib.core import *
from lib.cos import *
import crcmod


class CrcCheck(QThread):
    progress_all = pyqtSignal(dict)
    progress_one = pyqtSignal(dict)
    complete_list = pyqtSignal(list, dict)

    def __init__(self, parent=None):
        super(CrcCheck, self).__init__(parent=parent)
        self.file_list = COS(TencentCloud.Update.mod_bukkit, TencentCloud.Update.mod_region).get_file_list()
        self.dicts = {}
        # 去除文件夹，因为不需要下载
        for file_info in self.file_list:
            if file_info["Key"][-1] != "/":
                self.dicts[file_info["Key"]] = file_info["ETag"]
        logging.info("[校验文件] 校验列表初始化完成，开始校验")

    def run(self):
        file_sum = 0
        file_maxsum = len(self.dicts)
        restore_list = []
        for key in self.dicts.keys():
            file_sum += 1
            chk_complete = int(file_sum / file_maxsum * 100)
            cos_crc64 = COS(TencentCloud.Update.mod_bukkit, TencentCloud.Update.mod_region).get_file_metadata(key).get("x-cos-hash-crc64ecma", False)
            if cos_crc64:
                file_crc64 = ""
                try:
                    file_crc64 = self.calculate_file_crc64(os.path.join(run_path, key))
                except Exception as e:
                    logging.error(e)
                if f"{file_crc64}" != f"{cos_crc64}":
                    restore_list.append(key)
                self.sendProgressAll({
                    "file_sum": file_sum,
                    "file_max": file_maxsum,
                    "complete": chk_complete
                })
        self.sendCompleteList(restore_list, self.dicts)

    def sendProgressAll(self, data: dict):
        self.progress_all.emit(data)

    def sendProgressOne(self, data: dict):
        self.progress_one.emit(data)

    def sendCompleteList(self, data: list, dicts: dict):
        self.complete_list.emit(data, dicts)

    def calculate_file_crc64(self, file_path: str, chunk_size=5*1000*1000):
        """
        使用 crcmod 库计算文件的 CRC64-ECMA 校验码

        Args:
            file_path: 文件路径
            chunk_size: 读取块大小（字节）

        Returns:
            int: CRC64值
        """
        file_path = os.path.expandvars(file_path)

        # 创建 CRC64-ECMA 函数
        crc64_func = crcmod.mkCrcFun(0x142F0E1EBA9EA3693, initCrc=0, xorOut=0xFFFFFFFFFFFFFFFF)

        crc_value = 0

        # 初始化文件信息
        dirname = os.path.basename(os.path.dirname(file_path))
        hasdir = f"{dirname}/" if dirname else ""
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            self.sendProgressOne({
                "dir": hasdir,
                "file": filename,
                "complete": 0,
                "find": False
            })
            logging.info(f'[校验文件] {hasdir}{filename} 文件不存在')
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not os.path.isfile(file_path):
            logging.info(f"[校验文件] 路径不是文件: {file_path}")
            raise ValueError(f"路径不是文件: {file_path}")

        size = 0
        content_size = os.stat(file_path).st_size

        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    size += len(chunk)
                    complete = int(size / content_size * 100)
                    crc_value = crc64_func(chunk, crc_value)
                    self.sendProgressOne({
                        "dir": hasdir,
                        "file": filename,
                        "complete": complete,
                        "find": True
                    })
                    logging.info(f'[校验文件] {hasdir}{filename} 已完成 {complete}%')
                f.close()
        except IOError as e:
            self.sendProgressOne({
                "dir": hasdir,
                "file": filename,
                "complete": 0,
                "find": False
            })
            logging.error(f"[校验文件] 读取文件失败: {e}")
            raise IOError(f"读取文件失败: {e}")

        return crc_value
