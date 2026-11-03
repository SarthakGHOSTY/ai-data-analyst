import pytest

from utils.validator import validate_sql

ALLOWED = [
    "SELECT * FROM data LIMIT 5",
    "select Country, SUM(Quantity*UnitPrice) AS revenue from data group by Country order by revenue desc;",
    "WITH t AS (SELECT * FROM data) SELECT COUNT(*) FROM t",
    "SELECT * FROM data WHERE Description = 'please update me'",
    'SELECT "Order Date" FROM data -- comment',
    "SELECT strftime(InvoiceDate, '%Y-%m') AS month, SUM(Quantity) FROM data GROUP BY 1",
    "SELECT COUNT(DISTINCT CustomerID) FROM data",
    'SELECT * FROM "data" LIMIT 3',
]

BLOCKED = [
    "DELETE FROM data WHERE Quantity < 0",
    "DROP TABLE data",
    "SELECT 1; DROP TABLE data",
    "UPDATE data SET Quantity = 0",
    "INSERT INTO data VALUES (1)",
    "COPY data TO 'out.csv'",
    "PRAGMA database_list",
    "",
    "/* hi */ DELETE FROM data",
    "SELECT * FROM data; -- sneaky\nDELETE FROM data",
    "SELECT * FROM read_csv('secret.csv')",
    "SELECT * FROM read_csv_auto('x.csv')",
    "SELECT * FROM parquet_scan('a.parquet')",
    "SELECT * FROM 'data/Online_Retail.csv'",
    'SELECT * FROM "secret.csv"',
    "SELECT * FROM data JOIN 'other.csv' USING (a)",
    "select * from\n'x.csv'",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_allowed(sql):
    assert validate_sql(sql)[0] is True


@pytest.mark.parametrize("sql", BLOCKED)
def test_blocked(sql):
    assert validate_sql(sql)[0] is False