# app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import io
import os
import openai
from gtts import gTTS
from fpdf import FPDF
from fpdf import FPDF
import base64

# ---------- CONFIGURAÇÃO ----------
st.set_page_config(page_title="EVA — Assistente de Suporte (Vazamentos)", layout="wide", initial_sidebar_state="collapsed")

# OpenAI key: prefer env var, fallback para secrets
OPENAI_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else None
if not OPENAI_KEY:
    st.warning("⚠️ Defina OPENAI_API_KEY como variável de ambiente ou em Streamlit secrets para ativar o agente IA.")
else:
    openai.api_key = OPENAI_KEY

MODEL = "gpt-4o-mini"  # ajuste se necessário

# ---------- CONSTANTES / DADOS SIMULADOS FIXOS ----------
COMPANY = "Reply"
MACHINE = "A2203"
LAST_MAINT_DATE = "18/09/2025"
LAST_MAINT_DESC = "Substituição de junta e verificação de válvulas. Desgaste moderado em conexões."
DEFECT = "Vazamento na máquina (compartimento de pressão - lado direito)."
AUTHORIZED = "Sim"
TICKET = "TKT-092311"
TECHS = ["João R.", "Carla M.", "Renan O."]
PARTS = [
    {"part": "Válvula tipo B", "qty": 1},
    {"part": "Anel de vedação", "qty": 2},
    {"part": "Tubo conector", "qty": 1},
]

# ---------- FUNÇÕES ----------

@st.cache_data(show_spinner=False)
def gerar_simulacao_padrao():
    # retorna dataframe e resumo; sempre igual (seed fixa)
    np.random.seed(42)
    horas = 48
    agora = datetime.datetime.now()
    timestamps = [agora - datetime.timedelta(hours=i) for i in range(horas)][::-1]
    # dados fixos plausíveis para demonstração (sempre mesmo)
    base = np.array([3,3,2,2,3,4,5,6,6,8,7,6,5,6,7,8,10,12,11,9,7,6,5,4,3,3,2,2,3,4,4,6,7,8,7,6,5,5,6,7,8,9,7,6,5,4,3,3])
    ocorrencias = base[:horas].astype(int)
    df = pd.DataFrame({"timestamp": timestamps, "ocorrencias": ocorrencias})
    resumo = {
        "media": float(df.ocorrencias.mean()),
        "max": int(df.ocorrencias.max()),
        "hora_pico": df.loc[df.ocorrencias.idxmax(), "timestamp"].strftime("%H:%M"),
        "total": int(df.ocorrencias.sum())
    }
    return df, resumo

def gerar_grafico_bytes(df):
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(df["timestamp"], df["ocorrencias"], linewidth=2)
    ax.set_xlabel("")
    ax.set_ylabel("Ocorrências")
    ax.grid(True, linestyle="--", alpha=0.4)
    plt.xticks(rotation=30)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf

def gerar_audio_tts(texto):
    # gera mp3 em memória usando gTTS e retorna bytes
    try:
        tts = gTTS(text=texto, lang="pt-br")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Erro TTS: {e}")
        return None

from fpdf import FPDF


