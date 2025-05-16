from decimal import Decimal, InvalidOperation
import logging
import json

MIN_AMOUNT = Decimal(0.0001)
logger = logging.getLogger(__name__)


class ConfigValidator:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_data = self.load_config()

    def load_config(self) -> dict:
        """Загружает конфигурационный файл"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"❗️ Файл конфигурации {self.config_path} не найден.")
            exit(1)
        except json.JSONDecodeError:
            logging.error(f"❗️ Ошибка разбора JSON в файле конфигурации {self.config_path}.")
            exit(1)

    async def validate_config(self) -> dict:
        """Валидация всех полей конфигурации"""

        await self.validate_required_keys()

        if "from_network" not in self.config_data:
            logging.error("❗️ Ошибка: Отсутствует 'from_network' в конфигурации.")
            exit(1)

        if "amount" not in self.config_data:
            logging.error("❗️ Ошибка: Отсутствует 'amount' в конфигурации.")
            exit(1)

        if "to_network" not in self.config_data:
            logging.error("❗️ Ошибка: Отсутствует 'to_network' в конфигурации.")
            exit(1)

        if "token" not in self.config_data:
            logging.error("❗️ Ошибка: Отсутствует 'token' в конфигурации.")
            exit(1)

        if self.config_data["from_network"] == self.config_data["to_network"]:
            logging.error(
                "❗️ Ошибка: Поля 'from_network' и 'to_network' имеют одинаковое значение, введите разные сети.")
            exit(1)

        await self.validate_from_network(self.config_data["from_network"])
        await self.validate_to_network(self.config_data["to_network"])
        await self.validate_amount(self.config_data["amount"])
        await self.validate_token(self.config_data["token"])

        return self.config_data

    async def validate_required_keys(self):
        required_keys = [
            "from_network",
            "amount",
            "to_network",
            "token"
        ]

        for key in required_keys:
            if key not in self.config_data:
                logging.error(f"❗️ Ошибка: отсутствует обязательный ключ '{key}' в settings.json")
                exit(1)

    @staticmethod
    async def validate_token(token: str) -> None:
        """Валидация названия токена"""
        tokens = [
            "USDC",
            "ETH"
        ]
        if token not in tokens:
            logging.error("❗️ Ошибка: Неподдерживаемый токен! Введите один из поддерживаемых токенов.")
            exit(1)

    @staticmethod
    async def validate_from_network(network: str) -> None:
        """Валидация названия сети"""
        networks = [
            "Abstract",
            "Arbitrum"
        ]
        if network not in networks:
            logging.error("❗️ Ошибка: Неподдерживаемая сеть отправления! Введите одну из поддерживаемых сетей.")
            exit(1)

    @staticmethod
    async def validate_to_network(network: str) -> None:
        """Валидация названия сети"""
        networks = [
            "Abstract",
            "Arbitrum"
        ]
        if network not in networks:
            logging.error("❗️ Ошибка: Неподдерживаемая сеть получения! Введите одну из поддерживаемых сетей.")
            exit(1)

    @staticmethod
    async def validate_amount(amount_raw: float) -> None:
        """Валидация количества токенов"""
        if not isinstance(amount_raw, (str, int, float)):
            raise ValueError(f"❗️ Количество должно быть строкой или числом, но имеет тип {type(amount_raw)}.")

        try:
            amount = Decimal(str(amount_raw))
        except InvalidOperation:
            logging.error("❗️ Ошибка количества токенов! Введено невалидное значение.")
            exit(1)

        if amount <= 0:
            logging.error("❗️ Количество токенов должно быть больше нуля.")
            exit(1)

        if amount < MIN_AMOUNT:
            logging.error(f"❗️ Количество токенов для отправки слишком мало, введите значение больше {MIN_AMOUNT}.")
            exit(1)
