#!/usr/bin/python3
from data.api_setting import TencentCloud
from qcloud_cos import CosConfig, CosS3Client


class COS:
    def __init__(self, bucket: str, region: str):
        super(COS, self).__init__()
        self.bucket = bucket
        self.region = region
        self.secret_id = TencentCloud.COS.secret_id
        self.secret_key = TencentCloud.COS.secret_key
        self.token = TencentCloud.COS.token
        self.scheme = TencentCloud.COS.scheme
        self.config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key, Token=self.token, Scheme=self.scheme)
        self.client = CosS3Client(self.config)

    def get_file_list(self) -> dict:
        """
        获取文件列表
        """
        # for fileInfo in response["Contents"]:
        #     k = "文件"
        #     if fileInfo["Key"][-1] == "/":
        #         k = "文件夹"
        #     print(fileInfo["Key"], " ", fileInfo["ETag"], " ", k)
        response: dict = self.client.list_objects(Bucket=self.bucket, Delimiter="", Marker="", MaxKeys=1000, Prefix="", EncodingType="")
        return response.get("Contents", {})

    def get_file_metadata(self, key) -> dict:
        """
        获取文件列表
        :param key: COS 文件路径
        """
        response = self.client.head_object(self.bucket, key)
        return response
