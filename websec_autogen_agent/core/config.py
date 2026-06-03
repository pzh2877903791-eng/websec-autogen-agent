import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def get_bool_env(name: str, default:bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in ["true", "t", "yes", "1", "y", "on"]

def get_int_env(name: str, default:int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default

# 隐藏 API Key
def mask_secret(secret:str) -> str:
    if not secret:
        return ""

    if len(secret) <= 8:
        return "*" * len(secret)

    return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]

@dataclass
class Settings:
    enable_llm: bool = get_bool_env("ENABLE_LLM", False)
    enable_autogen: bool = get_bool_env("AUDIT_ENABLE_AUTOGEN", False)

    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    feishu_app_id: str = os.getenv("FEISHU_APP_ID", "")
    feishu_app_secret: str = os.getenv("FEISHU_APP_SECRET", "")
    feishu_webhook_url: str = os.getenv("FEISHU_WEBHOOK_URL", "")

    llm_timeout: int = get_int_env("LLM_TIMEOUT", 30)
    llm_retries: int = get_int_env("LLM_RETRIES", 2)

    @property
    def has_deepseek(self) -> bool:
        return bool(self.deepseek_api_key.strip())

    @property
    def has_feishu_app_credentials(self) -> bool:
        return bool(self.feishu_app_id.strip() and self.feishu_app_secret.strip())

    @property
    def has_feishu_webhook(self) -> bool:
        return bool(self.feishu_webhook_url.strip())


settings = Settings()


if __name__ == "__main__":
    print("当前配置：")
    print(f"ENABLE_LLM: {settings.enable_llm}")
    print(f"AUDIT_ENABLE_AUTOGEN: {settings.enable_autogen}")
    print(f"DEEPSEEK_MODEL: {settings.deepseek_model}")
    print(f"DEEPSEEK_BASE_URL: {settings.deepseek_base_url}")
    print(f"DEEPSEEK_API_KEY: {mask_secret(settings.deepseek_api_key)}")
    print(f"HAS_DEEPSEEK: {settings.has_deepseek}")
    print(f"LLM_TIMEOUT: {settings.llm_timeout}")
    print(f"LLM_RETRIES: {settings.llm_retries}")
    print(f"HAS_FEISHU_APP_CREDENTIALS: {settings.has_feishu_app_credentials}")
    print(f"HAS_FEISHU_WEBHOOK: {settings.has_feishu_webhook}")