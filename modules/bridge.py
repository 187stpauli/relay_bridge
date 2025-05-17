import aiohttp
from eth_utils import to_checksum_address

from client.client import Client
from utils.logger import logger


class Bridge:
    def __init__(self, client: Client, from_network: dict, to_network: dict, settings: dict, receiver_address: str):
        self.client = client
        self.receiver_address = receiver_address
        self.from_network = from_network
        self.to_network = to_network
        self.settings = settings
        self.pool_contract = None

    async def get_quote(self):
        try:
            url = "https://api.relay.link/quote"

            payload = {
                "useReceiver": True,
                "user": self.client.address,
                "originChainId": self.client.chain_id,
                "destinationChainId": self.client.chain_id_to,
                "originCurrency": "0x0000000000000000000000000000000000000000",
                "destinationCurrency": "0x0000000000000000000000000000000000000000",
                "amount": str(self.client.amount),
                "tradeType": "EXACT_INPUT"
            }

            headers = {"Content-Type": "application/json"}

            proxy = f"http://{self.client.proxy}"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, proxy=proxy) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise logger.error(f"❌ Ошибка запроса: статус {response.status}, ответ: {text}\n")
                    try:
                        result = await response.json()
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        raise logger.error(f"❌ Некорректный JSON в ответе: {text}\n")

                    return result
        except Exception as e:
            logger.error(f"❌ Ошибка при получении квоты: {e}")

    async def get_status(self, data):
        try:
            url = "https://api.relay.link/intents/status/v2"
            querystring = {"requestId": data}
            proxy = f"http://{self.client.proxy}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=querystring, proxy=proxy) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"❌ Ошибка запроса: статус {response.status}, ответ: {text}\n")
                        return {}

                    try:
                        result = await response.json()
                        logger.info(f"✅ Операция успешно завершена,"
                                    f" проверьте поступления средств в сети назначения...")
                        return result

                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        logger.error(f"❌ Некорректный JSON в ответе: {text}\n")
                        return {}
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении status-запроса: {e}")
            return {}

    async def execute_bridge(self):

        try:
            quote = await self.get_quote()
            step = quote["steps"][0]
            item = step["items"][0]
            tx_data = item["data"]

            tx = await self.client.prepare_tx(
                to_address=to_checksum_address(tx_data["to"]),
                value=int(tx_data["value"]),
                data=tx_data["data"],
                max_fee_per_gas=int(tx_data["maxFeePerGas"]),
                max_priority_fee_per_gas=int(tx_data["maxPriorityFeePerGas"])
            )

            tx_hash = await self.client.sign_and_send_tx(transaction=tx, external_gas=int(tx_data["gas"]))
            await self.client.wait_tx(tx_hash)
            await self.get_status(tx_data["data"])

            return
        except Exception as e:
            logger.error(f"{e}")
