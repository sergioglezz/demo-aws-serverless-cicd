import decimal
import json


class DecimalEncoder(json.JSONEncoder):
    """Serializa los Decimal que devuelve DynamoDB para los números.

    Workaround de https://bugs.python.org/issue16535
    """

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            if obj == obj.to_integral_value():
                return int(obj)
            return float(obj)
        return super().default(obj)
