Все файлы конфигурации находятся в папке config

Заполнение файла Settings:

from_network: "введите сеть отправки",
to_network: "введите сеть получения",
token: "введите токен для отправки ETH/USDC"
delay_between_profiles_range: [введите диапазон временных задержек в секундах]
transfer_amount_range: [введите диапазон % от баланса для бриджа где 50% это 0.5]
amount: "введите нужное кол-во токенов не менее 0.0001" (по умолчанию 0.0005)
min_balance_to_bridge: введите минимальный порог токенов от которого будет производиться бридж

Заполнение файлов proxies и private_keys:
Вставьте данные в соответствующие файлы скрипт не будет ничего перемешивать и запустит по соответствию строк.
Прокси вставлять в формате login:pass@host:port только http