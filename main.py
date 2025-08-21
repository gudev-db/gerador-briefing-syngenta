import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
from typing import Tuple
import re

# Configuração inicial
st.set_page_config(
    page_title="Gerador de Briefings - SYN",
    page_icon="📋"
)

# Dicionário de descrições de produtos
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

def generate_briefing(content: str, product_name: str, culture: str, action: str, data_input: datetime, formato_principal: str) -> str:
    """Gera um briefing completo no formato SYN"""
    
    # Formatar data
    data_str = data_input.strftime("%d/%m")
    
    # Determinar mês em português
    meses = {
        1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL",
        5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
        9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
    }
    mes = meses[data_input.month]
    
    # Determinar categoria baseada na cultura
    if culture in ["soja", "milho", "algodão", "trigo", "cana", "café"]:
        categoria = culture.upper()
    elif culture in ["batata", "tomate", "melão", "uva"]:
        categoria = "HF"
    else:
        categoria = "MULTI"
    
    description = PRODUCT_DESCRIPTIONS.get(product_name, "Descrição do produto não disponível.")
    
    # Gerar briefing no formato correto
    briefing = f"""CALENDÁRIO DE PAUTAS - SYN

{mes} - {categoria}
{content.upper()}
Data prevista: {data_str}
Sugestão: {formato_principal}

{description}

Para essa pauta, a ser publicada na editoria {categoria}, vamos trabalhar com {product_name} na cultura do {culture}. O foco principal será {action}.

A ideia é desenvolver um conteúdo que {action} do produto, mostrando seus benefícios e diferenciais para o produtor.

Algumas fontes de informações:
- Portal Mais Agro: https://maisagro.syngenta.com.br
- Material técnico do produto
- Resultados de campo e depoimentos

Pontos de atenção:
- Manter tom técnico e informativo
- Evitar linguagem alarmista
- Incluir CTAs para o portal Mais Agro
- Seguir guidelines de marca Syngenta

Para as redes sociais, podemos trazer os principais benefícios do produto, convidando o público a saber mais no blog.
"""
    
    return briefing

# Interface principal
st.markdown("### 📝 Digite o conteúdo da célula do calendário")

content_input = st.text_area(
    "Conteúdo da célula:",
    placeholder="Ex: megafol - série - potencial máximo, todo o tempo",
    height=100,
    help="Cole aqui o conteúdo exato da célula do calendário do Sheets"
)

# Campos opcionais para ajuste
col1, col2 = st.columns(2)

with col1:
    data_input = st.date_input("Data prevista:", value=datetime.now())

with col2:
    formato_principal = st.selectbox(
        "Formato principal:",
        ["Reels + capa", "Carrossel + stories", "Blog + redes", "Vídeo + stories", "Multiplataforma"]
    )

generate_btn = st.button("🚀 Gerar Briefing", type="primary")

# Processamento e exibição do briefing
if generate_btn and content_input:
    with st.spinner("Analisando conteúdo e gerando briefing..."):
        # Extrair informações do produto
        product, culture, action = extract_product_info(content_input)
        
        if product and product in PRODUCT_DESCRIPTIONS:
            # Gerar briefing completo
            briefing = generate_briefing(content_input, product, culture, action, data_input, formato_principal)
            
            # Exibir briefing
            st.markdown("## 📋 Briefing Gerado")
            st.text_area("Briefing:", value=briefing, height=400)
            
            # Botão de download
            st.download_button(
                label="📥 Baixar Briefing",
                data=briefing,
                file_name=f"briefing_{product}_{data_input.strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
            
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
**Formatos Reconhecidos:**
- `PRODUTO - CULTURA - AÇÃO`
- `PRODUTO - AÇÃO`
- `PRODUTO - CULTURA - TIPO DE CONTEÚDO`

**Exemplos:**
- `megafol - série - potencial máximo, todo o tempo`
- `verdavis - milho - resultados do produto`
- `engeo pleno s - soja - resultados GTEC`
- `miravis duo - algodão - depoimento produtor`
- `axial - trigo - reforço pós-emergente`
- `manejo limpo - importância manejo antecipado`
- `certano HF - a jornada de certano`
""")

# Rodapé
st.markdown("---")
st.caption("Ferramenta de geração automática de briefings - Padrão SYN 📋")
