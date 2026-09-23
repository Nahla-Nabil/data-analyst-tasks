"""
Task 7 - Tableau data source.

Reads  Cleaned_Hospital_Data.csv
Writes Hospital.hyper   (Tableau extract, table Extract.Extract, real types, blank bills kept as NULL)

Adds sort-helper columns so Tableau does not sort ordered categories alphabetically
(SeveritySort, AgeSort, StaySort, WeekdaySort); Review_Flag stays NULL when empty. The workbook itself is written by build_twb.py.
"""

import os

import pandas as pd
from tableauhyperapi import (Connection, CreateMode, HyperProcess, Inserter, SqlType, TableDefinition,
                             TableName, Telemetry)

IN_CSV = "Cleaned_Hospital_Data.csv"
OUT_HYPER = "Hospital.hyper"
DATES = ("Admission_Date", "Discharge_Date")
WEEKDAYS = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def load():
    df = pd.read_csv(IN_CSV, parse_dates=list(DATES))
    df["SeveritySort"] = df["Severity"].map({"Low": 1, "Medium": 2, "High": 3})
    df["AgeSort"] = df["Age_Group"].map({"Child (0-17)": 1, "Adult (18-39)": 2, "Middle age (40-59)": 3, "Senior (60+)": 4})
    df["StaySort"] = df["Stay_Band"].map({"1-3 days": 1, "4-7 days": 2, "8-14 days": 3, "15+ days": 4})
    df["WeekdaySort"] = df["Admission_Weekday"].map({d: i + 1 for i, d in enumerate(WEEKDAYS)})
    return df


def sql_type(col, series):
    if col in DATES:
        return SqlType.date()
    if pd.api.types.is_bool_dtype(series):
        return SqlType.bool()
    if pd.api.types.is_integer_dtype(series):
        return SqlType.big_int()
    if pd.api.types.is_float_dtype(series):
        return SqlType.double()
    return SqlType.text()


def main():
    df = load()
    if os.path.exists(OUT_HYPER):
        os.remove(OUT_HYPER)
    cols = list(df.columns)
    types = {c: sql_type(c, df[c]) for c in cols}
    table = TableDefinition(TableName("Extract", "Extract"), [TableDefinition.Column(c, types[c]) for c in cols])
    rows = []
    for rec in df.itertuples(index=False):
        row = []
        for c, v in zip(cols, rec):
            if pd.isna(v):
                row.append(None)
            elif c in DATES:
                row.append(v.date())
            elif types[c] == SqlType.big_int():
                row.append(int(v))
            elif types[c] == SqlType.double():
                row.append(float(v))
            elif types[c] == SqlType.bool():
                row.append(bool(v))
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
            n = conn.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract"')
            bills = conn.execute_scalar_query('SELECT COUNT("Bill") FROM "Extract"."Extract"')
    print(f"Wrote {OUT_HYPER}: {n} rows, {len(cols)} columns, {bills} genuine bills")
    return df, types


if __name__ == "__main__":
    main()
