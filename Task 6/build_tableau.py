"""
Task 6 - Tableau data source.

Reads  Cleaned_Weather.csv
Writes Weather.hyper   (Tableau extract, table Extract.Extract, real types, NULLs kept as NULL)

Adds three sort helper columns Tableau needs (SeasonSort, DirSort, plus a first-of-month date) so charts do not
sort alphabetically. The workbook itself is written by build_twb.py.
"""

import os

import pandas as pd
from tableauhyperapi import (Connection, CreateMode, HyperProcess, Inserter, SqlType, TableDefinition,
                             TableName, Telemetry)

IN_CSV = "Cleaned_Weather.csv"
OUT_HYPER = "Weather.hyper"

DIRS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
SEASON_SORT = {"Summer": 1, "Autumn": 2, "Winter": 3, "Spring": 4}


def load():
    df = pd.read_csv(IN_CSV, parse_dates=["Date"])
    df["MonthStart"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["SeasonSort"] = df["Season"].map(SEASON_SORT)
    df["DirSort"] = df["WindGustDir"].map({d: i + 1 for i, d in enumerate(DIRS)})
    return df


def sql_type(col, series):
    if col in ("Date", "MonthStart"):
        return SqlType.date()
    if pd.api.types.is_bool_dtype(series):
        return SqlType.bool()
    if pd.api.types.is_integer_dtype(series):
        return SqlType.big_int()
    if pd.api.types.is_float_dtype(series):
        # columns that are whole numbers apart from NULLs (gust speed, cloud) stay integers for Tableau
        non_null = series.dropna()
        if len(non_null) and (non_null == non_null.round()).all() and col in (
                "WindGustSpeed", "Cloud9am", "Cloud3pm", "DirSort"):
            return SqlType.big_int()
        return SqlType.double()
    return SqlType.text()


def main():
    df = load()
    if os.path.exists(OUT_HYPER):
        os.remove(OUT_HYPER)
    cols = list(df.columns)
    types = {c: sql_type(c, df[c]) for c in cols}
    table = TableDefinition(TableName("Extract", "Extract"),
                            [TableDefinition.Column(c, types[c]) for c in cols])
    rows = []
    for rec in df.itertuples(index=False):
        row = []
        for c, v in zip(cols, rec):
            if pd.isna(v):
                row.append(None)
            elif c in ("Date", "MonthStart"):
                row.append(v.date())
            elif types[c] == SqlType.big_int():
                row.append(int(v))
            elif types[c] == SqlType.double():
                row.append(float(v))
            else:
                row.append(v)
        rows.append(row)
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, OUT_HYPER, CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema("Extract")
            conn.catalog.create_table(table)
            with Inserter(conn, table) as ins:
                ins.add_rows(rows)
                ins.execute()
            n = conn.execute_scalar_query("SELECT COUNT(*) FROM \"Extract\".\"Extract\"")
            nulls = conn.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract" WHERE "WindGustSpeed" IS NULL')
    print(f"Wrote {OUT_HYPER}: {n} rows, {len(cols)} columns, {nulls} NULL gust rows")
    return df, types


if __name__ == "__main__":
    main()
