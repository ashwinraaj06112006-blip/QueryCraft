import argparse
from dataclasses import asdict

from .errors import QueryCraftError
from .lexer import tokenize
from .parser import parse
from .semantic import validate
from .sql_generator import generate


def compile_query(source: str):
    tokens = tokenize(source)
    ast = parse(tokens)
    validate(ast)
    return tokens, ast, generate(ast)


def main() -> int:
    cli = argparse.ArgumentParser(description="QueryCraft Phase 1 compiler prototype")
    cli.add_argument("query", help="controlled natural-language query")
    args = cli.parse_args()
    try:
        tokens, ast, sql = compile_query(args.query)
        print("TOKENS:")
        print("  " + ", ".join(f"{token.kind}({token.value})" for token in tokens))
        print("AST / IR:")
        print("  " + repr(asdict(ast)))
        print("SEMANTIC ANALYSIS: valid against students schema")
        print("GENERATED SQL:")
        print("  " + sql)
        return 0
    except QueryCraftError as error:
        print(f"{type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
