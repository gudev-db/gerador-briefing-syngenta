import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, List, Tuple
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
    .input-container {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
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
    "MIRAVIS": "Fungicida da família Miravis para controle de doenças.",
    "MIRAVIS PRO": "Fungicida premium da família Miravis para controle avançado de doenças.",
    "INSTIVO": "Lagarticida posicionado como especialista no controle de lagartas do gênero Spodoptera.",
    "CYPRESS": "Fungicida posicionado para últimas aplicações na soja, consolidando o manejo de doenças.",
    "CALARIS": "Herbicida composto por atrazina + mesotriona para controle de plantas daninhas no milho.",
    "SPONTA": "Inseticida para algodão com PLINAZOLIN® technology para controle de bicudo e outras pragas.",
    "INFLUX": "Inseticida lagarticida premium para controle de todas as lagartas, especialmente helicoverpa.",
    "JOINER": "Inseticida acaricida com tecnologia PLINAZOLIN para culturas hortifrúti.",
    "DUAL GOLD": "Herbicida para manejo de plantas daninhas.",
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
**Digite o conteúdo da célula do calendário para gerar um briefing completo no padrão SYN.**
""")

# Funções principais
def extract_product_info(text: str) -> Tuple[str, str, str]:
    """Extrai informações do produto do texto da célula"""
    if not text or not text.strip():
        return None, None, None
    
    text = str(text).strip()
    
    # Remover emojis e marcadores
    clean_text = re.sub(r'[🔵🟠🟢🔴🟣🔃📲]', '', text).strip()
    
    # Padrões para extração
    patterns = {
        'product': r'\b([A-Z][A-Za-z\s]+(?:PRO|S|NEO|LLI|ELITE|COMPLETO|DUO|FLEXI|PLENO|XTRA)?)\b',
        'culture': r'\b(soja|milho|algodão|cana|trigo|HF|café|citrus|batata|melão|uva|tomate|multi)\b',
        'action': r'\b(depoimento|resultados|série|reforço|controle|lançamento|importância|jornada|conceito|vídeo|ação|diferenciais|awareness|problemática|glossário|manejo|aplicação|posicionamento)\b'
    }
    
    product_match = re.search(patterns['product'], clean_text, re.IGNORECASE)
    culture_match = re.search(patterns['culture'], clean_text, re.IGNORECASE)
    action_match = re.search(patterns['action'], clean_text, re.IGNORECASE)
    
    product = product_match.group(1).strip().upper() if product_match else None
    culture = culture_match.group(0).lower() if culture_match else "multi"
    action = action_match.group(0).lower() if action_match else "conscientização"
    
    return product, culture, action

def generate_context(content, product_name, culture, action):
    """Gera o texto de contexto baseado nas informações"""
    # Usar a descrição do produto do dicionário em vez do Gemini
    description = PRODUCT_DESCRIPTIONS.get(product_name, "Descrição do produto não disponível.")
    
    context = f"""
**{product_name} - {culture.upper()} - {action.upper()}**
Conteúdo: {content}

Para essa pauta, vamos trabalhar com {product_name} na cultura do {culture}. O foco principal será {action}.

{description}
"""
    return context

def generate_platform_strategy(product_name, culture, action, content):
    """Gera estratégia por plataforma usando Gemini"""
    if not gemini_api_key:
        return "API key do Gemini não configurada. Estratégias por plataforma não disponíveis."
    
    prompt = f"""
    Como especialista em mídias sociais para o agronegócio Syngenta, crie uma estratégia de conteúdo detalhada:

    **PRODUTO:** {product_name}
    **CULTURA:** {culture}
    **AÇÃO:** {action}
    **CONTEÚDO ORIGINAL:** {content}
    **DESCRIÇÃO DO PRODUTO:** {PRODUCT_DESCRIPTIONS.get(product_name, 'Produto agrícola Syngenta')}

    **FORNECER ESTRATÉGIA PARA:**
    - Instagram (Feed, Reels, Stories)
    - Facebook 
    - LinkedIn
    - WhatsApp Business
    - YouTube
    - Portal Mais Agro (blog)

    **INCLUIR PARA CADA PLATAFORMA:**
    1. Tipo de conteúdo recomendado
    2. Formato ideal (vídeo, carrossel, estático, etc.)
    3. Tom de voz apropriado
    4. CTA específico
    5. Melhores práticas

    **FORMATO:** Markdown com seções claras
    """
    
    try:
        response = modelo_texto.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao gerar estratégia: {str(e)}"

def generate_briefing(content, product_name, culture, action):
    """Gera um briefing completo"""
    description = PRODUCT_DESCRIPTIONS.get(product_name, "Descrição do produto não disponível.")
    context = generate_context(content, product_name, culture, action)
    platform_strategy = generate_platform_strategy(product_name, culture, action, content)
    
    briefing = f"""
<div class='briefing-card'>
    <div class='product-header'>{product_name} - {culture.upper()} - {action.upper()}</div>
    
    <div class='section-header'>📋 CONTEXTO E OBJETIVO</div>
    {context}
    
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
        <li><strong>Portal Mais Agro:</strong> Blog post + Webstories</li>
    </ul>
    
    <div class='section-header'>📞 CONTATOS E OBSERVAÇÕES</div>
    <ul>
        <li>Validar com especialista técnico</li>
        <li>Checar disponibilidade de imagens/vídeos</li>
        <li>Incluir CTA para portal Mais Agro</li>
        <li>Seguir guidelines de marca Syngenta</li>
        <li>Revisar compliance regulatório</li>
    </ul>
</div>
"""
    return briefing

# Interface principal
st.markdown("### 📝 Digite o conteúdo da célula do calendário")

# Container de input
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    content_input = st.text_area(
        "Conteúdo da célula:",
        placeholder="Ex: megafol - série - potencial máximo, todo o tempo",
        height=100,
        help="Cole aqui o conteúdo exato da célula do calendário do Sheets"
    )
    
    # Campos opcionais para ajuste
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data_input = st.date_input("Data prevista:", value=datetime.now())
    
    with col2:
        dia_semana = st.selectbox(
            "Dia da semana:",
            ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        )
    
    with col3:
        formato_principal = st.selectbox(
            "Formato principal:",
            ["Reels + capa", "Carrossel + stories", "Blog + redes", "Vídeo + stories", "Multiplataforma"]
        )
    
    generate_btn = st.button("🚀 Gerar Briefing", type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Processamento e exibição do briefing
if generate_btn and content_input:
    with st.spinner("Analisando conteúdo e gerando briefing..."):
        # Extrair informações do produto
        product, culture, action = extract_product_info(content_input)
        
        if product and product in PRODUCT_DESCRIPTIONS:
            # Gerar briefing completo
            briefing = generate_briefing(content_input, product, culture, action)
            
            # Exibir briefing
            st.markdown("## 📋 Briefing Gerado")
            st.markdown(briefing, unsafe_allow_html=True)
            
            # Botão de download
            st.download_button(
                label="📥 Baixar Briefing",
                data=briefing,
                file_name=f"briefing_{product}_{data_input.strftime('%Y%m%d')}.html",
                mime="text/html"
            )
            
            # Informações extras
            with st.expander("ℹ️ Informações Extraídas"):
                st.write(f"**Produto:** {product}")
                st.write(f"**Cultura:** {culture}")
                st.write(f"**Ação:** {action}")
                st.write(f"**Data:** {data_input.strftime('%d/%m/%Y')}")
                st.write(f"**Dia da semana:** {dia_semana}")
                st.write(f"**Formato principal:** {formato_principal}")
                st.write(f"**Descrição:** {PRODUCT_DESCRIPTIONS[product]}")
                
        elif product:
            st.warning(f"Produto '{product}' não encontrado no dicionário. Verifique a grafia.")
            st.info("Produtos disponíveis: " + ", ".join(list(PRODUCT_DESCRIPTIONS.keys())[:10]) + "...")
        else:
            st.error("Não foi possível identificar um produto no conteúdo. Tente formatos como:")
            st.code("""
            megafol - série - potencial máximo, todo o tempo
            verdavis - soja - depoimento produtor
            engeo pleno s - milho - controle percevejo
            miravis duo - algodão - reforço preventivo
            """)

# Seção de exemplos
with st.expander("📚 Exemplos de Conteúdo", expanded=True):
    st.markdown("""
    ### 🎯 Formatos Reconhecidos:
    
    **Padrão:** `PRODUTO - CULTURA - AÇÃO` ou `PRODUTO - AÇÃO`
    
    **Exemplos:**
    - `megafol - série - potencial máximo, todo o tempo`
    - `verdavis - milho - resultados do produto`
    - `engeo pleno s - soja - resultados GTEC`
    - `miravis duo - algodão - depoimento produtor`
    - `axial - trigo - reforço pós-emergente`
    - `manejo limpo - importância manejo antecipado`
    - `certano HF - a jornada de certano`
    - `elestal neo - soja - depoimento de produtor`
    - `fortenza - a jornada da semente mais forte - EP 01`
    - `reverb - vídeo conceito`
    """)

# Lista de produtos reconhecidos
with st.expander("📋 Produtos Reconhecidos"):
    col1, col2, col3 = st.columns(3)
    products = list(PRODUCT_DESCRIPTIONS.keys())
    
    with col1:
        for product in products[:10]:
            st.write(f"• {product}")
    
    with col2:
        for product in products[10:20]:
            st.write(f"• {product}")
    
    with col3:
        for product in products[20:]:
            st.write(f"• {product}")

# Rodapé
st.markdown("---")
st.caption("""
Ferramenta de geração automática de briefings - Padrão SYN 📋
Digite o conteúdo da célula do calendário para gerar briefings completos.
""")
