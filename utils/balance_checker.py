from typing import Optional

from client.client import Client
from utils.logger import logger


async def check_balance(client: Client, settings: dict, from_network: Optional[dict] = None,
                        fee: Optional[int] = None) -> float:
    # Проверка баланса
    native_balance = await client.get_native_balance()
    gas = await client.get_tx_fee()

    if settings["token"] == "USDC":
        balance = await client.get_erc20_balance(from_network["usdc_address"])
        if client.amount > balance:
            logger.error(f"Недостаточно баланса {settings['token']}! Требуется: "
                         f"{await client.from_wei_main(client.amount):.8f} "
                         f"фактический баланс: "
                         f"{await client.from_wei_main(balance, from_network['usdc_address']):.8f}\n")
            exit(1)
        if gas + fee > native_balance:
            logger.error(f"Недостаточно баланса для оплаты газа! Требуется: "
                         f"{await client.from_wei_main(gas):.8f} "
                         f"фактический баланс: {await client.from_wei_main(native_balance):.8f}\n")
            exit(1)
    elif settings["token"] == "ETH":
        total_cost = client.amount + gas
        if total_cost > native_balance:
            logger.error(f"Недостаточно баланса! Требуется: {await client.from_wei_main(total_cost):.8f}"
                         f" фактический баланс: {await client.from_wei_main(native_balance):.8f}\n")
            exit(1)

    return native_balance
