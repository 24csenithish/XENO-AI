# app/tools/calculator.py
import ast
import operator

def safe_eval(expr: str) -> float:
    # Only allow numbers, operators, parentheses, and basic arithmetic
    allowed = {"+", "-", "*", "/", "(", ")", " ", ".", "0","1","2","3","4","5","6","7","8","9"}
    if not all(c in allowed or c.isdigit() for c in expr):
        raise ValueError("Invalid characters in expression")
    # Use ast.literal_eval with operators? Actually safer to use a parser.
    # For simplicity, use eval with restricted globals.
    return eval(expr, {"__builtins__": {}}, {})

async def calculator(expression: str) -> dict:
    try:
        result = safe_eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}