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
import logging
from pathlib import Path

# Configuração de logging seguro
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Linha de compatibilidade
collections.Callable = collections.abc.Callable

# Configurações de segurança
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.geojson'}
MAX_AREAS = 50  # Limite máximo de áreas
MAX_AREA_NAME_LENGTH = 100

def validate_file_upload(uploaded_file):
    """Valida o arquivo enviado pelo usuário"""
    if not uploaded_file:
        return False, "Nenhum arquivo enviado"
    
    # Verifica tamanho do arquivo
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Verifica extensão
    file_extension = Path(uploaded_file.name).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"Extensão não permitida. Permitido: {ALLOWED_EXTENSIONS}"
    
    # Verifica nome do arquivo (evita caracteres perigosos)
    if any(char in uploaded_file.name for char in ['..', '/', '\\', '<', '>', '|', '*', '?']):
        return False, "Nome do arquivo contém caracteres não permitidos"
    
    return True, "Arquivo válido"

def validate_area_names(areas_list):
    """Valida os nomes das áreas fornecidos pelo usuário"""
    if not areas_list:
        return False, "Lista de áreas vazia"
    
    if len(areas_list) > MAX_AREAS:
        return False, f"Muitas áreas. Máximo: {MAX_AREAS}"
    
    for i, area in enumerate(areas_list):
        # Verifica comprimento
        if len(area) > MAX_AREA_NAME_LENGTH:
            return False, f"Nome da área {i+1} muito longo. Máximo: {MAX_AREA_NAME_LENGTH} caracteres"
        
        # Verifica caracteres perigosos (básico)
        if any(char in area for char in ['<', '>', '"', "'", '&', '\n', '\r', '\t']):
            return False, f"Nome da área {i+1} contém caracteres não permitidos"
    
    return True, "Nomes válidos"

def sanitize_filename(filename):
    """Sanitiza nome do arquivo para uso seguro"""
    # Remove caracteres perigosos
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    sanitized = ''.join(c for c in filename if c in safe_chars)
    return sanitized[:50]  # Limita comprimento

def initialize_ee():
    """
    Inicializa o Google Earth Engine usando credenciais de conta de serviço
    armazenadas nos segredos do Streamlit.
    """
    try:
        # Testa se já está inicializado
        ee.Number(1).getInfo()
        logger.info("Earth Engine já inicializado")
        return True
        
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
                    logger.error(f"Erro JSON: {json_err}")
                    st.error("❌ Credenciais JSON inválidas")
                    st.stop()
                    return False
                
                # Valida campos obrigatórios
                required_fields = ['client_email', 'private_key', 'project_id']
                missing_fields = [field for field in required_fields if not json_object.get(field)]
                if missing_fields:
                    logger.error(f"Campos obrigatórios ausentes: {missing_fields}")
                    st.error(f"❌ Campos obrigatórios ausentes nas credenciais: {missing_fields}")
                    st.stop()
                    return False
                
                # Extrai o email da conta de serviço
                service_account = json_object.get('client_email')
                
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
                
                logger.info("Earth Engine inicializado com sucesso")
                st.sidebar.success("✅ Earth Engine inicializado!")
                return True
                
            else:
                # Fallback para desenvolvimento local
                logger.warning("Credenciais GEE não encontradas, tentando inicialização local")
                st.warning("⚠️ Modo desenvolvimento local")
                ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
                st.sidebar.info("🏠 Earth Engine (local)")
                return True
                
        except Exception as ex:
            logger.error(f"Falha ao inicializar Earth Engine: {ex}")
            st.error("❌ Falha na inicialização do Earth Engine")
            with st.expander("🔍 Detalhes do erro"):
                st.error(f"Erro: {str(ex)}")
                st.markdown("""
                **Possíveis soluções:**
                1. Verifique as credenciais no Streamlit Cloud
                2. Confirme permissões da conta de serviço no GCP
                3. Verifique se Earth Engine API está habilitado
                """)
            st.stop()
            return False

@st.cache_data
def uploaded_file_to_gdf(data):
    """Converte arquivo uploaded para GeoDataFrame com validações de segurança"""
    try:
        # Validação de entrada
        is_valid, message = validate_file_upload(data)
        if not is_valid:
            raise ValueError(f"Arquivo inválido: {message}")
        
        # Cria arquivo temporário seguro
        file_extension = Path(data.name).suffix.lower()
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(tempfile.gettempdir(), safe_filename)
        
        # Garante que o caminho é seguro (dentro do diretório temporário)
        temp_dir = Path(tempfile.gettempdir()).resolve()
        file_path_resolved = Path(file_path).resolve()
        if not str(file_path_resolved).startswith(str(temp_dir)):
            raise ValueError("Caminho de arquivo inseguro")
        
        # Escreve arquivo com tratamento de erro
        try:
            with open(file_path, "wb") as file:
                file.write(data.getbuffer())
            
            # Lê o arquivo
            if file_extension == ".kml":
                gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
                gdf = gpd.read_file(file_path, driver="KML")
            else:
                gdf = gpd.read_file(file_path)
            
            # Valida GeoDataFrame
            if gdf.empty:
                raise ValueError("Arquivo GeoJSON vazio")
            
            if len(gdf) > MAX_AREAS:
                raise ValueError(f"Muitas geometrias. Máximo: {MAX_AREAS}")
            
            logger.info(f"Arquivo processado com sucesso: {len(gdf)} geometrias")
            return gdf
            
        finally:
            # Remove arquivo temporário (limpeza segura)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Erro ao limpar arquivo temporário: {cleanup_error}")
    
    except Exception as e:
        logger.error(f"Erro ao processar arquivo: {e}")
        raise

