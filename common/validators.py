from django.core.exceptions import ValidationError


def ADDRESS_VALIDATOR(address: dict | None):
    if address is None:
        return

    if not any(
        [key in ["area", "city", "district", "pin_code", "state", "zipcode"]]
        for key in address
    ):
        raise ValidationError({"msg": "%s is not a valid address" % (address)})
