import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF
import datetime
from openai import OpenAI
import os

# ===============================
# Configurações Iniciais
# ===============================
st.set_page_config(page_title="Monitoramento Industrial - EVA", layout="wide")
st.markdown(
    """
    <style>
    body {background-color: #0e1117; color: white;}
    .stApp {background-color: #0e1117; color: white;}
    div[data-testid="stMarkdownContainer"] p {color: white;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===============================
# Função para gerar gráfico simulado
# ===============================
def gerar_grafico():
    st.subheader("📊 Histórico de Ocorrências de Vazamento")
    dias = np.arange(1, 11)
    ocorrencias = np.random.randint(0, 5, size=10)
    fig, ax = plt.subplots()
    ax.plot(dias, ocorrencias, marker='o', color='cyan')
    ax.set_facecolor('#111111')
    ax.set_xlabel('Dias')
    ax.set_ylabel('Ocorrências')
    ax.set_title('Histórico de Vazamentos - Máquina A2203', color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('white')
    st.pyplot(fig)

# ===============================
# Função para gerar relatório PDF
# ===============================
def gerar_pdf():
    data_atual = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Relatório de Manutenção - EVA', 0, 1, 'C')

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Empresa: Reply', 0, 1)
    pdf.cell(0, 10, f'Data: {data_atual}', 0, 1)
    pdf.cell(0, 10, 'Máquina: A2203', 0, 1)
    pdf.multi_cell(0, 10, 'Detalhes da máquina: Modelo antigo, última manutenção há 8 meses.')
    pdf.cell(0, 10, 'Defeito: Vazamento identificado no tanque principal.', 0, 1)
    pdf.cell(0, 10, 'Autorização: Liberada para manutenção imediata.', 0, 1)

    pdf.multi_cell(0, 10, 'Passos para manutenção:\n1. Isolar área.\n2. Drenar tanque.\n3. Substituir mangueira danificada.\n4. Testar estanqueidade.')
    pdf.multi_cell(0, 10, 'IPI necessários:\nMangueira 32mm - Cod. 9982\nSelante industrial - Cod. 4021')

    pdf.cell(0, 10, 'Técnicos designados: João S., Renata P.', 0, 1)
    pdf.multi_cell(0, 10, 'Peças utilizadas:\n- 1x Mangueira 32mm\n- 2x Selante industrial')
    pdf.output('relatorio_eva.pdf')
    return 'relatorio_eva.pdf'

# ===============================
# Função de agente conversacional OpenAI
# ===============================
def conversar_com_agente(pergunta):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é a EVA, assistente técnica de manutenção industrial. Responda com clareza e precisão."},
            {"role": "user", "content": pergunta}
        ]
    )
    return resposta.choices[0].message.content

# ===============================
# Layout da Aplicação
# ===============================
st.title("🤖 EVA - Sistema de Monitoramento Industrial")
st.markdown("---")

# Caixa de ação rápida
st.subheader("⚙️ Ações Rápidas")
col1, col2 = st.columns(2)
with col1:
    if st.button("🚨 Isolar área"):
        st.success("Área isolada com sucesso!")
with col2:
    if st.button("🔧 Acionar manutenção"):
        st.warning("Equipe de manutenção acionada!")

st.markdown("---")

gerar_grafico()

st.markdown("---")

# Agente de suporte
st.subheader("💬 Agente EVA de Suporte Técnico")
entrada = st.text_input("Descreva o problema ou solicite ajuda:")
if st.button("Enviar para EVA") and entrada:
    resposta = conversar_com_agente(entrada)
    st.markdown(f"**EVA:** {resposta}")

st.markdown("---")

# Geração de relatório
st.subheader("🧾 Relatório de Manutenção")
if st.button("Gerar Relatório PDF"):
    arquivo_pdf = gerar_pdf()
    with open(arquivo_pdf, "rb") as file:
        st.download_button(
            label="📥 Baixar Relatório",
            data=file,
            file_name="Relatorio_EVA.pdf",
            mime="application/pdf"
        )
