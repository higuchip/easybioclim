import collections
import geopandas as gpd
import geemap.foliumap as geemap # geemap já importa ee
import json
import streamlit as st
from streamlit_folium import folium_static
import ee # Importar explicitamente para inicialização
import pandas as pd
import os # Para uploaded_file_to_gdf
import tempfile # Para uploaded_file_to_gdf
import uuid # Para uploaded_file_to_gdf

# Sua linha de compatibilidade (importante para algumas versões de Python/bibliotecas)
collections.Callable = collections.abc.Callable

# Função para inicializar o Earth Engine
def initialize_ee():
    """
    Inicializa o Google Earth Engine usando credenciais de conta de serviço
    armazenadas nos segredos do Streamlit.
    """
    try:
        # Tenta uma operação simples para verificar se já está inicializado
        ee.Number(1).getInfo()
        # st.sidebar.info("Earth Engine já inicializado.") # Opcional para debug
    except ee.EEException as e:
        # Se não inicializado ou erro de credencial, tenta inicializar
        try:
            # Verifica se o segredo com as credenciais JSON está configurado
            if "gee_service_account_credentials" in st.secrets:
                # st.secrets retorna um objeto TomlOrderedDict, pegue o valor string
                google_credentials_json_str = st.secrets["gee_service_account_credentials"]
                
                # Parse o JSON para um dicionário
                try:
                    credentials_dict = json.loads(google_credentials_json_str)
                except json.JSONDecodeError as json_err:
                    st.error(f"Erro ao decodificar o JSON das credenciais: {json_err}")
                    st.error(f"Verifique o formato do segredo 'gee_service_account_credentials'. Ele deve ser o CONTEÚDO do arquivo JSON.")
                    st.stop()
                    return

                # O e-mail da conta de serviço está dentro do arquivo JSON da chave
                service_account_email = credentials_dict.get('client_email')
                if not service_account_email:
                    st.error("A chave 'client_email' não foi encontrada nas credenciais JSON.")
                    st.stop()
                    return

                # Inicializa as credenciais.
                # A documentação do ee.ServiceAccountCredentials sugere que key_data pode ser a string JSON.
                credentials = ee.ServiceAccountCredentials(
                    service_account_email, 
                    key_data=google_credentials_json_str # Passa a string JSON diretamente
                )
                
                # Inicializa o Earth Engine com as credenciais e, opcionalmente, o projeto.
                # O endpoint de alto volume pode ser útil.
                ee.Initialize(
                    credentials=credentials,
                    opt_url='https://earthengine-highvolume.googleapis.com'
                    # project='seu-gcp-project-id' # Opcional, se o GEE precisar explicitamente
                )
                # st.sidebar.success("Earth Engine Inicializado com Sucesso via Conta de Serviço!") # Opcional para debug
            else:
                # Fallback para desenvolvimento local (se os segredos não estiverem configurados)
                # Isso pode tentar usar credenciais padrão locais ou falhar se não configurado.
                st.warning("Credenciais da conta de serviço do GEE não encontradas nos segredos. Tentando inicialização padrão (local).")
                ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')

        except Exception as ex:
            st.error(f"Falha ao inicializar o Earth Engine: {ex}")
            st.error("Verifique se o segredo 'gee_service_account_credentials' está configurado corretamente no Streamlit Cloud e se a conta de serviço tem as permissões necessárias no GCP.")
            st.stop() # Para a execução do app se o GEE não puder ser inicializado
    # except Exception as general_exception: # Captura outras exceções durante a verificação
    #     st.warning(f"Não foi possível verificar o status do EE, tentando inicializar: {general_exception}")
    #     # Proceder com a tentativa de inicialização como acima.
    #     # Esta lógica pode ser duplicada ou refatorada para evitar repetição.

# Chame a função de inicialização no início do seu script, ANTES de qualquer chamada ao 'ee' ou 'geemap' que use 'ee'.
initialize_ee()

# st.set_page_config(layout="wide") # Mova para o topo se for usar

@st.cache_data # st.cache foi depreciado, use st.cache_data ou st.cache_resource
def uploaded_file_to_gdf(data):
    # import tempfile # Já importado globalmente
    # import os # Já importado globalmente
    # import uuid # Já importado globalmente

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

# Resto do seu código...
col1, col2 = st.columns([2, 3]) # Descomente se for usar

# with col1: # Descomente se for usar
original_title = '<h1 style="color:Blue">⛅ Easy Bioclim</h1>'
st.markdown(original_title, unsafe_allow_html=True)
st.caption(
    "Powered by worldclim.org, Google Earth Engine and Python | Developed by Pedro Higuchi ([@pe_hi](https://twitter.com/pe_hi))"
)

# with col2: # Descomente se for usar
st.markdown(
    "<h4 style=' color: black; background-color:lightgreen; padding:25px; border-radius: 25px; box-shadow: 0 0 0.1em black'>Web app para obtenção de dados bioclimáticos de pontos de interesse</h4>",
    unsafe_allow_html=True,
)

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

# Certifique-se que ee está inicializado antes de chamar geemap.Map se ele for usar ee implicitamente
# A chamada initialize_ee() no início já cuida disso.
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
areas_list = []
if input_areas: # Evitar erro se input_areas for vazio
    areas_list = [area.strip() for area in input_areas.split(",") if area.strip()]


