from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import pandas as pd


INPUT_CSV = Path("/Users/isaifloreschora/Desktop/Python/Coordenadas Marco/CoordenadasDBB.csv")
OUTPUT_CSV = Path("/Users/isaifloreschora/Desktop/Python/Coordenadas Marco/CoordenadasDBB_con_distancias.csv")


def haversine_meters(lat1, lon1, lat2, lon2):
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return pd.NA

    earth_radius_m = 6371000
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return round(earth_radius_m * c, 2)


def load_coordinates(csv_path):
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    coordinate_columns = [
        "Latitud Facturacion",
        "Longitud Facturacion",
        "Latitud Check in",
        "Longitud Check in",
        "Latitud FA",
        "Longitud FA",
    ]

    for column in coordinate_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def add_distance_columns(df):
    df = df.copy()

    df["Distancia Facturacion vs Check in (m)"] = df.apply(
        lambda row: haversine_meters(
            row["Latitud Facturacion"],
            row["Longitud Facturacion"],
            row["Latitud Check in"],
            row["Longitud Check in"],
        ),
        axis=1,
    )

    df["Distancia Facturacion vs FA (m)"] = df.apply(
        lambda row: haversine_meters(
            row["Latitud Facturacion"],
            row["Longitud Facturacion"],
            row["Latitud FA"],
            row["Longitud FA"],
        ),
        axis=1,
    )

    return df


def main():
    df = load_coordinates(INPUT_CSV)
    result = add_distance_columns(df)
    result.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Archivo generado: {OUTPUT_CSV}")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
