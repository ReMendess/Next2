import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import openai

# ==============================================
# CONFIGURAÇÕES
# ==============================================
openai.api_key = "SUA_CHAVE_API"  # substitua pela sua chave
MODEL = "gpt-4o-mini"

st.set_page_config(page_title="EVA - Assistente de Suporte Industrial", layout="centered")

# ==============================================
# GERAÇÃO AUTOMÁTICA DE GRÁFICO (SIMULAÇÃO FIXA)
# ==============================================
def gerar_simulacao_padrao():
    np.random.seed(42)  # garante que o gráfico será sempre igual
    horas = 48
    agora = datetime.datetime.now()
    tempos = [agora - datetime.timedelta(hours=i) for i in range(horas)][::-1]

    # padrão de ocorrências simuladas (picos leves + ruído)
    base = np.linspace(3, 7, horas) + np.random.normal(0, 1, horas)
    picos = [10 if 18 < i < 22 else 0 for i in range(horas)]
    ocorrencias = np.maximum(base + picos, 0).astype(int)

    df = pd.DataFrame({"timestamp": tempos, "ocorrencias": ocorrencias})
    resumo = {
        "media": round(df.ocorrencias.mean(), 2),
        "max": int(df.ocorrencias.max()),
        "horario_pico": df.loc[df.ocorrencias.idxmax(), "timestamp"].strftime("%H:%M"),
        "total": int(df.ocorrencias.sum()),
    }
    return df, resumo

df, resumo = gerar_simulacao_padrao()

# ==============================================
# INTERFACE
# ==============================================
st.title("🤖 EVA - Evolution Virtual Assistant")
st.markdown(
    "Sistema de monitoramento industrial - painel de ocorrências recentes."
)
st.markdown("### 📊 Ocorrências detectadas nas últimas 48 horas")

# gráfico fixo (igual para todos)
fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(df["timestamp"], df["ocorrencias"], linewidth=2)
ax.set_xlabel("Horário")
ax.set_ylabel("Ocorrências")
ax.grid(True, linestyle="--", alpha=0.6)
st.pyplot(fig)

# breve resumo abaixo do gráfico
st.markdown(
    f"**Resumo:** Média = {resumo['media']} | Pico = {resumo['max']} ocorrências às {resumo['horario_pico']} | Total = {resumo['total']} ocorrências."
)
st.divider()

# ==============================================
# AGENTE DE SUPORTE (CHAT)
# ==============================================
st.markdown("### 💬 Converse com EVA (Assistente de Suporte)")
st.write(
    "EVA é uma assistente especializada em incidentes de **vazamento industrial**, "
    "pronta para orientar sobre diagnósticos, contenção e segurança."
)

# inicializa histórico
if "chat" not in st.session_state:
    st.session_state.chat = []

# mostra histórico
for msg in st.session_state.chat:
    if msg["role"] == "user":
        st.markdown(f"**Você:** {msg['content']}")
    else:
        st.markdown(f"**EVA:** {msg['content']}")

# entrada do usuário
pergunta = st.text_input("Digite sua dúvida:")

# prompt base do agente
prompt_sistema = f"""
Você é EVA, assistente técnica da Evolution.
Seu papel é orientar sobre vazamentos e situações de anomalias em sensores de umidade e pressão.

Contexto atual (simulado, mas o usuário não sabe disso):
- Monitoramento de 48h mostrou média de {resumo['media']} ocorrências/hora.
- Pico de {resumo['max']} ocorrências às {resumo['horario_pico']}.
- Total de {resumo['total']} ocorrências no período.
Comporte-se como se esses dados fossem reais.
Explique causas prováveis, medidas de segurança, ações corretivas e recomendações.
Não diga que é uma simulação.
Fale de forma profissional e natural.
"""

# envio da pergunta
if st.button("Enviar") and pergunta:
    try:
        resposta = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pergunta},
            ],
            max_tokens=400,
        )
        conteudo = resposta.choices[0].message.content.strip()
    except Exception as e:
        conteudo = f"[Erro ao consultar modelo IA: {e}]"

    st.session_state.chat.append({"role": "user", "content": pergunta})
    st.session_state.chat.append({"role": "assistant", "content": conteudo})
    st.experimental_rerun()