# Mova a lógica que depende de 'data' e 'input_areas' para dentro de um if
if data and areas_list: # Garante que ambos os inputs estão presentes
    gdf = uploaded_file_to_gdf(data)
    
    # Validação: Verifique se o número de geometrias corresponde ao número de nomes de áreas
    if len(gdf) != len(areas_list):
        st.error(f"O número de áreas identificadas ({len(areas_list)}) não corresponde ao número de geometrias no arquivo GeoJSON ({len(gdf)}). Por favor, verifique.")
    else:
        pontos = {"latitude": gdf.geometry.y, "longitude": gdf.geometry.x}
        pontos_df = pd.DataFrame(pontos) # Renomeado para evitar conflito com a variável 'pontos' do GDF

        gdf_json_str = gdf.to_json() # Correção: gdf é um GeoDataFrame, não precisa ser convertido para json e depois para dict
        # gdf_features = json.loads(gdf_json_str)["features"] # Esta linha é para quando se tem o JSON string
        
        # Para converter GeoDataFrame para ee.FeatureCollection diretamente com geemap:
        try:
            roi = geemap.geopandas_to_ee(gdf) 
        except Exception as e_feature_collection:
            st.error(f"Erro ao converter GeoDataFrame para ee.FeatureCollection: {e_feature_collection}")
            st.stop()

        dataset = ee.Image("WORLDCLIM/V1/BIO")
        
        try:
            # geemap.extract_values_to_points retorna uma lista de valores, que precisa ser processada.
            # Se você quer um DataFrame direto, geemap.ee_to_pandas(image.sampleRegions(collection=roi, scale=scale_resolution)) é mais comum.
            # Vamos usar o extract_values_to_points e convertê-lo.
            # Primeiro, defina a escala (resolução) para a extração. A imagem WorldClim tem uma escala nativa.
            # A escala nativa do WorldClim V1 BIO é de 30 arc-seconds (aprox. 1km).
            # Você pode obter a projeção e a escala da imagem:
            scale_resolution = dataset.projection().nominalScale().getInfo()

            df_ee_values = geemap.extract_values_to_points(roi, dataset, scale=scale_resolution) 
            # df_ee_values é uma lista de dicionários (ou uma ee.FeatureCollection dependendo da versão do geemap)
            # Se for uma ee.FeatureCollection, converta para pandas
            if isinstance(df_ee_values, ee.featurecollection.FeatureCollection):
                 df_extracted = geemap.ee_to_pandas(df_ee_values)
            elif isinstance(df_ee_values, list): # geemap pode retornar lista de listas/valores
                 # A estrutura de df_ee_values pode variar. Precisa inspecionar.
                 # Supondo que seja uma lista de valores para cada banda por ponto:
                 # E que as colunas sejam as bandas da imagem "WORLDCLIM/V1/BIO"
                 band_names = dataset.bandNames().getInfo()
                 if df_ee_values and isinstance(df_ee_values[0], list):
                    df_extracted = pd.DataFrame(df_ee_values, columns=band_names)
                 else: # Tentar uma conversão genérica se a estrutura for diferente
                    df_extracted = pd.DataFrame(df_ee_values) # Pode precisar de mais ajustes
            else:
                st.error("Formato inesperado de 'extract_values_to_points'. Verifique a saída.")
                st.stop()

        except Exception as e_extract:
            st.error(f"Erro durante a extração de valores do Earth Engine: {e_extract}")
            st.error("Isso pode ocorrer devido a problemas de permissão, formato de ROI ou limites de uso do GEE.")
            st.stop()


        st.markdown("---")

        # Concatenar com base nos índices se os dataframes tiverem o mesmo número de linhas
        if len(pontos_df) == len(df_extracted):
            df_final = pd.concat([pontos_df.reset_index(drop=True), df_extracted.reset_index(drop=True)], axis=1)
            df_final.index = areas_list
            df_final = df_final.T
            st.markdown(
                "<h3> Aqui estão suas variáveis bioclimáticas! 😀 </h3>",
                unsafe_allow_html=True,
            )
            st.dataframe(df_final) # Use st.dataframe para melhor visualização

            st.markdown(
                "<h3> 👇👇👇 clique para o download</h3>",
                unsafe_allow_html=True,
            )

            def convert_df(df_to_convert):
                return df_to_convert.to_csv(sep=";", decimal=",").encode("utf-8")

            csv = convert_df(df_final)

            st.download_button(
                "Download CSV...",
                csv,
                "bioclim_data.csv", # Nome de arquivo mais descritivo
                "text/csv",
                key="download-csv",
            )
        else:
            st.error(f"Inconsistência no número de linhas entre coordenadas ({len(pontos_df)}) e valores extraídos ({len(df_extracted)}). Não foi possível combinar os dados.")
            st.write("Dados de coordenadas:", pontos_df)
            st.write("Dados extraídos do EE:", df_extracted)


        st.markdown("---")
        st.markdown(
            "<h5>Detalhamento:</h5>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "Para maiores informações, acessar o site do [worldclim](https://www.worldclim.org/)."
        )
        st.table(bioclim_df.set_index("Nome"))
        st.caption("Resolução da fonte WorldClim V1: ~1 km (30 arc-seconds)")


elif data and not areas_list:
    st.warning("Por favor, forneça os nomes/identificações para as áreas no passo 3.")
elif not data and areas_list:
    st.warning("Por favor, faça o upload do arquivo GeoJSON no passo 2.")


st.markdown("---")
st.subheader("Referência")
referencia = "<p>Hijmans, R.J., S.E. Cameron, J.L. Parra, P.G. Jones and A. Jarvis, 2005. Very High Resolution Interpolated Climate Surfaces for Global Land Areas. International Journal of Climatology 25: 1965-1978. doi:10.1002/joc.1276.</p>"
st.markdown(referencia, unsafe_allow_html=True)