# Inicializa o Earth Engine ANTES de qualquer outra operação
if not initialize_ee():
    st.stop()

# Interface do usuário
st.set_page_config(
    page_title="Easy Bioclim",
    page_icon="⛅",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Header principal
col1, col2 = st.columns([2, 3])

with col1:
    original_title = '<h1 style="color:Blue">⛅ Easy Bioclim</h1>'
    st.markdown(original_title, unsafe_allow_html=True)
    st.caption(
        "Powered by worldclim.org, Google Earth Engine and Python | Developed by Pedro Higuchi ([@pe_hi](https://twitter.com/pe_hi))"
    )

with col2:
    st.markdown(
        "<h4 style=' color: black; background-color:lightgreen; padding:25px; border-radius: 25px; box-shadow: 0 0 0.1em black'>Web app para obtenção de dados bioclimáticos de pontos de interesse</h4>",
        unsafe_allow_html=True,
    )

# Sidebar compacto com informações de segurança
with st.sidebar:
    st.markdown("### 🔒 Limites de Segurança")
    st.info(f"""
    📁 Arquivo máx: {MAX_FILE_SIZE // (1024*1024)}MB  
    📍 Áreas máx: {MAX_AREAS}  
    🔒 Apenas GeoJSON  
    """)
    
    # Status do Earth Engine
    if st.button("🔄 Status GEE"):
        try:
            ee.Number(1).getInfo()
            st.success("✅ GEE Conectado")
        except:
            st.error("❌ GEE Desconectado")

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
st.markdown("---")

# Seção 1: Mapa
st.markdown(
    "<h3>1) Selecione e exporte os pontos de interesse 📌 </h3>",
    unsafe_allow_html=True,
)

# Mapa interativo com configurações seguras
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
    "⚠️ **Instruções:** Use apenas a ferramenta 'Draw a marker' para selecionar pontos, depois clique em 'Export'."
)

# Container centralizado para o mapa
map_container = st.container()
with map_container:
    map_data = st_folium(m, width=700, height=400, returned_objects=["last_clicked", "all_drawings"])

st.markdown("---")

# Seção 2: Upload
st.markdown(
    "<h3>2) Upload do arquivo GeoJSON 📤</h3>",
    unsafe_allow_html=True,
)

data = st.file_uploader(
    f"📁 Faça upload do arquivo GeoJSON exportado acima",
    type=["geojson"],
    help=f"Limite: {MAX_FILE_SIZE // (1024*1024)}MB • Apenas arquivos GeoJSON são aceitos"
)

st.markdown("---")

# Seção 3: Identificação das áreas
st.markdown(
    "<h3>3) Identificar as áreas #️⃣ </h3>",
    unsafe_allow_html=True,
)

input_areas = st.text_area(
    "🏷️ Digite os nomes das áreas separados por vírgula:",
    height=75,
    placeholder="Exemplo: Área 1, Ponto Central, Local de Estudo...",
    help=f"Seguir ordem do mapa • Máx: {MAX_AREAS} áreas, {MAX_AREA_NAME_LENGTH} chars/nome"
)

areas_list = []
if input_areas:
    areas_list = [area.strip() for area in input_areas.split(",") if area.strip()]
    
    # Validação dos nomes das áreas
    is_valid, message = validate_area_names(areas_list)
    if not is_valid:
        st.error(f"❌ {message}")
        areas_list = []

