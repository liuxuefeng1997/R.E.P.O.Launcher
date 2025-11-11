class TencentCloud:
    class COS:
        secret_id = "从腾讯云获取"
        secret_key = "从腾讯云获取"
        region = "ap-beijing"
        token = None
        scheme = "https"

    class Update:
        # 本体更新
        update_region = "ap-shanghai"
        update_bukkit = "update-1251534239"
        update_cosDir = "repo_mod_updater"
        update_manifest = "gui_version.json"
        update_channel_list = "gui_channel.json"

        self_update_manifest_url = "https://"f"{update_bukkit}.cos.{update_region}.myqcloud.com/{update_cosDir}/{update_manifest}"
        self_update_url = "https://"f"{update_bukkit}.cos.{update_region}.myqcloud.com/{update_cosDir}/"
        self_update_channel_list_url = "https://"f"{update_bukkit}.cos.{update_region}.myqcloud.com/{update_cosDir}/{update_channel_list}"

        # Mod更新
        mod_region = "ap-beijing"
        mod_bukkit = "repo-1251534239"
        enable_global = False  # 是否启用全球加速域名
        mod_update_url = "https://"f"{mod_bukkit}.cos.{'accelerate' if enable_global else mod_region}.myqcloud.com/"

