from html import escape
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="Coordenadas Marco", layout="wide")

DEFAULT_CSV_PATH = Path("/Users/isaifloreschora/Desktop/Python/Coordenadas Marco/CoordenadasDBB.csv")


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


@st.cache_data
def load_coordinates_csv(file_source):
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    last_error = None

    for encoding in encodings:
        try:
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            df = pd.read_csv(file_source, encoding=encoding)
            return prepare_coordinates_df(df), encoding
        except Exception as exc:
            last_error = exc

    raise ValueError(f"No se pudo leer el CSV: {last_error}")


def prepare_coordinates_df(df):
    df = df.copy()
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
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["PDV"] = df["PDV"].astype("string").str.strip()
    return df


def extract_unique_pairs(group, lat_column, lon_column):
    pairs = (
        group[[lat_column, lon_column]]
        .dropna()
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    return [(float(lat), float(lon)) for lat, lon in pairs]


def first_facturation_pair(group):
    pairs = extract_unique_pairs(group, "Latitud Facturacion", "Longitud Facturacion")
    if pairs:
        return pairs[0]
    return (pd.NA, pd.NA)


def consolidate_coordinates(df):
    grouped_rows = []
    max_checkins = 0
    max_fa = 0

    for pdv, group in df.groupby("PDV", dropna=False):
        fact_lat, fact_lon = first_facturation_pair(group)
        checkins = extract_unique_pairs(group, "Latitud Check in", "Longitud Check in")
        fa_points = extract_unique_pairs(group, "Latitud FA", "Longitud FA")

        max_checkins = max(max_checkins, len(checkins))
        max_fa = max(max_fa, len(fa_points))

        grouped_rows.append(
            {
                "PDV": pdv,
                "Facturacion": (fact_lat, fact_lon),
                "Checkins": checkins,
                "FA": fa_points,
            }
        )

    consolidated = []
    for row in grouped_rows:
        fact_lat, fact_lon = row["Facturacion"]
        consolidated_row = {
            "PDV": row["PDV"],
            "Latitud Facturacion": fact_lat,
            "Longitud Facturacion": fact_lon,
        }

        for index in range(max_checkins):
            if index < len(row["Checkins"]):
                check_lat, check_lon = row["Checkins"][index]
                consolidated_row[f"Latitud Check in {index + 1}"] = check_lat
                consolidated_row[f"Longitud Check in {index + 1}"] = check_lon
                consolidated_row[f"Distancia Facturacion vs Check in {index + 1} (m)"] = haversine_meters(
                    fact_lat, fact_lon, check_lat, check_lon
                )
            else:
                consolidated_row[f"Latitud Check in {index + 1}"] = pd.NA
                consolidated_row[f"Longitud Check in {index + 1}"] = pd.NA
                consolidated_row[f"Distancia Facturacion vs Check in {index + 1} (m)"] = pd.NA

        for index in range(max_fa):
            if index < len(row["FA"]):
                fa_lat, fa_lon = row["FA"][index]
                consolidated_row[f"Latitud FA {index + 1}"] = fa_lat
                consolidated_row[f"Longitud FA {index + 1}"] = fa_lon
                consolidated_row[f"Distancia Facturacion vs FA {index + 1} (m)"] = haversine_meters(
                    fact_lat, fact_lon, fa_lat, fa_lon
                )
            else:
                consolidated_row[f"Latitud FA {index + 1}"] = pd.NA
                consolidated_row[f"Longitud FA {index + 1}"] = pd.NA
                consolidated_row[f"Distancia Facturacion vs FA {index + 1} (m)"] = pd.NA

        consolidated.append(consolidated_row)

    return pd.DataFrame(consolidated), max_checkins, max_fa


def format_number(value, decimals=6):
    if pd.isna(value):
        return "Sin dato"
    return f"{float(value):,.{decimals}f}"


def format_distance(value):
    if pd.isna(value):
        return "Sin distancia"
    return f"{float(value):,.2f} m"


def build_google_maps_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"


def classify_distance(distance, correct_threshold, review_threshold):
    if pd.isna(distance):
        return "Sin dato", "sin-dato"
    if float(distance) <= correct_threshold:
        return "Correcto", "correcto"
    if float(distance) <= review_threshold:
        return "Revisar", "revisar"
    return "Incorrecto", "incorrecto"


def render_coord_block(label, lat, lon, distance=None, status_label=None, status_class=None):
    if pd.isna(lat) or pd.isna(lon):
        return '<div class="coord-card empty">Sin dato</div>'

    map_link = escape(build_google_maps_link(float(lat), float(lon)), quote=True)
    distance_html = ""
    if distance is not None:
        distance_html = f'<div class="coord-distance">{escape(format_distance(distance))}</div>'
    status_html = ""
    if status_label and status_class:
        status_html = f'<div class="status-pill {status_class}">{escape(status_label)}</div>'

    return f"""
    <div class="coord-card">
        <div class="coord-label">{escape(label)}</div>
        <div class="coord-value">{escape(format_number(lat))}, {escape(format_number(lon))}</div>
        {distance_html}
        {status_html}
        <a class="map-link" href="{map_link}" target="_blank" rel="noopener noreferrer">Abrir mapa</a>
    </div>
    """


def build_html_table(df, max_checkins, max_fa, correct_threshold, review_threshold):
    headers = ["PDV", "Facturacion"]
    headers.extend([f"Check in {index}" for index in range(1, max_checkins + 1)])
    headers.extend([f"FA {index}" for index in range(1, max_fa + 1)])

    rows_html = []
    for _, row in df.iterrows():
        cells = [f"<td class='pdv-cell'>{escape(str(row['PDV']))}</td>"]
        cells.append(
            "<td>"
            + render_coord_block(
                "Facturacion",
                row["Latitud Facturacion"],
                row["Longitud Facturacion"],
            )
            + "</td>"
        )

        for index in range(1, max_checkins + 1):
            status_label, status_class = classify_distance(
                row[f"Distancia Facturacion vs Check in {index} (m)"],
                correct_threshold,
                review_threshold,
            )
            cells.append(
                "<td>"
                + render_coord_block(
                    f"Check in {index}",
                    row[f"Latitud Check in {index}"],
                    row[f"Longitud Check in {index}"],
                    row[f"Distancia Facturacion vs Check in {index} (m)"],
                    status_label,
                    status_class,
                )
                + "</td>"
            )

        for index in range(1, max_fa + 1):
            cells.append(
                "<td>"
                + render_coord_block(
                    f"FA {index}",
                    row[f"Latitud FA {index}"],
                    row[f"Longitud FA {index}"],
                    row[f"Distancia Facturacion vs FA {index} (m)"],
                )
                + "</td>"
            )

        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_html = "".join(rows_html)

    return f"""
    <html>
    <head>
        <style>
            :root {{
                color-scheme: light;
                --bg: #f4efe6;
                --panel: #fffaf3;
                --line: #dccbb4;
                --ink: #2f2419;
                --muted: #6b5a4a;
                --accent: #a44a3f;
                --accent-soft: #f2d1c9;
            }}

            * {{
                box-sizing: border-box;
                font-family: "Avenir Next", "Segoe UI", sans-serif;
            }}

            body {{
                margin: 0;
                background: linear-gradient(180deg, #f9f4eb 0%, #f1e7d9 100%);
                color: var(--ink);
            }}

            .table-shell {{
                position: relative;
                padding: 12px;
            }}

            .table-wrap {{
                overflow: auto;
                border: 1px solid rgba(90, 66, 44, 0.18);
                border-radius: 18px;
                background: rgba(255, 250, 243, 0.96);
                box-shadow: 0 18px 50px rgba(88, 61, 39, 0.1);
            }}

            table {{
                width: max-content;
                min-width: 100%;
                border-collapse: separate;
                border-spacing: 0;
            }}

            th {{
                position: sticky;
                top: 0;
                z-index: 3;
                background: #fff7ec;
                color: #704730;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 12px;
                padding: 14px 12px;
                border-bottom: 1px solid var(--line);
            }}

            td {{
                padding: 10px;
                border-bottom: 1px solid rgba(220, 203, 180, 0.55);
                vertical-align: top;
                min-width: 220px;
            }}

            tr:nth-child(even) td {{
                background: rgba(255, 255, 255, 0.45);
            }}

            .pdv-cell {{
                min-width: 260px;
                font-weight: 700;
                color: #543826;
            }}

            .coord-card {{
                background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(251,244,235,0.96) 100%);
                border: 1px solid rgba(164, 74, 63, 0.16);
                border-radius: 16px;
                padding: 12px;
                min-height: 116px;
                box-shadow: 0 8px 24px rgba(113, 74, 45, 0.07);
            }}

            .coord-card.empty {{
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--muted);
                border-style: dashed;
                box-shadow: none;
            }}

            .coord-label {{
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: var(--accent);
                margin-bottom: 8px;
            }}

            .coord-value {{
                font-size: 14px;
                line-height: 1.45;
                margin-bottom: 8px;
            }}

            .coord-distance {{
                font-size: 13px;
                color: #6d4a36;
                margin-bottom: 8px;
            }}

            .status-pill {{
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 6px 10px;
                margin-bottom: 10px;
                font-size: 12px;
                font-weight: 800;
            }}

            .status-pill.correcto {{
                background: #dcfce7;
                color: #166534;
            }}

            .status-pill.revisar {{
                background: #fef3c7;
                color: #92400e;
            }}

            .status-pill.incorrecto {{
                background: #fee2e2;
                color: #991b1b;
            }}

            .status-pill.sin-dato {{
                background: #ece7df;
                color: #6b5a4a;
            }}

            .map-link {{
                display: inline-flex;
                align-items: center;
                text-decoration: none;
                border-radius: 999px;
                padding: 8px 12px;
                background: var(--accent-soft);
                color: #7c2d23;
                font-weight: 800;
            }}

            .map-link:hover {{
                background: #e7b8ae;
            }}
        </style>
    </head>
    <body>
        <div class="table-shell">
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>{header_html}</tr>
                    </thead>
                    <tbody>{body_html}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


st.title("Coordenadas Marco")
st.caption("Unifica cada PDV en una sola fila, abre cada coordenada directo en Google Maps y clasifica los Check in por distancia.")

uploaded_file = st.file_uploader("Sube un CSV si quieres reemplazar el archivo base", type=["csv"])

try:
    source = uploaded_file if uploaded_file is not None else DEFAULT_CSV_PATH
    raw_df, encoding = load_coordinates_csv(source)
except Exception as exc:
    st.error(str(exc))
    st.stop()

if raw_df.empty:
    st.warning("El archivo no contiene registros.")
    st.stop()

consolidated_df, max_checkins, max_fa = consolidate_coordinates(raw_df)

st.sidebar.header("Clasificacion")
correct_threshold = st.sidebar.number_input(
    "Metros maximos para Correcto",
    min_value=0,
    value=100,
    step=10,
)
review_threshold = st.sidebar.number_input(
    "Metros maximos para Revisar",
    min_value=int(correct_threshold),
    value=max(300, int(correct_threshold)),
    step=10,
)

search_term = st.text_input("Buscar PDV", placeholder="Ej. AB AVILA AHOME")
if search_term:
    filtered_df = consolidated_df[
        consolidated_df["PDV"].str.contains(search_term, case=False, na=False)
    ].copy()
else:
    filtered_df = consolidated_df.copy()

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("PDVs unicos", f"{len(consolidated_df):,}")
metric_2.metric("Max. Check in por PDV", max_checkins)
metric_3.metric("Max. FA por PDV", max_fa)

distance_columns = [
    column
    for column in filtered_df.columns
    if column.startswith("Distancia Facturacion vs Check in")
]
all_distances = pd.to_numeric(filtered_df[distance_columns].stack(), errors="coerce").dropna()
correct_count = int((all_distances <= correct_threshold).sum())
review_count = int(((all_distances > correct_threshold) & (all_distances <= review_threshold)).sum())
incorrect_count = int((all_distances > review_threshold).sum())

status_1, status_2, status_3 = st.columns(3)
status_1.metric("Check in correctos", f"{correct_count:,}")
status_2.metric("Check in para revisar", f"{review_count:,}")
status_3.metric("Check in incorrectos", f"{incorrect_count:,}")

st.download_button(
    "Descargar CSV consolidado",
    data=consolidated_df.to_csv(index=False, encoding="utf-8-sig"),
    file_name="CoordenadasDBB_consolidado.csv",
    mime="text/csv",
)

components.html(
    build_html_table(filtered_df, max_checkins, max_fa, correct_threshold, review_threshold),
    height=900,
    scrolling=True,
)
