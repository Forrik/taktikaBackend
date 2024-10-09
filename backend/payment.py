from yookassa import Configuration, Payment, Webhook

Configuration.account_id = '464176'
Configuration.secret_key = 'test_OjtZbDjgDDZnA3Cf_zKHY_pFI4VvKVhizI9FBYZuBdw'


def create_split_payment(amount, recipient_account_id, recipient_amount):
    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://localhost:5173"
        },
        "capture": True,
        "description": "Payment for subscription",
        "receipt": {
            "customer": {
                "email": "customer@example.com"
            },
            "items": [
                {
                    "description": "Subscription",
                    "quantity": "1.00",
                    "amount": {
                        "value": str(amount),
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        },
        "splits": [
            {
                "account_id": recipient_account_id,
                "amount": {
                    "value": str(recipient_amount),
                    "currency": "RUB"
                }
            },
            {
                "account_id": Configuration.account_id,
                "amount": {
                    "value": str(amount - recipient_amount),
                    "currency": "RUB"
                }
            }
        ]
    })
    return payment


def create_webhook():
    response = Webhook.add({
        "event": "payment.succeeded",
        "url": "https://localhost:8000/webhook/payment/",
    })
    return response


# Пример использования
if __name__ == "__main__":
    # Создаем платеж
    payment = create_split_payment(1000, 'recipient_account_id', 500)
    print("Payment created:", payment)

    # Создаем вебхук
    webhook = create_webhook()
    print("Webhook created:", webhook)
