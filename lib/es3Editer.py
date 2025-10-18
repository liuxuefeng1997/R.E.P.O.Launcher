from es3_modifier import ES3
from lib.core import *


class Es3Editer:
    def __init__(self, file_path: str):
        """
        ES3 存档编辑器
        :param file_path: 存档文件路径
        """
        super(Es3Editer, self).__init__()
        self.file_path = file_path
        self.decrypting_password = "Why would you want to cheat?... :o It's no fun. :') :'D"

    def read_es3_obj(self) -> ES3 | None:
        """
        读取 ES3 存档
        :return: 返回存档json object
        """
        try:
            with open(self.file_path, 'rb') as f:
                es3 = ES3(f.read(), self.decrypting_password)
                f.close()
        except Exception as e:
            logging.error(e)
            return None
        return es3

    def read_es3(self) -> dict:
        """
        读取 ES3 存档
        :return: 返回存档json object
        """
        try:
            with open(self.file_path, 'rb') as f:
                es3 = ES3(f.read(), self.decrypting_password)
                f.close()
        except Exception as e:
            logging.error(e)
            return {}
        return es3.load()

    def write_es3(self, save_data: dict) -> bool:
        """
        写入 ES3 存档
        :param save_data: 修改后的存档 json object
        :return: 返回是否成功
        """
        try:
            with open(self.file_path, 'wb') as f:
                json_str = json.dumps(save_data, ensure_ascii=False, indent=4)
                f.write(self.read_es3_obj().save(json_str))
        except Exception as e:
            logging.error(e)
            return False
        return True
