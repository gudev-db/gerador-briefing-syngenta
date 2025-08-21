import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, List
import re

# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Gerador de Briefings - SYN",
    page_icon="📋"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton button {
        background-color: #1e88e5 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 500 !important;
    }
    .briefing-card {
        background-color: white;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #1e88e5;
    }
    .product-header {
        color: #1e88e5;
        font-size: 1.4em;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .section-header {
        color: #333;
        font-size: 1.2em;
        font-weight: 600;
        margin: 20px 0 10px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
    }
    .platform-strategy {
        background-color: #f5f7fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Dicionário de descrições de produtos (baseado nos briefings anteriores)
PRODUCT_DESCRIPTIONS = {
    "FORTENZA": "Tratamento de sementes inseticida, focado no Cerrado e posicionado para controle do complexo de lagartas e outras pragas iniciais. Comunicação focada no mercado 'on farm' (tratamento feito na fazenda).",
    "ALADE": "Fungicida para controle de doenças em soja, frequentemente posicionado em programa com Mitrion para controle de podridões de vagens e grãos.",
    "VERDAVIS": "Inseticida e acaricida composto por PLINAZOLIN® technology (nova molécula, novo grupo químico, modo de ação inédito) + lambda-cialotrina. KBFs: + mais choque, + mais espectro e + mais dias de controle.",
    "ENGEO PLENO S": "Inseticida de tradição, referência no controle de percevejos. Mote: 'Nunca foi sorte. Sempre foi Engeo Pleno S'.",
    "MEGAFOL": "Bioativador da Syngenta Biologicals. Origem 100% natural (extratos vegetais e de algas Ascophyllum nodosum). Desenvolvido para garantir que a planta alcance todo seu potencial produtivo.",
    "MIRAVIS DUO": "Fungicida da família Miravis. Traz ADEPIDYN technology (novo ingrediente ativo, novo grupo químico). Focado no controle de manchas foliares.",
    "AVICTA COMPLETO": "Oferta comercial de tratamento industrial de sementes (TSI). Composto por inseticida, fungicida e nematicida.",
    "MITRION": "Fungicida para controle de doenças em soja, frequentemente posicionado em programa com Alade.",
    "AXIAL": "Herbicida para trigo. Composto por um novo ingrediente ativo. Foco no controle do azevém.",
    "CERTANO": "Bionematicida e biofungicida. Composto pela bactéria Bacillus velezensis. Controla nematoides e fungos de solo.",
    "MANEJO LIMPO": "Programa da Syngenta para manejo integrado de plantas daninhas.",
    "ELESTAL NEO": "Fungicida para controle de doenças em soja e algodão.",
    "FRONDEO": "Inseticida para cana-de-açúcar com foco no controle da broca da cana.",
    "FORTENZA ELITE": "Oferta comercial de TSI. Solução robusta contra pragas, doenças e nematoides do Cerrado.",
    "REVERB": "Produto para manejo de doenças em soja e milho com ação prolongada ou de espectro amplo.",
    "YIELDON": "Produto focado em maximizar a produtividade das lavouras.",
    "ORONDIS FLEXI": "Fungicida com flexibilidade de uso para controle de requeima, míldios e manchas.",
    "RIZOLIQ LLI": "Inoculante ou produto para tratamento de sementes que atua na rizosfera.",
    "ARVATICO": "Fungicida ou inseticida com ação específica para controle de doenças foliares ou pragas.",
    "VERDADERO": "Produto relacionado à saúde do solo ou nutrição vegetal.",
}

# Inicializar Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    modelo_texto = genai.GenerativeModel("gemini-1.5-flash")
else:
    st.warning("API key do Gemini não encontrada. Algumas funcionalidades estarão limitadas.")

# Título do aplicativo
st.title("📋 Gerador de Briefings - SYN")
st.markdown("""
**Carregue o cronograma do Sheets e gere briefings completos seguindo o padrão SYN.**
""")

# Funções principais
def extract_product_info(text):
    """Extrai informações do produto do texto da célula"""
    if pd.isna(text):
        return None, None, None
    
    text = str(text).strip()
    
    # Padrões comuns nos briefings
    patterns = {
        'product': r'([A-Z][A-Z\s]+(?:PRO|S|NEO|LLI|ELITE|COMPLETO)?)(?:\s|$|-)',
        'culture': r'(?:soja|milho|algodão|cana|trigo|HF|café|citrus|batata)',
        'action': r'(?:depoimento|resultados|série|reforço|controle|lançamento|importância|jornada)'
    }
    
    product_match = re.search(patterns['product'], text, re.IGNORECASE)
    culture_match = re.search(patterns['culture'], text, re.IGNORECASE)
    action_match = re.search(patterns['action'], text, re.IGNORECASE)
    
    product = product_match.group(1).strip() if product_match else None
    culture = culture_match.group(0).lower() if culture_match else "MULTI"
    action = action_match.group(0).lower() if action_match else "awareness"
    
    return product, culture, action

def generate_context(row, product_name, culture, action):
    """Gera o texto de contexto baseado nas informações da linha"""
    date = row.name.strftime("%d/%m") if hasattr(row.name, 'strftime') else "Data não especificada"
    
    context = f"""
**{product_name} - {culture.upper()} - {action.upper()}**
Data prevista: {date}

Para essa pauta, vamos trabalhar com {product_name} na cultura do {culture}. O foco principal será {action}.
"""
    return context

def generate_platform_strategy(product_name, culture, action):
    """Gera estratégia por plataforma usando Gemini"""
    if not gemini_api_key:
        return "API key do Gemini não configurada. Estratégias por plataforma não disponíveis."
    
    prompt = f"""
    Como especialista em mídias sociais para o agronegócio, crie uma estratégia de conteúdo para as seguintes plataformas:
    - Instagram (Feed, Reels, Stories)
    - Facebook
    - LinkedIn
    - WhatsApp Business
    - YouTube

    Produto: {product_name}
    Cultura: {culture}
    Ação: {action}
    Descrição do produto: {PRODUCT_DESCRIPTIONS.get(product_name, 'Produto agrícola Syngenta')}

    Forneça:
    1. Estratégia específica para cada plataforma
    2. Tipos de conteúdo recomendados
    3. CTAs apropriados
    4. Melhores práticas para cada canal

    Formato: Markdown com seções para cada plataforma
    """
    
    try:
        response = modelo_texto.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao gerar estratégia: {str(e)}"

def generate_briefing(row, product_name, culture, action):
    """Gera um briefing completo"""
    description = PRODUCT_DESCRIPTIONS.get(product_name, "Descrição do produto não disponível.")
    context = generate_context(row, product_name, culture, action)
    platform_strategy = generate_platform_strategy(product_name, culture, action)
    
    briefing = f"""
<div class='briefing-card'>
    <div class='product-header'>{product_name} - {culture.upper()}</div>
    
    <div class='section-header'>📋 CONTEXTO E OBJETIVO</div>
    {context}
    
    <div class='section-header'>📝 DESCRIÇÃO DO PRODUTO</div>
    {description}
    
    <div class='section-header'>🎯 ESTRATÉGIA POR PLATAFORMA</div>
    <div class='platform-strategy'>
        {platform_strategy}
    </div>
    
    <div class='section-header'>📊 FORMATOS SUGERIDOS</div>
    <ul>
        <li><strong>Instagram:</strong> Reels + Stories + Feed post</li>
        <li><strong>Facebook:</strong> Carrossel + Link post</li>
        <li><strong>LinkedIn:</strong> Artigo + Post informativo</li>
        <li><strong>WhatsApp:</strong> Card informativo + Link</li>
        <li><strong>YouTube:</strong> Shorts + Vídeo explicativo</li>
    </ul>
    
    <div class='section-header'>📞 CONTATOS E OBSERVAÇÕES</div>
    <ul>
        <li>Validar com especialista técnico</li>
        <li>Checar disponibilidade de imagens/vídeos</li>
        <li>Incluir CTA para portal Mais Agro</li>
        <li>Seguir guidelines de marca Syngenta</li>
    </ul>
</div>
"""
    return briefing

# Interface principal
uploaded_file = st.file_uploader(
    "📤 Faça upload do cronograma do Sheets (CSV)",
    type=['csv'],
    help="O arquivo deve conter datas na primeira coluna e conteúdos nas demais colunas"
)

if uploaded_file:
    try:
        # Ler o CSV
        df = pd.read_csv(uploaded_file)
        
        # Processar datas (assumindo que a primeira coluna é a data)
        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df.set_index(date_col, inplace=True)
        
        st.success(f"✅ Arquivo carregado com {len(df)} linhas")
        
        # Selecionar coluna para análise
        content_col = st.selectbox(
            "Selecione a coluna com os conteúdos:",
            df.columns.tolist()
        )
        
        # Processar briefings
        briefings = []
        for idx, row in df.iterrows():
            content = row[content_col]
            product, culture, action = extract_product_info(content)
            
            if product and product in PRODUCT_DESCRIPTIONS:
                briefing = generate_briefing(row, product, culture, action)
                briefings.append((idx, product, briefing))
        
        # Exibir briefings
        if briefings:
            st.markdown(f"## 📋 Briefings Gerados ({len(briefings)})")
            
            for date, product, briefing in briefings:
                with st.expander(f"{date.strftime('%d/%m')} - {product}", expanded=True):
                    st.markdown(briefing, unsafe_allow_html=True)
                    
                    # Botão de download individual
                    st.download_button(
                        label=f"📥 Baixar briefing {product}",
                        data=briefing,
                        file_name=f"briefing_{product}_{date.strftime('%Y%m%d')}.html",
                        mime="text/html",
                        key=f"download_{product}_{date.strftime('%Y%m%d')}"
                    )
            
            # Botão para baixar todos os briefings
            all_briefings = "\n\n".join([f"# Briefing {product} - {date}\n{briefing}" 
                                       for date, product, briefing in briefings])
            
            st.download_button(
                label="📦 Baixar Todos os Briefings",
                data=all_briefings,
                file_name="todos_briefings_syn.html",
                mime="text/html"
            )
        else:
            st.warning("Nenhum produto reconhecido encontrado no arquivo.")
            
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")

else:
    # Exemplo de estrutura esperada
    st.markdown("""
    ### 📝 Estrutura Esperada do CSV:
    
    O arquivo CSV deve seguir este formato:
    
    | Data | Conteúdo |
    |------|----------|
    | 2024-01-01 | VERDAVIS - SOJA - DEPOIMENTO PRODUTOR |
    | 2024-01-02 | ENGEO PLENO S - MILHO - CONTROLE PERCEVEJO |
    | 2024-01-03 | MIRAVIS DUO - ALGODÃO - REFORÇO PREVENTIVO |
    
    ### 🎯 Produtos Reconhecidos:
    """
    )
    
    # Lista de produtos reconhecidos
    col1, col2, col3 = st.columns(3)
    products = list(PRODUCT_DESCRIPTIONS.keys())
    
    with col1:
        for product in products[:7]:
            st.write(f"• {product}")
    
    with col2:
        for product in products[7:14]:
            st.write(f"• {product}")
    
    with col3:
        for product in products[14:]:
            st.write(f"• {product}")

# Rodapé
st.markdown("---")
st.caption("""
Ferramenta de geração automática de briefings - Padrão SYN 📋
Desenvolvido para otimizar o planejamento de conteúdo de mídias sociais.
""")