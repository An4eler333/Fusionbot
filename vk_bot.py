"""
Запускатель VK Bot Fusionbot v6.x
"""
import logging
from dotenv import load_dotenv
from error_handler import DataValidator, ValidationError

load_dotenv('ТОКЕНЫ.env')

from vk_bot_v6_clean import main  # noqa: E402

if __name__ == "__main__":
    try:
        # Базовая валидация токена перед запуском
        import os
        vk_token = os.getenv('VK_TOKEN', '')
        DataValidator.validate_vk_token(vk_token)
    except ValidationError as e:
        logging.getLogger(__name__).error(f"Некорректный VK_TOKEN: {e}")
        raise SystemExit(2)

    main()


