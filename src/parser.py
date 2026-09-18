from .errors import SyntaxError
from .model import Condition, Query, Token


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens, self.index = tokens, 0

    def current(self) -> Token | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def accept(self, *kinds: str) -> Token | None:
        token = self.current()
        if token and token.kind in kinds:
            self.index += 1
            return token
        return None

    def require(self, *kinds: str) -> Token:
        token = self.accept(*kinds)
        if token:
            return token
        actual = self.current().value if self.current() else "end of query"
        raise SyntaxError(f"Expected {' or '.join(kinds)}, found {actual!r}.")

    def parse(self) -> Query:
        count = bool(self.accept("COUNT"))
        projection = None
        limit = None
        order_by = None
        descending = False
        if count:
            self.require("ENTITY")
        else:
            self.require("ACTION")
            # "Show top 5 students by CGPA" is a compact selection form.
            if self.accept("TOP"):
                limit = int(float(self.require("NUMBER").value))
                self.require("ENTITY")
                self.require("BY")
                order_by = self.require("ATTRIBUTE").value
                descending = True
            elif self.accept("ALL"):
                self.require("ENTITY")
            elif self.current() and self.current().kind == "ENTITY":
                self.require("ENTITY")
                # Controlled wording: "Show student names".
                if self.current() and self.current().kind == "ATTRIBUTE":
                    projection = [self.require("ATTRIBUTE").value.rstrip("s")]
            else:
                projection = [self.require("ATTRIBUTE").value]
                self.require("ENTITY")
        source = "students"  # both 'student' and 'students' map to the schema table
        conditions: list[Condition] = []
        if self.accept("CONDITION"):
            conditions.append(self.parse_condition())
            while connector := self.accept("LOGICAL"):
                conditions.append(self.parse_condition(connector.value.upper()))
        elif self.accept("FROM"):
            value = self.require("WORD", "STRING").value
            # Optional natural-language noun in "from CSE department".
            if self.current() and self.current().kind == "ATTRIBUTE" and self.current().value == "department":
                self.index += 1
            conditions.append(Condition("department", "=", value))
        if self.accept("ORDERED"):
            self.require("BY")
            order_by = self.require("ATTRIBUTE").value
            descending = bool(self.accept("DESC"))
            self.accept("ASC")
        if self.accept("LIMIT"):
            limit = int(float(self.require("NUMBER").value))
        if self.current():
            raise SyntaxError(f"Unexpected token {self.current().value!r}.")
        return Query(projection, source, conditions, order_by, descending, limit, count)

    def parse_condition(self, connector: str | None = None) -> Condition:
        attribute = self.require("ATTRIBUTE", "WORD").value
        filler = self.accept("FILLER")
        if operator := self.accept("OPERATOR"):
            op = operator.value
        elif self.accept("COMPARISON_WORD"):
            word = self.tokens[self.index - 1].value
            self.require("THAN")
            op = ">" if word == "greater" else "<"
        elif self.accept("AT"):
            op = ">=" if self.accept("LEAST") else "<=" if self.accept("MOST") else None
            if op is None:
                raise SyntaxError("Expected 'least' or 'most' after 'at'.")
        elif filler:
            # In the controlled language, "CGPA is 8" means equality.
            op = "="
        else:
            raise SyntaxError("Expected a comparison operator after attribute.")
        value = self.require("NUMBER", "STRING", "WORD").value
        return Condition(attribute, op, value, connector)


def parse(tokens: list[Token]) -> Query:
    return Parser(tokens).parse()
