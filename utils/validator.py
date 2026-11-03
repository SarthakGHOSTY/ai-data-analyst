import re

FORBIDDEN = {
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "attach", "detach", "copy", "export", "import", "install", "load",
    "pragma", "call", "set", "execute", "begin", "commit", "rollback",
}


def validate_sql(sql: str) -> tuple[bool, str]:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"--[^\n]*", " ", sql).strip().rstrip(";").strip()
    if not sql:
        return False, "Empty query."
    if ";" in sql:
        return False, "Only one statement is allowed."
    # A quoted name after FROM/JOIN can be a file path in DuckDB, e.g. FROM 'x.csv'.
    if re.search(r"""\b(from|join)\s*(['"])(?!data\2)""", sql, flags=re.I):
        return False, "Reading files is not allowed."
    
    # Ignore text inside quotes, so 'update' in a string is not a false alarm.
    check = re.sub(r"'(?:[^']|'')*'", "''", sql)
    check = re.sub(r'"[^"]*"', '""', check).lower()

    if not re.match(r"(select|with)\b", check):
        return False, "Only SELECT queries are allowed."
    for word in re.findall(r"[a-z_]+", check):
        if word in FORBIDDEN:
            return False, f"Forbidden keyword: {word}."
    if re.search(r"\bread_\w+|\bglob\b|\w+_scan\b", check):
        return False, "Reading files is not allowed."
    return True, sql