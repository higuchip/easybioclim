import collections
import geopandas as gpd
import geemap.foliumap as geemap
import json
import streamlit as st
from streamlit_folium import st_folium
import ee
import pandas as pd
import os
import tempfile
import uuid

# Linha de compatibilidade
collections.Callable = collections.abc.Callable

def initialize_ee():
    """
    Inicializa o Google Earth Engine usando credenciais de conta de serviço
    armazenadas nos segredos do Streamlit.
    """
    try:
        # Testa se já está inicializado
        ee.Number(1).getInfo()
        return  # Já inicializado, não precisa fazer nada
        
    except ee.EEException:
        # Não inicializado, procede com a inicialização
        try:
            # Verifica se as credenciais estão nos segredos do Streamlit
            if "gee_service_account_credentials" in st.secrets:
                # Obtém a string JSON das credenciais
                json_data = st.secrets["gee_service_account_credentials"]
                
                # Parse do JSON (seguindo o tutorial)
                try:
                    json_object = json.loads(json_data, strict=False)
                except json.JSONDecodeError as json_err:
                    st.error(f"Erro ao decodificar JSON das credenciais: {json_err}")
                    st.error("Verifique se o segredo 'gee_service_account_credentials' contém um JSON válido.")
                    st.stop()
                    return
                
                # Extrai o email da conta de serviço
                service_account = json_object.get('client_email')
                if not service_account:
                    st.error("Campo 'client_email' não encontrado nas credenciais.")
                    st.stop()
                    return
                
                # Converte de volta para string JSON (conforme tutorial)
                json_object_str = json.dumps(json_object)
                
                # Cria as credenciais
                credentials = ee.ServiceAccountCredentials(
                    service_account, 
                    key_data=json_object_str
                )
                
                # Inicializa o Earth Engine
                ee.Initialize(
                    credentials=credentials,
                    opt_url='https://earthengine-highvolume.googleapis.com'
                )
                
                st.sidebar.success("✅ Earth Engine inicializado com sucesso!")
                
            else:
                # Fallback para desenvolvimento local
                st.warning("⚠️ Credenciais do GEE não encontradas. Tentando inicialização local...")
                ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
                st.sidebar.info("🏠 Earth Engine inicializado localmente")
                
        except Exception as ex:
            st.error(f"❌ Falha ao inicializar o Earth Engine: {ex}")
            st.error("""
            **Possíveis soluções:**
            1. Verifique se o segredo 'gee_service_account_credentials' está configurado no Streamlit Cloud
            2. Confirme se o JSON das credenciais está completo e válido
            3. Verifique se a conta de serviço tem as permissões necessárias no Google Cloud Platform
            4. Confirme se o Earth Engine API está habilitado no seu projeto GCP
            """)
            st.stop()

# Inicializa o Earth Engine ANTES de qualquer outra operação
initialize_ee()

@st.cache_data
def uploaded_file_to_gdf(data):
    """Converte arquivo uploaded para GeoDataFrame"""
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

# Interface do usuário
col1, col2 = st.columns([2, 3])

original_title = '<h1 style="color:Blue">⛅ Easy Bioclim</h1>'
st.markdown(original_title, unsafe_allow_html=True)
st.caption(
    "Powered by worldclim.org, Google Earth Engine and Python | Developed by Pedro Higuchi ([@pe_hi](https://twitter.com/pe_hi))"
)

st.markdown(
    "<h4 style=' color: black; background-color:lightgreen; padding:25px; border-radius: 25px; box-shadow: 0 0 0.1em black'>Web app para obtenção de dados bioclimáticos de pontos de interesse</h4>",
    unsafe_allow_html=True,
)

# Definições das variáveis bioclimáticas
bios_symbols = [
    "BIO1", "BIO2", "BIO3", "BIO4", "BIO5", "BIO6", "BIO7", "BIO8", "BIO9", "BIO10",
    "BIO11", "BIO12", "BIO13", "BIO14", "BIO15", "BIO16", "BIO17", "BIO18", "BIO19",
]
bios_names = [
    "Temperatura média anual", "Média da amplitude da temperatura diurna", "Isotermalidade",
    "Sazonalidade da Temperatura", "Temperatura máxima do mês mais quente", "Temperatura mínima do mês mais frio",
    "Amplitude da temperatura anual", "Média da temperatura no trimestre mais úmido",
    "Média da temperatura no trimestre mais seco", "Média da temperatura no trimestre mais quente",
    "Média da temperatura no trimestre mais frio", "Precipitação anual", "Precipitação no mês mais úmido",
    "Precipitação no mês mais seco", "Sazonalidade de precipitação", "Precipitação no trimestre mais úmido",
    "Precipitação no trimestre mais seco", "Precipitação no trimestre mais quente", "Precipitação no trimestre mais frio",
]
units = [
    "°C", "°C", "%", "°C", "°C", "°C", "°C", "°C", "°C", "°C", "°C",
    "mm", "mm", "mm", "%", "mm", "mm", "mm", "mm",
]
scale = [
    "0.1", "0.1", " ", "0.01", "0.1", "0.1", "0.1", "0.1", "0.1", "0.1", "0.1",
    " ", " ", " ", " ", " ", " ", " ", " ",
]

