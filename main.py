import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, List, Tuple
import re
import io

# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Gerador de Briefings - SYN",
    page_icon="📋"
)

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
    "FORTENZA ELITE": "Oferta comercial de TSI. Solução robusta contre pragas, doenças e nematoides do Cerrado.",
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
st.title("Gerador de Briefings - SYN")
st.markdown("Digite o conteúdo da célula do calendário para gerar um briefing completo no padrão SYN.")

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

def generate_context(content, product_name, culture, action, data_input, formato_principal):
    """Gera o texto de contexto discursivo usando LLM"""
    if not gemini_api_key:
        return "API key do Gemini não configurada. Contexto não disponível."
    
    # Determinar mês em português
    meses = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    mes = meses[data_input.month]
    
    prompt = f"""
    Como redator especializado em agronegócio da Syngenta, elabore um texto contextual discursivo de 3-4 parágrafos para uma pauta de conteúdo.

    Informações da pauta:
    - Produto: {product_name}
    - Cultura: {culture}
    - Ação/tema: {action}
    - Mês de publicação: {mes}
    - Formato principal: {formato_principal}
    - Conteúdo original: {content}

    Descrição do produto: {PRODUCT_DESCRIPTIONS.get(product_name, 'Produto agrícola Syngenta')}

    Instruções:
    - Escreva em formato discursivo e fluido, com 3-4 parágrafos bem estruturados
    - Mantenha tom técnico mas acessível, adequado para produtores rurais
    - Contextualize a importância do tema para a cultura e época do ano
    - Explique por que este conteúdo é relevante neste momento
    - Inclua considerações sobre o público-alvo e objetivos da comunicação
    - Não repita literalmente a descrição do produto, mas a incorpore naturalmente no texto
    - Use linguagem persuasiva mas factual, baseada em dados técnicos

    Formato: Texto corrido em português brasileiro
    """
    
    try:
        response = modelo_texto.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao gerar contexto: {str(e)}"

def generate_platform_strategy(product_name, culture, action, content):
    """Gera estratégia por plataforma usando Gemini"""
    if not gemini_api_key:
        return "API key do Gemini não configurada. Estratégias por plataforma não disponíveis."
    
    prompt = f"""
    Como especialista em mídias sociais para o agronegócio Syngenta, crie uma estratégia de conteúdo detalhada:

    PRODUTO: {product_name}
    CULTURA: {culture}
    AÇÃO: {action}
    CONTEÚDO ORIGINAL: {content}
    DESCRIÇÃO DO PRODUTO: {PRODUCT_DESCRIPTIONS.get(product_name, 'Produto agrícola Syngenta')}

    FORNECER ESTRATÉGIA PARA:
    - Instagram (Feed, Reels, Stories)
    - Facebook 
    - LinkedIn
    - WhatsApp Business
    - YouTube
    - Portal Mais Agro (blog)

    INCLUIR PARA CADA PLATAFORMA:
    1. Tipo de conteúdo recomendado
    2. Formato ideal (vídeo, carrossel, estático, etc.)
    3. Tom de voz apropriado
    4. CTA específico
    5. Melhores práticas

    Formato: Texto claro com seções bem definidas
    """
    
    try:
        response = modelo_texto.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro ao gerar estratégia: {str(e)}"

def generate_briefing(content, product_name, culture, action, data_input, formato_principal):
    """Gera um briefing completo em formato de texto puro"""
    description = PRODUCT_DESCRIPTIONS.get(product_name, "Descrição do produto não disponível.")
    context = generate_context(content, product_name, culture, action, data_input, formato_principal)
    platform_strategy = generate_platform_strategy(product_name, culture, action, content)
    
    briefing = f"""
BRIEFING DE CONTEÚDO - {product_name} - {culture.upper()} - {action.upper()}

CONTEXTO E OBJETIVO
{context}

DESCRIÇÃO DO PRODUTO
{description}

ESTRATÉGIA POR PLATAFORMA
{platform_strategy}

FORMATOS SUGERIDOS
- Instagram: Reels + Stories + Feed post
- Facebook: Carrossel + Link post
- LinkedIn: Artigo + Post informativo
- WhatsApp: Card informativo + Link
- YouTube: Shorts + Vídeo explicativo
- Portal Mais Agro: Blog post + Webstories

CONTATOS E OBSERVAÇÕES
- Validar com especialista técnico
- Checar disponibilidade de imagens/vídeos
- Incluir CTA para portal Mais Agro
- Seguir guidelines de marca Syngenta
- Revisar compliance regulatório

DATA PREVISTA: {data_input.strftime('%d/%m/%Y')}
DIA DA SEMANA: {dia_semana}
FORMATO PRINCIPAL: {formato_principal}
"""
    return briefing

