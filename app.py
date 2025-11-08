import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import openai   # pip install openai

# --- CONFIGURAÇÕES ---
OPENAI_API_KEY = "SEU_OPENAI_API_KEY"  # ou use st.secrets
openai.api_key = OPENAI_API_KEY
MODEL = "gpt-4o-mini"  # ajuste conforme disponibilidade

# --- UI ---
st.set_page_config(page_title="Agente de Suporte - Vazamentos", layout="wide")
st.title("🤖 Agente de Suporte — Cenário de Vazamentos (SIMULADO)")
st.write("Este agente **não** recebe nem grava dados reais. Aqui você pode simular ocorrências e conversar com o assistente especializado em vazamentos.")

# sessão para armazenar simulação em memória
if "sim_df" not in st.session_state:
    st.session_state.sim_df = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

col1, col2 = st.columns([2, 1])

with col2:
    st.markdown("### Gerar gráfico simulado")
    window_days = st.number_input("Janela (horas)", min_value=1, max_value=168, value=24)
    intensity = st.slider("Intensidade média (ocorrências/h)", 0.1, 20.0, 2.0)
    burstiness = st.slider("Risco de picos (0=suave, 1=explosivo)", 0.0, 1.0, 0.3)
    noise = st.slider("Ruído (%)", 0.0, 1.0, 0.1)
    generate = st.button("▶️ Gerar gráfico de ocorrências simuladas")

    if generate:
        # gerar tempos (hora-a-hora) para a janela
        now = datetime.datetime.now()
        periods = int(window_days)  # horas
        times = [now - datetime.timedelta(hours=i) for i in range(periods)][::-1]

        # Simulação: processo Poisson com picos aleatórios (burst)
        base_rate = intensity
        rates = np.random.normal(loc=base_rate, scale=base_rate * noise, size=periods)
        # adicionar picos aleatórios
        num_peaks = max(1, int(burstiness * 5))
        for _ in range(num_peaks):
            peak_pos = np.random.randint(0, periods)
            peak_height = base_rate * (5 + 10 * burstiness) * np.random.rand()
            # espalha o pico em uma janela curta
            spread = max(1, int(3 * (1 + burstiness*4)))
            for s in range(-spread, spread+1):
                idx = peak_pos + s
                if 0 <= idx < periods:
                    rates[idx] += peak_height * np.exp(-abs(s)/2)

        # garantir não-negatividade
        rates = np.clip(rates, 0.0, None)

        # gerar contagens (Poisson)
        counts = np.random.poisson(rates)
        df = pd.DataFrame({"timestamp": times, "ocorrencias": counts})
        st.session_state.sim_df = df

        # resumo para o agente usar
        summary = {
            "media_por_hora": float(df.ocorrencias.mean()),
            "maximo": int(df.ocorrencias.max()),
            "horario_maximo": df.loc[df.ocorrencias.idxmax(), "timestamp"].strftime("%Y-%m-%d %H:%M"),
            "total_ocorrencias": int(df.ocorrencias.sum()),
            "janela_horas": periods
        }
        st.session_state.sim_summary = summary
        st.success("Simulação gerada. Use o chat para pedir análises baseadas na simulação.")

with col1:
    # gráfico (se existir)
    if st.session_state.sim_df is not None:
        st.markdown("### Gráfico de ocorrências simuladas")
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(st.session_state.sim_df["timestamp"], st.session_state.sim_df["ocorrencias"])
        ax.set_xlabel("Hora")
        ax.set_ylabel("Ocorrências")
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.info("Nenhuma simulação gerada ainda. Abra o painel direito e clique em 'Gerar gráfico de ocorrências simuladas'.")

st.markdown("---")
st.markdown("### Conversa com o Agente (contexto: vazamentos)")

# Prepare system prompt fixo — agente já preparado para vazamentos
system_prompt = """
Você é EVA, assistente virtual especializado em suporte a incidentes de vazamento em ambientes industriais.
Seu papel: orientar o usuário sobre diagnóstico inicial, medidas de contenção imediata, sinais que indicam falsos-positivos e passos para acionamento de equipe técnica.
Você NÃO tem dados reais do sensor; você pode usar a simulação gerada pelo usuário (caso exista) para fundamentar respostas.
Se houver um resumo de simulação fornecido, mencione-o de forma transparente (ex.: "Na simulação x..."). Forneça instruções práticas, passo-a-passo e sugestões de priorização.
Sempre peça ao usuário para confirmar condições de segurança e acionar emergência se houver risco à integridade humana.
"""

# display conversation
for entry in st.session_state.chat_history:
    role, text = entry
    if role == "user":
        st.markdown(f"**Você:** {text}")
    else:
        st.markdown(f"**EVA:** {text}")

# input
user_msg = st.text_input("Digite sua pergunta para o agente (ex.: 'O que fazer agora?')")

if st.button("Enviar") and user_msg:
    # compor mensagem com contexto simulado (se houver)
    context_text = ""
    if st.session_state.get("sim_summary"):
        s = st.session_state.sim_summary
        context_text = (
            f"Resumo da simulação:\n"
            f"- janela (horas): {s['janela_horas']}\n"
            f"- média por hora: {s['media_por_hora']:.2f}\n"
            f"- total ocorrências: {s['total_ocorrencias']}\n"
            f"- pico máximo: {s['maximo']} às {s['horario_maximo']}\n"
        )

    # construir prompt para API
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if context_text:
        messages.append({"role": "system", "content": f"Contexto adicional (simulação):\n{context_text}"})
    # adicionar histórico local (opcional)
    # enviar pergunta atual
    messages.append({"role": "user", "content": user_msg})

    # chamada ao LLM
    try:
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            max_tokens=400
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Erro ao chamar LLM: {e}"

    # guardar no histórico da sessão e mostrar
    st.session_state.chat_history.append(("user", user_msg))
    st.session_state.chat_history.append(("assistant", answer))
    st.experimental_rerun()
