from typing import Sized
from eth_utils import to_checksum_address
from config.configvalidator import ConfigValidator
from utils.balance_checker import check_balance
from client.client import Client
from modules.bridge import Bridge
from utils.logger import logger
import asyncio
import random
import json


def load_profiles(private_keys_path: str, proxies_path: str) -> list[dict]:
    with open(private_keys_path, "r", encoding="utf-8") as pk_file:
        private_keys = [line.strip() for line in pk_file if line.strip()]

    with open(proxies_path, "r", encoding="utf-8") as proxy_file:
        proxies = [line.strip() for line in proxy_file if line.strip()]

    if len(private_keys) != len(proxies):
        raise ValueError("Количество приватных ключей и прокси не совпадает!")

    return [{"private_key": pk, "proxy": proxy} for pk, proxy in zip(private_keys, proxies)]


async def get_random_float(min_value: float, max_value: float, precision: int = 3) -> float:

    return round(random.uniform(min_value, max_value), precision)


async def run_profile(profiles: Sized, i: int, profile: dict, settings: dict, from_network: dict, to_network: dict):
    try:
        from_address = None
        receiver_address = None
        if settings["token"] == "ETH":
            from_address = from_network["native_address"]
            receiver_address = to_checksum_address(from_network["receiver"])

        client = Client(
            proxy=profile["proxy"],
            rpc_url=from_network["rpc_url"],
            chain_id=from_network["chain_id"],
            chain_id_to=to_network["chain_id"],
            private_key=profile["private_key"],
            from_address=from_address,
            amount=settings["amount"],
            token=settings["token"],
            explorer_url=from_network["explorer_url"]
        )
        logger.info(f"➡️ Запуск профиля {i}/{len(profiles)}: {client.address}...\n")
        bridge_method = settings.get("bridge_method")
        amount = settings.get("amount")
        percent_min, percent_max = settings.get("transfer_amount_range")
        percentage = await get_random_float(percent_min, percent_max)
        min_amount = await client.to_wei_main(settings["min_balance_to_bridge"])

        native_balance = await check_balance(client, settings)
        if native_balance < min_amount:
            logger.info(
                f"⚠️ Профиль #{i} пропущен — баланс ниже минимума ({native_balance} < {min_amount} wei)\n"
            )
            return
        if bridge_method == "P":
            real_amount = int(native_balance * percentage)
        elif bridge_method == "PFL":
            real_amount = int((native_balance - min_amount) * percentage)
        else:
            real_amount = int(await client.to_wei_main(amount))

        await client.set_amount(real_amount)

        logger.info("⚙️ Собираем и подписываем транзакцию...\n")
        bridge = Bridge(client, from_network, to_network, settings, receiver_address)
        await bridge.execute_bridge()

    except Exception as e:
        logger.error(f"❌ Ошибка в профиле #{i}: {e}\n")


async def main():
    try:
        logger.info("🚀 Запуск скрипта...\n")
        validator = ConfigValidator("config/settings.json")
        settings = await validator.validate_config()

        with open("constants/networks_data.json", "r", encoding="utf-8") as file:
            networks_data = json.load(file)

        from_network = networks_data[settings["from_network"]]
        to_network = networks_data[settings["to_network"]]

        # 📌 Загрузка профилей
        profiles = load_profiles("config/private_keys.txt", "config/proxies.txt")
        logger.info(f"🔐 Загружено {len(profiles)} профилей.\n")

        for i, profile in enumerate(profiles, 1):
            await run_profile(profiles, i, profile, settings, from_network, to_network)

            if i < len(profiles):
                delay_min, delay_max = settings.get("delay_between_profiles_range", [5, 10])
                delay = random.randint(delay_min, delay_max)
                logger.info(f"⏳ Ожидание {delay:.2f} сек перед следующим профилем...\n")
                await asyncio.sleep(delay)

    except Exception as e:
        logger.error(f"❗️Произошла ошибка в основном пути: {e}")


if __name__ == "__main__":
    asyncio.run(main())
