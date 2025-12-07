import json
import logging
import os.path


class Config:
    def __init__(self, _config_path: str):
        """
        配置类
        :param _config_path: 配置目录
        """
        super(Config, self).__init__()
        self.config_path = _config_path
        logging.info(f"[配置管理模块] 已初始化: {_config_path}")

    @staticmethod
    def _readJson(path: str) -> dict:
        try:
            with open(path, "r", encoding="utf8") as f:
                r = json.loads(f.read())
                f.close()
        except FileNotFoundError:
            r = {}
        return r

    @staticmethod
    def _writeJson(path: str, json_object: dict) -> bool:
        try:
            with open(path, "w", encoding="utf8") as f:
                f.write(json.dumps(json_object, ensure_ascii=False, indent=4))
                f.close()
            r = True
        except Exception as e:
            logging.error(f"[配置管理模块] {e}")
            r = False
        return r

    def read(self, config_file: str, config_session: str, config_item: str, default_value=None):
        """
        读取配置
        :param config_file: 配置文件名称
        :param config_session: 配置节点
        :param config_item: 配置项
        :param default_value: 默认值
        :return:
        """
        conf = self._readJson(os.path.join(self.config_path, config_file))
        value = conf.get(config_session, {}).get(config_item, default_value)
        logging.info(f"[配置管理模块] 读取配置: {config_file} - {config_session}, {config_item} = {value}")
        return value

    def write(self, config_file: str, config_session: str, config_item: str, config_value=None):
        """
        写入配置
        :param config_file: 配置文件名称
        :param config_session: 配置节点
        :param config_item: 配置项
        :param config_value: 配置值，留空删除配置项，如果配置节点无其他项目，则配置节点也会被删除
        :return:
        """
        conf = self._readJson(os.path.join(self.config_path, config_file))
        if not conf.get(config_session):
            conf.update({config_session: {}})
            logging.info(f"[配置管理模块] 写入配置: {config_file} - {config_session} 不存在，已添加")
        conf.get(config_session, {}).update({config_item: config_value})
        logging.info(f"[配置管理模块] 写入配置: {config_file} - {config_session}, {config_item} = {'null' if config_value is None else config_value}")
        if config_value is None and not type(config_value) == bool:
            conf.get(config_session, {}).pop(config_item)
            logging.info(f"[配置管理模块] 写入配置: {config_file} - {config_session}, {config_item} = null 已移除此项目")
        if not conf.get(config_session, {}):
            conf.pop(config_session)
            logging.info(f"[配置管理模块] 写入配置: {config_file} - {config_session} 项下无任何内容，已移除")
        self._writeJson(os.path.join(self.config_path, config_file), conf)