# Processamento principal
if data and areas_list:
    try:
        with st.spinner("📂 Processando arquivo..."):
            gdf = uploaded_file_to_gdf(data)
        
        # Validação
        if len(gdf) != len(areas_list):
            st.error(f"❌ Incompatibilidade: {len(areas_list)} nomes ≠ {len(gdf)} geometrias")
        else:
            # Preparação dos dados
            pontos = {"latitude": gdf.geometry.y, "longitude": gdf.geometry.x}
            pontos_df = pd.DataFrame(pontos)

            # Conversão para Earth Engine com tratamento de erro
            with st.spinner("🌍 Preparando dados para Earth Engine..."):
                try:
                    roi = geemap.geopandas_to_ee(gdf) 
                    dataset = ee.Image("WORLDCLIM/V1/BIO")
                    scale_resolution = dataset.projection().nominalScale().getInfo()
                except Exception as ee_error:
                    logger.error(f"Erro Earth Engine: {ee_error}")
                    st.error("❌ Erro ao preparar dados no Earth Engine")
                    raise
            
            # Extração dos valores bioclimáticos
            with st.spinner("🌡️ Extraindo dados bioclimáticos..."):
                try:
                    # Timeout de segurança para operações Earth Engine
                    sampled = dataset.sampleRegions(
                        collection=roi,
                        scale=scale_resolution,
                        geometries=False
                    )
                    
                    # Converte com limite de timeout
                    features_list = sampled.getInfo()['features']
                    
                    if not features_list:
                        raise ValueError("Nenhum dado bioclimático encontrado para as coordenadas")
                    
                    # Extrai propriedades
                    bio_data = []
                    for feature in features_list:
                        properties = feature.get('properties', {})
                        if properties:
                            bio_data.append(properties)
                    
                    if not bio_data:
                        raise ValueError("Dados bioclimáticos vazios")
                    
                    # Converte para DataFrame
                    df_extracted = pd.DataFrame(bio_data)
                    
                    # Identifica colunas bioclimáticas
                    bio_columns = [col for col in df_extracted.columns if 'bio' in col.lower()]
                    
                    if not bio_columns:
                        bio_columns = df_extracted.select_dtypes(include=[float, int]).columns.tolist()
                    
                    if not bio_columns:
                        raise ValueError("Nenhuma variável bioclimática encontrada")
                    
                    # Combina dados
                    coords_data = pd.DataFrame({
                        'latitude': pontos_df['latitude'].values,
                        'longitude': pontos_df['longitude'].values
                    })
                    
                    if len(coords_data) == len(df_extracted):
                        df_final = pd.concat([
                            coords_data.reset_index(drop=True), 
                            df_extracted[bio_columns].reset_index(drop=True)
                        ], axis=1)
                        df_final.index = areas_list
                        df_final = df_final.T
                    else:
                        raise ValueError(f"Incompatibilidade de dados: {len(coords_data)} vs {len(df_extracted)}")
                    
                except Exception as extraction_error:
                    logger.error(f"Erro na extração: {extraction_error}")
                    st.error(f"❌ Erro na extração: {str(extraction_error)}")
                    raise

            # Exibição dos resultados
            st.markdown("---")
            st.success("🎉 **Processamento concluído com sucesso!**")
            st.markdown(
                "<h3> 📊 Seus dados bioclimáticos:</h3>",
                unsafe_allow_html=True,
            )
            
            # Métricas rápidas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📍 Áreas", len(areas_list))
            with col2:
                st.metric("🌡️ Variáveis", len(bio_columns))
            with col3:
                st.metric("📏 Resolução", "~1km")
            
            st.dataframe(df_final, use_container_width=True)

            # Download em container destacado
            st.markdown("---")
            download_container = st.container()
            with download_container:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(
                        "<h3 style='text-align: center;'> 📥 Download dos dados</h3>",
                        unsafe_allow_html=True,
                    )

                    @st.cache_data
                    def convert_df(df_to_convert):
                        return df_to_convert.to_csv(sep=";", decimal=",").encode("utf-8")

                    csv = convert_df(df_final)
                    
                    # Nome de arquivo seguro baseado no timestamp
                    safe_filename = f"bioclim_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"

                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        safe_filename,
                        "text/csv",
                        key="download-csv",
                        use_container_width=True
                    )
            
            logger.info(f"Dados extraídos com sucesso para {len(areas_list)} áreas")

    except Exception as e:
        logger.error(f"Erro no processamento principal: {e}")
        st.error("❌ Erro no processamento dos dados")
        with st.expander("🔍 Detalhes do erro"):
            st.error(str(e))

elif data and not areas_list:
    st.warning("⚠️ Forneça os nomes das áreas no passo 3")
elif not data and areas_list:
    st.warning("⚠️ Faça upload do arquivo GeoJSON no passo 2")

# Informações adicionais em seção colapsável
st.markdown("---")

# Tabela de variáveis bioclimáticas em expander
with st.expander("📊 **Detalhamento das variáveis bioclimáticas** (clique para expandir)", expanded=False):
    st.markdown(
        "Para maiores informações, acessar o site do [worldclim](https://www.worldclim.org/)."
    )
    st.table(bioclim_df.set_index("Nome"))
    st.caption("📏 Resolução da fonte WorldClim V1: ~1 km (30 arc-seconds)")

# Referência em footer
st.markdown("---")
st.markdown("### 📚 Referência")
referencia = "<small>Hijmans, R.J., S.E. Cameron, J.L. Parra, P.G. Jones and A. Jarvis, 2005. Very High Resolution Interpolated Climate Surfaces for Global Land Areas. International Journal of Climatology 25: 1965-1978. doi:10.1002/joc.1276.</small>"
st.markdown(referencia, unsafe_allow_html=True)