def gerar_pdf_report(resumo, chart_bytes):
    # Inicializa FPDF
    pdf = FPDF(orientation='P', unit='pt', format='A4')
    pdf.set_auto_page_break(auto=True, margin=40)
    pdf.add_page()
    
    # Define a cor de fundo (para contraste com texto em preto)
    pdf.set_fill_color(255, 255, 255) 

    # HEADER
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(6, 182, 212) # Cor azul para o título
    pdf.cell(0, 18, "Relatório Técnico - Monitoramento de Vazamentos", ln=True)
    pdf.ln(4)

    # Detalhes do Relatório
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(0, 0, 0) # Cor preta para o texto do corpo
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(0, 14, f"Empresa: {COMPANY}", ln=True)
    pdf.cell(0, 14, f"Data/Hora: {now}", ln=True)
    pdf.cell(0, 14, f"Máquina: {MACHINE}", ln=True)
    pdf.ln(6)

    # Detalhes da máquina (caixa com cor de fundo)
    pdf.set_fill_color(230, 230, 230) # Cor cinza claro para o fundo da caixa
    pdf.set_draw_color(80, 80, 80)
    # Ajustei a altura do retângulo para cobrir o texto
    pdf.rect(36, pdf.get_y(), 520, 48, style='FD') # 'FD' para Fill and Draw
    # Ajustei o posicionamento do texto na caixa
    pdf.set_xy(40, pdf.get_y() + 4)
    pdf.set_font("Helvetica", size=10)
    # Usando multi_cell para garantir que o texto caiba
    pdf.multi_cell(520, 12, f"Detalhes da máquina: Máquina com mais de 15 anos de uso. Última manutenção: {LAST_MAINT_DATE}. {LAST_MAINT_DESC}")

    pdf.ln(6) # Espaçamento após a caixa
    # Reajusta o Y (precisa ser manual após multi_cell e rect)
    pdf.set_y(pdf.get_y() + 20)
    
    # Corpo principal do relatório
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, f"Defeito: {DEFECT}", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 12, f"Autorizado para manutenção: {AUTHORIZED}", ln=True)
    pdf.ln(6)

    # Passos para verificação e reparo
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, "Passos para verificação e reparo:", ln=True)
    pdf.set_font("Helvetica", size=10)
    passos = [
        "1. Garantir segurança: isolar e sinalizar a área.",
        "2. Despressurizar o compartimento e desligar a máquina.",
        "3. Remover tampa lateral e inspecionar juntas e válvulas.",
        "4. Substituir anéis de vedação e a válvula defeituosa, se identificada.",
        "5. Reapertar conexões, recolocar tampa e realizar teste com baixa pressão.",
        "6. Registrar resultado e reabrir produção quando seguro."
    ]
    for p in passos:
        pdf.multi_cell(0, 12, p)
    pdf.ln(6)

    # Peças previstas
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, "IPIs necessários / Peças previstas:", ln=True)
    pdf.set_font("Helvetica", size=10)
    for p in PARTS:
        pdf.cell(0, 12, f"- {p['part']} — Qtd: {p['qty']}", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, f"Ticket de suporte: #{TICKET}", ln=True)
    pdf.cell(0, 14, f"Técnicos responsáveis: {', '.join(TECHS)}", ln=True)

    # ---------- página do gráfico ----------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(6, 182, 212) # Cor azul para o título do gráfico
    pdf.cell(0, 16, "Gráfico de Ocorrências (últimas 48h)", ln=True)

    # **********************************************
    # CORREÇÃO CRÍTICA PARA BytesIO COM FPDF
    # chart_bytes precisa estar no início do stream ANTES de pdf.image()
    chart_bytes.seek(0) 
    # Passamos o BytesIO diretamente.
    pdf.image(chart_bytes, x=36, y=60, w=520, type='PNG')
    # **********************************************

    # Retornar PDF como BytesIO
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output
    
    # Peças previstas
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, "IPIs necessários / Peças previstas:", ln=True)
    pdf.set_font("Helvetica", size=10)
    for p in PARTS:
        pdf.cell(0, 12, f"- {p['part']} — Qtd: {p['qty']}", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, f"Ticket de suporte: #{TICKET}", ln=True)
    pdf.cell(0, 14, f"Técnicos responsáveis: {', '.join(TECHS)}", ln=True)

    # ---------- página do gráfico ----------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(6, 182, 212) # Cor azul para o título do gráfico
    pdf.cell(0, 16, "Gráfico de Ocorrências (últimas 48h)", ln=True)

    # Inserir gráfico direto do BytesIO (o fpdf aceita)
    # chart_bytes precisa estar no início do stream
    chart_bytes.seek(0) 
    pdf.image(chart_bytes, x=36, y=60, w=520, type='PNG')

    # Retornar PDF como BytesIO
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

    # Peças previstas
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, "IPIs necessários / Peças previstas:", ln=True)
    pdf.set_font("Helvetica", size=10)
    for p in PARTS:
        pdf.cell(0, 12, f"- {p['part']} — Qtd: {p['qty']}", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, f"Ticket de suporte: #{TICKET}", ln=True)
    pdf.cell(0, 14, f"Técnicos responsáveis: {', '.join(TECHS)}", ln=True)

    # ---------- página do gráfico ----------
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(6, 182, 212)
    pdf.cell(0, 16, "Gráfico de Ocorrências (últimas 48h)", ln=True)

    # Inserir gráfico direto do BytesIO
    pdf.image(chart_bytes, x=36, y=60, w=520, type='PNG')

    # Retornar PDF como BytesIO
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output


    # detalhes da máquina (caixa)
    pdf.set_fill_color(18,24,29)
    pdf.set_draw_color(80,80,80)
    pdf.rect(36, pdf.get_y(), 520, 72, style='F')
    pdf.set_xy(40, pdf.get_y() + 6)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(520, 14, f"Detalhes da máquina: Máquina com mais de 15 anos de uso. Última manutenção: {LAST_MAINT_DATE}. {LAST_MAINT_DESC}")

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, f"Defeito: {DEFECT}", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 12, f"Autorizado para manutenção: {AUTHORIZED}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, "Passos para verificação e reparo:", ln=True)
    pdf.set_font("Helvetica", size=10)
    passos = [
        "1. Garantir segurança: isolar e sinalizar a área.",
        "2. Despressurizar o compartimento e desligar a máquina.",
        "3. Remover tampa lateral e inspecionar juntas e válvulas.",
        "4. Substituir anéis de vedação e a válvula defeituosa, se identificada.",
        "5. Reapertar conexões, recolocar tampa e realizar teste com baixa pressão.",
        "6. Registrar resultado e reabrir produção quando seguro."
    ]
    for p in passos:
        pdf.multi_cell(0, 12, p)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, "IPIs necessários / Peças previstas:", ln=True)
    pdf.set_font("Helvetica", size=10)
    for p in PARTS:
        pdf.cell(0, 12, f"- {p['part']} — Qtd: {p['qty']}", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 14, f"Ticket de suporte: #{TICKET}", ln=True)
    pdf.cell(0, 14, f"Técnicos responsáveis: {', '.join(TECHS)}", ln=True)

    # adicionar página com gráfico
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(6,182,212)
    pdf.cell(0, 16, "Gráfico de Ocorrências (últimas 48h)", ln=True)
    # inserir imagem do gráfico (chart_bytes)
    pdf.image(chart_bytes, x=36, y=60, w=520)
    # voltar bytes
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

