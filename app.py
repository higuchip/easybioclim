import collections
from turtle import width
import folium
import geopandas as gpd
import geemap.foliumap as geemap
import json
import streamlit as st
from streamlit_folium import folium_static
import ee
import pandas as pd


collections.Callable = collections.abc.Callable

# st.set_page_config(layout="wide")


@st.cache(allow_output_mutation=True)
def uploaded_file_to_gdf(data):
    import tempfile
    import os
    import uuid

    _, file_extension = os.path.splitext(data.name)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")

    with open(file_path, "wb") as file:
        file.write(data.getbuffer())

    if file_path.lower().endswith(".kml"):
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
        gdf = gpd.read_file(file_path, driver="KML")
    else:
        gdf = gpd.read_file(file_path)

    return gdf


col1, col2 = st.columns([2, 3])

# with col1:
original_title = '<h1 style="color:Blue">⛅ Easy Bioclim</h1>'
st.markdown(original_title, unsafe_allow_html=True)
st.caption(
    "Powered by worldclim.org, Google Earth Engine and Python | Developed by Pedro Higuchi ([@pe_hi](https://twitter.com/pe_hi))"
)


# with col2:
# st.header("Web app para obtenção de dados bioclimáticos de pontos geográficos de interesse")
st.markdown(
    "<h4 style=' color: black; background-color:lightgreen; padding:25px; border-radius: 25px; box-shadow: 0 0 0.1em black'>Web app para obtenção de dados bioclimáticos de pontos de interesse</h4>",
    unsafe_allow_html=True,
)

# st.markdown(
#    "Variáveis bioclimáticas são derivadas a partir de dados de temperatura e precipitação e desempenham grande influência sobre o desenvolvimento dos organismos e processos ecossistêmicos (Hijmans et al. 2005)."
# )

# st.markdown(
#    "A obtenção das mesmas pode ser util para estudos ecológicos, como, por exemplo, na modelagem de nicho ecológico de espécies e variação espacial de comunidades de espécies."
# )

bios_symbols = [
    "BIO1",
    "BIO2",
    "BIO3",
    "BIO4",
    "BIO5",
    "BIO6",
    "BIO7",
    "BIO8",
    "BIO9",
    "BIO10",
    "BIO11",
    "BIO12",
    "BIO13",
    "BIO14",
    "BIO15",
    "BIO16",
    "BIO17",
    "BIO18",
    "BIO19",
]
bios_names = [
    "Temperatura média anual",
    "Média da amplitude da temperatura diurna",
    "Isotermalidade",
    "Sazonalidade da Temperatura",
    "Temperatura máxima do mês mais quente",
    "Temperatura mínima do mês mais frio",
    "Amplitude da temperatura anual",
    "Média da temperatura no trimestre mais úmido",
    "Média da temperatura no trimestre mais seco",
    "Média da temperatura no trimestre mais quente",
    "Média da temperatura no trimestre mais frio",
    "Precipitação anual",
    "Precipitação no mês mais úmido",
    "Precipitação no mês mais seco",
    "Sazonalidade de precipitação",
    "Precipitação no trimestre mais úmido",
    "Precipitação no trimestre mais seco",
    "Precipitação no trimestre mais quente",
    "Precipitação no trimestre mais frio",
]

units = [
    "°C",
    "°C",
    "%",
    "°C",
    "°C",
    "°C",
    "°C",
    "°C",
    "°C",
    "°C",
    "°C",
    "mm",
    "mm",
    "mm",
    "%",
    "mm",
    "mm",
    "mm",
    "mm",
]

scale = [
    "0.1",
    "0.1",
    " ",
    "0.01",
    "0.1",
    "0.1",
    "0.1",
    "0.1",
    "0.1",
    "0.1",
    "0.1",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
    " ",
]


zipped = list(zip(bios_symbols, bios_names, units, scale))

bioclim_df = pd.DataFrame(zipped, columns=["Nome", "Descrição", "Unidade", "Escala"])

##st.markdown("""---""")
st.text(" ")
st.text(" ")


st.markdown("""---""")
st.markdown(
    "<h3>1) Selecione e exporte os pontos de interesse 📌 </h3>",
    unsafe_allow_html=True,
)

m = geemap.Map(
    center=[-27.86, -50.20],
    zoom=10,
    basemap="HYBRID",
    plugin_Draw=True,
    Draw_export=True,
    locate_control=True,
    plugin_LatLngPopup=False,
)
st.warning(
    "Usar **apenas** a ferramenta 'Draw a marker', para selecionar os pontos de interesse e, em seguida, clicar em 'Export'."
)
folium_static(m, width=700, height=400)

st.markdown("""---""")
st.markdown(
    "<h3>2) Upload do arquivo GeoJSON 📤</h3>",
    unsafe_allow_html=True,
)
data = st.file_uploader(
    "Fazer o upload do arquivo GeoJSON exportado no passo acima para utilizar como áreas de interesse 👇👇",
    type=["geojson"],
)

st.markdown("""---""")

st.markdown(
    "<h3>3) Indicar a identificação das áreas #️⃣ </h3>",
    unsafe_allow_html=True,
)

input_areas = st.text_area(
    "Seguir a ordem indicada no mapa e separar por vírgula. Usar tecla 'tab' para confirmar",
    height=50,
)
areas_list = input_areas.split(",")

if input_areas:
    gdf = uploaded_file_to_gdf(data)
    pontos = {"latitude": gdf.geometry.y, "longitude": gdf.geometry.x}
    pontos = pd.DataFrame(pontos)

    gdf = gdf.to_json()
    gdf = json.loads(gdf)
    gdf = gdf["features"]

    roi = ee.FeatureCollection(gdf)
    dataset = ee.Image("WORLDCLIM/V1/BIO")
    df = geemap.ee_to_pandas(geemap.extract_values_to_points(roi, dataset))

    st.markdown("---")

    df_final = pd.concat([pontos, df], axis=1)
    df_final.index = areas_list
    df_final = df_final.T
    st.markdown(
        "<h3> Aqui estão suas variáveis bioclimáticas! 😀 </h3>",
        unsafe_allow_html=True,
    )

    df_final

    st.markdown(
        "<h3> 👇👇👇 clique para  o download</h3>",
        unsafe_allow_html=True,
    )

    def convert_df(df):
        return df.to_csv(sep=";", decimal=",").encode("utf-8")

    csv = convert_df(df_final)

    st.download_button(
        "Download CSV...",
        csv,
        "file.csv",
        "text/csv",
        key="download-csv",
    )
    st.markdown("---")
    st.markdown(
        "<h5>Detalhamento:</h5>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Para maiores informações, acessar o site do [worldclim](https://www.worldclim.org/)."
    )
    st.table(bioclim_df.set_index("Nome"))
    st.caption("Resolução: 927,67 metros")

st.markdown("---")
st.subheader("Referência")
referencia = "<p>Hijmans, R.J., S.E. Cameron, J.L. Parra, P.G. Jones and A. Jarvis, 2005. Very High Resolution Interpolated Climate Surfaces for Global Land Areas. International Journal of Climatology 25: 1965-1978. doi:10.1002/joc.1276.</p>"
st.markdown(referencia, unsafe_allow_html=True)
