from yookassa import Configuration, Payment

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