def call_openai_agent(user_text, resumo):
    # chama o OpenAI ChatCompletion (chat-based)
    if not OPENAI_KEY:
        return "[Agente IA não configurado - configure OPENAI_API_KEY]"
    system_prompt = f"""
Você é EVA, assistente técnico especializado em vazamentos industriais.
Contexto (simulado, fornecido): média de ocorrências = {resumo['media']} por hora; pico = {resumo['max']} às {resumo['hora_pico']}; total = {resumo['total']}.
Seja objetivo, forneça passos de contenção, verificação e recomendações de segurança. Não mencione que os dados são simulados.
Responda em português claro, dividido por passos quando apropriado.
"""
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            max_tokens=500,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Erro ao chamar OpenAI: {e}]"

# ---------- LAYOUT ----------
st.markdown(
    """
    <style>
    .reportview-container {background: linear-gradient(180deg,#040609 0%, #071017 100%);}
    .stButton>button {background: #06b6d4;color:#021018;border-radius:8px;padding:8px 12px}
    .stDownloadButton>button {background:#10b981;color:#021018;border-radius:8px;padding:8px 12px}
    </style>
    """, unsafe_allow_html=True
)

# Header
col1, col2 = st.columns([3,1])
with col1:
    st.markdown(f"## <span style='color:#06b6d4'>EVA</span> — Assistente de Suporte (Vazamentos)", unsafe_allow_html=True)
    st.write("Sistema de monitoramento industrial — demonstração. Ao clicar em **Gerar Relatório**, você fará download de um PDF com os dados apresentados.")