# Interface principal
st.markdown("### Opções de Geração")

# Abas para diferentes modos de operação
tab1, tab2 = st.tabs(["Briefing Individual", "Processamento em Lote (CSV)"])

with tab1:
    st.markdown("### Digite o conteúdo da célula do calendário")

    content_input = st.text_area(
        "Conteúdo da célula:",
        placeholder="Ex: megafol - série - potencial máximo, todo o tempo",
        height=100,
        help="Cole aqui o conteúdo exato da célula do calendário do Sheets",
        key="individual_content"
    )

    # Campos opcionais para ajuste
    col1, col2, col3 = st.columns(3)

    with col1:
        data_input = st.date_input("Data prevista:", value=datetime.now(), key="individual_date")

    with col2:
        dia_semana = st.selectbox(
            "Dia da semana:",
            ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"],
            key="individual_day"
        )

    with col3:
        formato_principal = st.selectbox(
            "Formato principal:",
            ["Reels + capa", "Carrossel + stories", "Blog + redes", "Vídeo + stories", "Multiplataforma"],
            key="individual_format"
        )

    generate_btn = st.button("Gerar Briefing Individual", type="primary", key="individual_btn")

    # Processamento e exibição do briefing individual
    if generate_btn and content_input:
        with st.spinner("Analisando conteúdo e gerando briefing..."):
            # Extrair informações do produto
            product, culture, action = extract_product_info(content_input)
            
            if product and product in PRODUCT_DESCRIPTIONS:
                # Gerar briefing completo
                briefing = generate_briefing(content_input, product, culture, action, data_input, formato_principal)
                
                # Exibir briefing
                st.markdown("## Briefing Gerado")
                st.text(briefing)
                
                # Botão de download
                st.download_button(
                    label="Baixar Briefing",
                    data=briefing,
                    file_name=f"briefing_{product}_{data_input.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    key="individual_download"
                )
                
                # Informações extras
                with st.expander("Informações Extraídas"):
                    st.write(f"Produto: {product}")
                    st.write(f"Cultura: {culture}")
                    st.write(f"Ação: {action}")
                    st.write(f"Data: {data_input.strftime('%d/%m/%Y')}")
                    st.write(f"Dia da semana: {dia_semana}")
                    st.write(f"Formato principal: {formato_principal}")
                    st.write(f"Descrição: {PRODUCT_DESCRIPTIONS[product]}")
                    
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

