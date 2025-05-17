import aiohttp
from eth_abi import abi
from client.client import Client
from utils.logger import logger
from utils.balance_checker import check_balance


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

    async def get_status(self):

    async def execute_bridge(self):

        try:
            quote = await self.get_quote()
            step = quote["steps"][0]
            item = step["items"][0]
            tx_data = item["data"]
            to_address = tx_data["to"]

            tx = await self.client.prepare_tx(
                to_address=tx_data["to"],
                value=int(tx_data["value"]),
                data=tx_data["data"],
                max_fee_per_gas=int(tx_data["maxFeePerGas"]),
                max_priority_fee_per_gas=int(tx_data["maxPriorityFeePerGas"])
            )

            tx_hash = await self.client.sign_and_send_tx(transaction=tx, external_gas=int(tx_data["gas"]))
            status = await self.client.wait_tx(tx_hash)


            send_params = [
                self.to_network['endpoint_id'],
                abi.encode(["address"], [self.client.address]),
                self.client.amount,
                quote_oft[2][1],
                b'',
                b'',
                b''
            ]

            tx = await self.pool_contract.functions.send(
                send_params,
                bridge_fee,
                self.client.address
            ).build_transaction(await self.client.prepare_tx(value))

            amount_approve = 2 ** 256 - 1

            if self.settings["token"] == "USDC":
                allowance = await self.client.get_allowance(self.from_network["usdc_address"], self.client.address,
                                                            self.from_network["usdc_pool_address"])
                if allowance < amount_approve:
                    await self.client.approve_usdc(self.from_network["usdc_address"],
                                                   self.from_network["usdc_pool_address"],
                                                   amount_approve, True)

            tx_hash = await self.client.sign_and_send_tx(tx)
            result = await self.client.wait_tx(tx_hash, self.client.explorer_url)
            if result:
                logger.info(f"💵 Бридж совершен, ожидайте поступления средств в сети назначения...")

            return
        except Exception as e:
            logger.error(f"{e}")