with col2:
    st.markdown(f"**Máquina:** {MACHINE}")
    st.markdown(f"**Ticket:** {TICKET}")

# main content: gráfico + resumo
df, resumo = gerar_simulacao_padrao()
chart_buf = gerar_grafico_bytes(df)

left, right = st.columns([3,1])


# main content: gráfico + resumo
df, resumo = gerar_simulacao_padrao()
chart_buf = gerar_grafico_bytes(df)

left, right = st.columns([3,1])

with left:
    st.markdown("### Ocorrências de Falhas — últimas 48 horas")
    # O Streamlit.image consome o buffer, mas o reuso do buffer 
    # para a próxima chamada (get_pdf_buffer) deve estar protegido
    st.image(chart_buf, use_column_width=True) 
    st.markdown(f"**Resumo:** Média = {resumo['media']} | Pico = {resumo['max']} às {resumo['hora_pico']} | Total = {resumo['total']}")
    
    @st.cache_data
    def get_pdf_buffer(resumo, chart_buf_initial):
        # Clonar o buffer para evitar que o fpdf/Streamlit o consuma 
        # antes que o outro possa usá-lo.
        # Criamos uma cópia que está no início.
        chart_buf_copy = io.BytesIO(chart_buf_initial.getvalue())
        chart_buf_copy.seek(0)
        return gerar_pdf_report(resumo, chart_buf_copy)
    
    # Garante que o buffer inicial do gráfico está no início para a clonagem/leitura
    chart_buf.seek(0)
    pdf_buf = get_pdf_buffer(resumo, chart_buf) # Passamos o buffer original

    # 2. Renderizar botões (o download_button fica visível sempre, usando o buffer gerado)
    col_a, col_b, col_c = st.columns([1,1,1])
    # ... (Botões de Ouvir e Baixar PDF/PNG permanecem como na sua última versão)
with col_a:
        # ... (Botão Ouvir)
    
with col_b:
        # st.download_button aceita um BytesIO como 'data'
        st.download_button(
            "⬇️ Baixar Relatório (PDF)", 
            data=pdf_buf, 
            file_name=f"Relatorio_{MACHINE}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
            mime="application/pdf"
        )

with col_c:
        if st.button("Exportar gráfico (PNG)"):
            # O gráfico deve ser lido do início
            chart_buf.seek(0)
            st.download_button("⬇️ Baixar PNG", data=chart_buf, file_name=f"ocorrencias_{MACHINE}.png", mime="image/png")
# ...

with right:
    st.markdown("### Conversa com EVA")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    # show chat
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            st.markdown(f"**Você:** {entry['text']}")
        else:
            st.markdown(f"**EVA:** {entry['text']}")
    user_input = st.text_input("Digite sua pergunta para EVA", key="user_prompt")
    send = st.button("Enviar para EVA")
    clear = st.button("Limpar conversa")
    if clear:
        st.session_state.chat_history = []
        st.experimental_rerun()
    if send and user_input:
        # append user
        st.session_state.chat_history.append({"role":"user","text":user_input})
        # call OpenAI agent
        with st.spinner("EVA está analisando..."):
            resposta = call_openai_agent(user_input, resumo)
        st.session_state.chat_history.append({"role":"assistant","text":resposta})
        # auto-play TTS: generate and show audio player
        audio_buf = gerar_audio_tts(resposta)
        # refresh
        st.experimental_rerun()

# footer info: machine details / technicians / parts (boxes)
st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Detalhes da Máquina**")
    st.write(f"Máquina: **{MACHINE}**")
    st.write(f"Última manutenção: **{LAST_MAINT_DATE}**")
    st.write(LAST_MAINT_DESC)
with c2:
    st.markdown("**Técnicos designados**")
    for t in TECHS:
        st.write(f"- {t}")
with c3:
    st.markdown("**Peças previstas**")
    for p in PARTS:
        st.write(f"- {p['part']} — Qtd: {p['qty']}")

st.markdown("**Nota:** Esta é uma demonstração com dados simulados. O agente IA usa o contexto mostrado para orientar a investigação técnica.")