with tab2:
    st.markdown("### Processamento em Lote via CSV")
    
    st.info("""
    Faça upload de um arquivo CSV exportado do Google Sheets.
    O sistema irá processar cada linha a partir da segunda linha (ignorando cabeçalhos)
    e gerar briefings apenas para as linhas que contêm produtos reconhecidos.
    """)
    
    uploaded_file = st.file_uploader(
        "Escolha o arquivo CSV", 
        type=['csv'],
        help="Selecione o arquivo CSV exportado do Google Sheets"
    )
    
    if uploaded_file is not None:
        try:
            # Ler o CSV
            df = pd.read_csv(uploaded_file)
            st.success(f"CSV carregado com sucesso! {len(df)} linhas encontradas.")
            
            # Mostrar prévia do arquivo
            with st.expander("Visualizar primeiras linhas do CSV"):
                st.dataframe(df.head())
            
            # Configurações para processamento em lote
            st.markdown("### Configurações do Processamento em Lote")
            col1, col2 = st.columns(2)
            
            with col1:
                data_padrao = st.date_input(
                    "Data padrão para todos os briefings:",
                    value=datetime.now(),
                    key="batch_date"
                )
            
            with col2:
                formato_padrao = st.selectbox(
                    "Formato principal padrão:",
                    ["Reels + capa", "Carrossel + stories", "Blog + redes", "Vídeo + stories", "Multiplataforma"],
                    key="batch_format"
                )
            
            # Identificar coluna com conteúdo
            colunas = df.columns.tolist()
            coluna_conteudo = st.selectbox(
                "Selecione a coluna que contém o conteúdo das células:",
                colunas,
                help="Selecione a coluna que contém os textos das células do calendário"
            )
            
            processar_lote = st.button("Processar CSV e Gerar Briefings", type="primary", key="batch_btn")
            
            if processar_lote:
                briefings_gerados = []
                linhas_processadas = 0
                linhas_com_produto = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for index, row in df.iterrows():
                    linhas_processadas += 1
                    progress_bar.progress(linhas_processadas / len(df))
                    status_text.text(f"Processando linha {linhas_processadas} de {len(df)}...")
                    
                    # Pular a primeira linha (cabeçalhos)
                    if index == 0:
                        continue
                    
                    # Obter conteúdo da célula
                    content = str(row[coluna_conteudo]) if pd.notna(row[coluna_conteudo]) else ""
                    
                    if content:
                        # Extrair informações do produto
                        product, culture, action = extract_product_info(content)
                        
                        if product and product in PRODUCT_DESCRIPTIONS:
                            linhas_com_produto += 1
                            # Gerar briefing
                            briefing = generate_briefing(
                                content, 
                                product, 
                                culture, 
                                action, 
                                data_padrao, 
                                formato_padrao
                            )
                            
                            briefings_gerados.append({
                                'linha': index + 1,
                                'produto': product,
                                'conteudo': content,
                                'briefing': briefing,
                                'arquivo': f"briefing_{product}_{index+1}.txt"
                            })
                
                progress_bar.empty()
                status_text.empty()
                
                # Resultados do processamento
                st.success(f"Processamento concluído! {linhas_com_produto} briefings gerados de {linhas_processadas-1} linhas processadas.")
                
                if briefings_gerados:
                    # Exibir resumo
                    st.markdown("### Briefings Gerados")
                    resumo_df = pd.DataFrame([{
                        'Linha': b['linha'],
                        'Produto': b['produto'],
                        'Conteúdo': b['conteudo'][:50] + '...' if len(b['conteudo']) > 50 else b['conteudo']
                    } for b in briefings_gerados])
                    
                    st.dataframe(resumo_df)
                    
                    # Criar arquivo ZIP com todos os briefings
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for briefing_info in briefings_gerados:
                            zip_file.writestr(
                                briefing_info['arquivo'], 
                                briefing_info['briefing']
                            )
                    
                    zip_buffer.seek(0)
                    
                    # Botão para download do ZIP
                    st.download_button(
                        label="📥 Baixar Todos os Briefings (ZIP)",
                        data=zip_buffer,
                        file_name="briefings_syngenta.zip",
                        mime="application/zip",
                        key="batch_download_zip"
                    )
                    
                    # Também permitir download individual
                    st.markdown("---")
                    st.markdown("### Download Individual")
                    
                    for briefing_info in briefings_gerados:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"Linha {briefing_info['linha']}: {briefing_info['produto']} - {briefing_info['conteudo'][:30]}...")
                        with col2:
                            st.download_button(
                                label="📄 Baixar",
                                data=briefing_info['briefing'],
                                file_name=briefing_info['arquivo'],
                                mime="text/plain",
                                key=f"download_{briefing_info['linha']}"
                            )
                else:
                    st.warning("Nenhum briefing foi gerado. Verifique se o CSV contém produtos reconhecidos.")
                    st.info("Produtos reconhecidos: " + ", ".join(list(PRODUCT_DESCRIPTIONS.keys())[:15]) + "...")
                    
        except Exception as e:
            st.error(f"Erro ao processar o arquivo CSV: {str(e)}")

# Seção de exemplos
with st.expander("Exemplos de Conteúdo", expanded=True):
    st.markdown("""
    Formatos Reconhecidos:

    Padrão: PRODUTO - CULTURA - AÇÃO ou PRODUTO - AÇÃO

    Exemplos:
    - megafol - série - potencial máximo, todo o tempo
    - verdavis - milho - resultados do produto
    - engeo pleno s - soja - resultados GTEC
    - miravis duo - algodão - depoimento produtor
    - axial - trigo - reforço pós-emergente
    - manejo limpo - importância manejo antecipado
    - certano HF - a jornada de certano
    - elestal neo - soja - depoimento de produtor
    - fortenza - a jornada da semente mais forte - EP 01
    - reverb - vídeo conceito
    """)

# Lista de produtos reconhecidos
with st.expander("Produtos Reconhecidos"):
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
st.caption("Ferramenta de geração automática de briefings - Padrão SYN. Digite o conteúdo da célula do calendário para gerar briefings completos.")