zipped = list(zip(bios_symbols, bios_names, units, scale))
bioclim_df = pd.DataFrame(zipped, columns=["Nome", "Descrição", "Unidade", "Escala"])

st.text(" ")
st.text(" ")
st.markdown("""---""")

st.markdown(
    "<h3>1) Selecione e exporte os pontos de interesse 📌 </h3>",
    unsafe_allow_html=True,
)

# Mapa interativo
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
st_folium(m, width=700, height=400)

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
    height=75,
)
areas_list = []
if input_areas:
    areas_list = [area.strip() for area in input_areas.split(",") if area.strip()]

# Processamento principal
if data and areas_list:
    try:
        gdf = uploaded_file_to_gdf(data)
        
        # Validação
        if len(gdf) != len(areas_list):
            st.error(f"❌ Número de áreas ({len(areas_list)}) ≠ número de geometrias ({len(gdf)})")
        else:
            # Preparação dos dados
            pontos = {"latitude": gdf.geometry.y, "longitude": gdf.geometry.x}
            pontos_df = pd.DataFrame(pontos)

            # Conversão para Earth Engine
            roi = geemap.geopandas_to_ee(gdf) 
            dataset = ee.Image("WORLDCLIM/V1/BIO")
            
            # Extração dos valores
            scale_resolution = dataset.projection().nominalScale().getInfo()
            
            with st.spinner("🌍 Extraindo dados bioclimáticos..."):
                # Usa sampleRegions para extração mais robusta
                sampled = dataset.sampleRegions(
                    collection=roi,
                    scale=scale_resolution,
                    geometries=False  # Não precisamos das geometrias
                )
                
                # Converte ee.FeatureCollection para lista de features
                features_list = sampled.getInfo()['features']
                
                # Extrai as propriedades (dados bioclimáticos) de cada feature
                bio_data = []
                for feature in features_list:
                    bio_data.append(feature['properties'])
                
                # Converte para DataFrame
                df_extracted = pd.DataFrame(bio_data)
                
                # Garante que temos as colunas bio (algumas podem ter nomes ligeiramente diferentes)
                bio_columns = [col for col in df_extracted.columns if 'bio' in col.lower()]
                
                # Se não encontrou colunas bio, usa todas as colunas numéricas
                if not bio_columns:
                    bio_columns = df_extracted.select_dtypes(include=[float, int]).columns.tolist()
                
                # Combina coordenadas com dados bioclimáticos
                coords_data = pd.DataFrame({
                    'latitude': pontos_df['latitude'].values,
                    'longitude': pontos_df['longitude'].values
                })
                
                # Verifica se o número de linhas é compatível
                if len(coords_data) == len(df_extracted):
                    df_final = pd.concat([
                        coords_data.reset_index(drop=True), 
                        df_extracted[bio_columns].reset_index(drop=True)
                    ], axis=1)
                    df_final.index = areas_list
                    df_final = df_final.T
                else:
                    st.error(f"❌ Incompatibilidade: {len(coords_data)} coordenadas vs {len(df_extracted)} extrações")
                    raise ValueError("Número de pontos não coincide com extrações")

            st.markdown("---")
            st.markdown(
                "<h3> ✅ Aqui estão suas variáveis bioclimáticas! 😀 </h3>",
                unsafe_allow_html=True,
            )
            st.dataframe(df_final, use_container_width=True)

            st.markdown(
                "<h3> 👇👇👇 clique para o download</h3>",
                unsafe_allow_html=True,
            )

            @st.cache_data
            def convert_df(df_to_convert):
                return df_to_convert.to_csv(sep=";", decimal=",").encode("utf-8")

            csv = convert_df(df_final)

            st.download_button(
                "📥 Download CSV",
                csv,
                "bioclim_data.csv",
                "text/csv",
                key="download-csv",
            )

    except Exception as e:
        st.error(f"❌ Erro no processamento: {e}")
        st.error("Verifique se o arquivo GeoJSON está válido e tente novamente.")

elif data and not areas_list:
    st.warning("⚠️ Por favor, forneça os nomes/identificações para as áreas no passo 3.")
elif not data and areas_list:
    st.warning("⚠️ Por favor, faça o upload do arquivo GeoJSON no passo 2.")

# Informações adicionais
st.markdown("---")
st.markdown(
    "<h5>📊 Detalhamento das variáveis bioclimáticas:</h5>",
    unsafe_allow_html=True,
)
st.markdown(
    "Para maiores informações, acessar o site do [worldclim](https://www.worldclim.org/)."
)
st.table(bioclim_df.set_index("Nome"))
st.caption("📏 Resolução da fonte WorldClim V1: ~1 km (30 arc-seconds)")

st.markdown("---")
st.subheader("📚 Referência")
referencia = "<p>Hijmans, R.J., S.E. Cameron, J.L. Parra, P.G. Jones and A. Jarvis, 2005. Very High Resolution Interpolated Climate Surfaces for Global Land Areas. International Journal of Climatology 25: 1965-1978. doi:10.1002/joc.1276.</p>"
st.markdown(referencia, unsafe_allow_html=True)