import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, List, Tuple
import re
import numpy as np

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
    .calendar-cell {
        background-color: #e3f2fd;
        padding: 8px;
        border-radius: 4px;
        margin: 2px;
        font-size: 0.9em;
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

# Funções para processar o CSV específico
def process_syn_calendar(df: pd.DataFrame) -> List[Tuple[datetime, str, str]]:
    """Processa o formato específico do calendário SYN"""
    events = []
    
    # Encontrar o mês e ano
    month_year = None
    for idx, row in df.iterrows():
        for col in df.columns:
            if "MAIO" in str(row[col]) and "2025" in str(row[col]):
                month_year = "05/2025"
                break
    
    # Mapear dias da semana para colunas
    day_columns = {}
    for idx, row in df.iterrows():
        if "DOMINGO" in str(row.iloc[0]):
            # Esta linha contém os dias da semana
            for i, cell in enumerate(row):
                if pd.notna(cell) and any(day in str(cell).upper() for day in ["DOMINGO", "SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO"]):
                    day_columns[i] = str(cell).strip()
            break
    
    # Processar eventos
    for idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            if pd.notna(cell) and col_idx in day_columns and col_idx > 0:
                content = str(cell).strip()
                if content and not any(x in content for x in ["🔵", "🟠", "🟢", "🔴", "🟣", "🔃", "📲", "Anotações"]):
                    # Tentar extrair a data
                    try:
                        day_num = None
                        # Verificar se há número de dia nesta célula ou anterior
                        for check_idx in [col_idx - 1, col_idx]:
                            if check_idx < len(row) and pd.notna(row.iloc[check_idx]):
                                try:
                                    day_num = int(str(row.iloc[check_idx]).strip())
                                    break
                                except ValueError:
                                    continue
                        
                        if day_num:
                            date_str = f"{day_num:02d}/{month_year}"
                            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                            events.append((date_obj, content, day_columns[col_idx]))
                    except:
                        continue
    
    return events

def extract_product_info(text: str) -> Tuple[str, str, str]:
    """Extrai informações do produto do texto da célula"""
    if pd.isna(text) or not text.strip():
        return None, None, None
    
    text = str(text).strip()
    
    # Remover emojis e marcadores
    clean_text = re.sub(r'[🔵🟠🟢🔴🟣🔃📲]', '', text).strip()
    
    # Padrões para extração
    patterns = {
        'product': r'\b([A-Z][A-Z\s]+(?:PRO|S|NEO|LLI|ELITE|COMPLETO|DUO|FLEXI)?)\b',
        'culture': r'\b(soja|milho|algodão|cana|trigo|HF|café|citrus|batata|multi)\b',
        'action': r'\b(depoimento|resultados|série|reforço|controle|lançamento|importância|jornada|conceito|vídeo|ação|diferenciais)\b'
    }
    
    product_match = re.search(patterns['product'], clean_text, re.IGNORECASE)
    culture_match = re.search(patterns['culture'], clean_text, re.IGNORECASE)
    action_match = re.search(patterns['action'], clean_text, re.IGNORECASE)
    
    product = product_match.group(1).strip().upper() if product_match else None
    culture = culture_match.group(0).lower() if culture_match else "multi"
    action = action_match.group(0).lower() if action_match else "awareness"
    
    return product, culture, action

def generate_context(date, content, day_of_week, product_name, culture, action):
    """Gera o texto de contexto baseado nas informações"""
    date_str = date.strftime("%d/%m/%Y") if hasattr(date, 'strftime') else "Data não especificada"
    
    context = f"""
**{product_name} - {culture.upper()} - {action.upper()}**
Data prevista: {date_str} ({day_of_week})
Conteúdo: {content}

Para essa pauta, vamos trabalhar com {product_name} na cultura do {culture}. O foco principal será {action}.
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

def generate_briefing(date, content, day_of_week, product_name, culture, action):
    """Gera um briefing completo"""
    description = PRODUCT_DESCRIPTIONS.get(product_name, "Descrição do produto não disponível.")
    context = generate_context(date, content, day_of_week, product_name, culture, action)
    platform_strategy = generate_platform_strategy(product_name, culture, action, content)
    
    briefing = f"""
<div class='briefing-card'>
    <div class='product-header'>{product_name} - {culture.upper()} - {action.upper()}</div>
    
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
uploaded_file = st.file_uploader(
    "📤 Faça upload do cronograma do Sheets (CSV)",
    type=['csv'],
    help="O arquivo deve seguir o formato do calendário SYN com matriz de conteúdo"
)

if uploaded_file:
    try:
        # Ler o CSV mantendo todas as colunas e linhas
        df = pd.read_csv(uploaded_file, header=None)
        
        st.success(f"✅ Arquivo carregado com {len(df)} linhas e {len(df.columns)} colunas")
        
        # Mostrar preview do arquivo
        with st.expander("📊 Visualização do Arquivo Carregado"):
            st.dataframe(df.head(10))
        
        # Processar eventos do calendário
        events = process_syn_calendar(df)
        
        if events:
            st.success(f"🎯 {len(events)} eventos identificados no calendário")
            
            # Exibir eventos encontrados
            with st.expander("📅 Eventos Identificados", expanded=True):
                for date, content, day in events:
                    st.markdown(f"<div class='calendar-cell'>{date.strftime('%d/%m')} ({day}): {content}</div>", 
                               unsafe_allow_html=True)
            
            # Processar briefings
            briefings = []
            for date, content, day in events:
                product, culture, action = extract_product_info(content)
                
                if product and product in PRODUCT_DESCRIPTIONS:
                    briefing = generate_briefing(date, content, day, product, culture, action)
                    briefings.append((date, product, content, briefing))
            
            # Exibir briefings
            if briefings:
                st.markdown(f"## 📋 Briefings Gerados ({len(briefings)})")
                
                for date, product, content, briefing in briefings:
                    with st.expander(f"{date.strftime('%d/%m')} - {product} - {content[:50]}...", expanded=True):
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
                all_briefings = "\n\n".join([f"# Briefing {product} - {date.strftime('%d/%m/%Y')}\n{briefing}" 
                                           for date, product, content, briefing in briefings])
                
                st.download_button(
                    label="📦 Baixar Todos os Briefings",
                    data=all_briefings,
                    file_name="todos_briefings_syn.html",
                    mime="text/html"
                )
            else:
                st.warning("Nenhum produto reconhecido encontrado nos eventos.")
                
        else:
            st.warning("Não foi possível identificar eventos no calendário. Verifique o formato do arquivo.")
            
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
        st.info("Certifique-se de que o arquivo segue o formato padrão do calendário SYN")

else:
    # Exemplo de estrutura esperada
    st.markdown("""
    ### 📝 Formato Esperado do CSV:
    
    O arquivo deve seguir exatamente o formato do calendário SYN:
    
    | | | CX | herbicidas | seedcare | fungicidas | inseticidas | biológicos | culturas |
    |---|---|---|---|---|---|---|---|---|
    | | | CALENDÁRIO DE PAUTAS | | | | MAIO | | 2025 |
    | | | 🔵- dia a dia do campo | 🟠- inov e tendências | 🟢- sustentabilidade | 🔴- mercado e safra | 🟣 - especialistas | 🔃 webstories | 📲 UGC |
    | | | DOMINGO | SEGUNDA | TERÇA | QUARTA | QUINTA | SEXTA | SÁBADO |
    | | | | | | | 1 | 2 | 3 |
    | | | | | | | fortenza - a jornada... | 📲 alade - depoimento... | |
    | | | | | | | | verdavis - milho... | |
    
    ### 🎯 Produtos Reconhecidos:
    """
    )
    
    # Lista de produtos reconhecidos
    col1, col2, col3 = st.columns(3)
    products = list(PRODUCT_DESCRIPTIONS.keys())
    
    with col1:
        for product in products[:8]:
            st.write(f"• {product}")
    
    with col2:
        for product in products[8:16]:
            st.write(f"• {product}")
    
    with col3:
        for product in products[16:]:
            st.write(f"• {product}")

# Rodapé
st.markdown("---")
st.caption("""
Ferramenta de geração automática de briefings - Padrão SYN 📋
Desenvolvido para processar calendários do Sheets e gerar briefings completos.
""")
