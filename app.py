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
import base64

# ---------- CONFIGURAÇÃO ----------
# 1. Ajuste de layout e FORÇAR TEMA ESCURO (dark)
st.set_page_config(page_title="EVA — Assistente de Suporte (Vazamentos)", layout="wide", initial_sidebar_state="collapsed", theme="dark")

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
    # Ajuste para tema escuro: cores claras para elementos do gráfico
    fig, ax = plt.subplots(figsize=(9, 3), facecolor="#071017") # fundo do Streamlit
    ax.plot(df["timestamp"], df["ocorrencias"], linewidth=2, color="#06b6d4") # Cor da linha
    ax.set_xlabel("", color="white")
    ax.set_ylabel("Ocorrências", color="white")
    ax.tick_params(axis='x', colors='white') # Cor dos ticks X
    ax.tick_params(axis='y', colors='white') # Cor dos ticks Y
    ax.spines['left'].set_color('white') # Cor da borda Y
    ax.spines['bottom'].set_color('white') # Cor da borda X
    ax.spines['top'].set_color('#071017') # Esconde borda superior
    ax.spines['right'].set_color('#071017') # Esconde borda direita
    ax.set_facecolor("#071017") # Fundo da área de plotagem
    ax.grid(True, linestyle="--", alpha=0.4, color="#555")
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

def gerar_pdf_report(resumo, chart_bytes):
    # usa FPDF para montar PDF e retorna bytes
    # Mantive as cores do PDF focadas no esquema de cores da aplicação
    pdf = FPDF(orientation='P', unit='pt', format='A4')
    pdf.set_auto_page_break(auto=True, margin=40)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(6, 182, 212) # Cor de destaque (ciano)
    pdf.cell(0, 18, "Relatório Técnico - Monitoramento de Vazamentos", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", size=10)
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.set_text_color(230,230,230) # Cor de texto geral (claro)

    # ... (o restante da função gerar_pdf_report é mantido como estava, pois as cores já foram ajustadas no código original para tons de cinza/claro no PDF, o que é um bom contraste para impressão) ...
    
    pdf.cell(0, 14, f"Empresa: {COMPANY}", ln=True)
    pdf.cell(0, 14, f"Data/Hora: {now}", ln=True)
    pdf.cell(0, 14, f"Máquina: {MACHINE}", ln=True)
    pdf.ln(6)

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
    # chart_bytes must be reset to the beginning
    chart_bytes.seek(0)
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
    /* 2. CSS para tema escuro */
    .stApp {
        background: linear-gradient(180deg, #071017 0%, #040609 100%); /* Fundo escuro */
        color: white; /* Cor do texto padrão */
    }
    /* Estilo para botões */
    .stButton>button {
        background: #06b6d4;
        color: #021018;
        border-radius: 8px;
        padding: 8px 12px;
        border: none;
    }
    .stDownloadButton>button {
        background: #10b981;
        color: #021018;
        border-radius: 8px;
        padding: 8px 12px;
        border: none;
    }
    /* Estilo para a caixa de chat */
    .chat-container {
        height: 400px; /* Altura fixa para histórico */
        overflow-y: auto; /* Scroll se o conteúdo for muito grande */
        background-color: #1a1a2e; /* Fundo do chat */
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .chat-user {
        background-color: #3f3f6e; /* Cor da fala do usuário */
        padding: 5px 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        text-align: right;
    }
    .chat-eva {
        background-color: #06b6d420; /* Cor da fala do EVA */
        padding: 5px 10px;
        border-radius: 10px;
        margin-bottom: 5px;
        text-align: left;
    }
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

# main content: gráfico + resumo + chat
df, resumo = gerar_simulacao_padrao()
chart_buf = gerar_grafico_bytes(df)

# 3. Alteração da proporção: [1, 2] -> Gráfico menor, Chat maior
left, right = st.columns([1, 2])
with left:
    st.markdown("### 📊 Ocorrências de Vazamento — últimas 48 horas")
    st.image(chart_buf, use_column_width=True)
    st.markdown(f"**Resumo:** Média = {resumo['media']:.2f} | Pico = {resumo['max']} às {resumo['hora_pico']} | Total = {resumo['total']}")
    
    # audio / pdf buttons
    st.markdown("---")
    col_a, col_b, col_c = st.columns([1,1,1])
    # Para corrigir o download button
    pdf_buf = gerar_pdf_report(resumo, chart_buf)
    chart_buf.seek(0)

    with col_a:
        if st.button("🔊 Ouvir diagnóstico"):
            texto = (f"Detectamos um possível vazamento na máquina {MACHINE}. "
                     f"Há um pico de ocorrências às {resumo['hora_pico']}, com média de {resumo['media']:.2f} ocorrências por hora. "
                     "Recomenda-se isolar a área, despressurizar o equipamento e verificar juntas e válvulas.")
            audio_buf = gerar_audio_tts(texto)
            if audio_buf:
                st.audio(audio_buf.read(), format='audio/mp3')

    with col_b:
        # gerar PDF e oferecer download (movemos a geração para evitar recálculo)
        st.download_button("⬇️ Baixar Relatório (PDF)", data=pdf_buf, file_name=f"Relatorio_{MACHINE}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
    
    with col_c:
        # reed chart_buf
        st.download_button("⬇️ Baixar PNG", data=chart_buf, file_name=f"ocorrencias_{MACHINE}.png", mime="image/png")


with right:
    st.markdown("### 💬 Conversa com EVA")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # 4. Histórico de chat em container com scroll
    chat_placeholder = st.container()
    with chat_placeholder:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        # show chat
        for entry in st.session_state.chat_history:
            if entry["role"] == "user":
                st.markdown(f"<div class='chat-user'>**Você:** {entry['text']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-eva'>**EVA:** {entry['text']}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Input e botões de ação
    col_input, col_send, col_clear = st.columns([4, 1, 1])
    with col_input:
        user_input = st.text_input("Digite sua pergunta para EVA", key="user_prompt", label_visibility="collapsed", placeholder="O que devo fazer agora?")

    with col_send:
        send = st.button("Enviar", key="send_button", use_container_width=True)

    with col_clear:
        clear = st.button("Limpar", key="clear_button", use_container_width=True)

    if clear:
        st.session_state.chat_history = []
        st.rerun() # Use st.rerun() no Streamlit mais recente
        
    if send and user_input:
        # append user
        st.session_state.chat_history.append({"role":"user","text":user_input})
        # call OpenAI agent
        with st.spinner("EVA está analisando..."):
            resposta = call_openai_agent(user_input, resumo)
        st.session_state.chat_history.append({"role":"assistant","text":resposta})
        
        # auto-play TTS: generate and show audio player (removido para evitar poluição visual, pode ser adicionado de volta se o usuário pedir)
        # áudio pode ser gerado/tocado no próprio histórico
        
        # refresh
        st.rerun() # Use st.rerun() no Streamlit mais recente

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
