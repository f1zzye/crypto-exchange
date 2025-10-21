import secrets


class MathOperationGenerator:

    OPERATIONS: list[str] = ["+", "-", "*"]

    @classmethod
    def generate(cls) -> tuple[int, int, str, int]:
        operation = secrets.choice(cls.OPERATIONS)

        if operation == "+":
            num1 = secrets.randbelow(9) + 1
            num2 = secrets.randbelow(9) + 1
            result = num1 + num2
        elif operation == "-":
            num1 = secrets.randbelow(8) + 2
            num2 = secrets.randbelow(num1 - 1) + 1
            result = num1 - num2
        else:
            num1 = secrets.randbelow(4) + 2
            num2 = secrets.randbelow(3) + 2
            result = num1 * num2

        return num1, num2, operation, result
