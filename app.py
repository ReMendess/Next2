import streamlit as st
import openai

# --- CONFIGURAÇÕES ---
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY
MODEL = "gpt-4o-mini"  # ou o modelo que desejar

# --- UI ---
st.set_page_config(page_title="Agente de Suporte Industrial", layout="wide")
st.title("🤖 Agente Inteligente para Vazamentos & Falhas Mecânicas")
st.write("""
Este agente é especializado em **diagnóstico inicial e orientações de contenção** para **vazamentos e problemas em máquinas industriais**.
> Ele **não substitui** engenheiros ou equipes presenciais.  
> Use para **primeiros passos, triagem e orientação**.
""")

# Histórico de conversa
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Prompt base
system_prompt = """
Você é AVA — Assistente Virtual de Apoio Industrial.
Especialização: identificação e orientação inicial para incidentes como:
- Vazamentos de óleo, fluido hidráulico, água industrial, vapor
- Superaquecimento de motores
- Vibração anormal
- Ruídos fora do padrão
- Queda de rendimento operacional

Suas responsabilidades:
1. Coletar informações do operador (local, cheiro, cor, pressão, temperatura, ruídos).
2. Orientar medidas imediatas seguras (travar máquina, sinalizar área, isolar energia).
3. Sugerir hipóteses prováveis com base nos sintomas narrados.
4. Orientar quando **acionar manutenção imediatamente**.
5. Priorize **segurança humana acima de tudo**.

Nunca minimize risco. Se houver dúvida → recomendar *parada controlada e bloqueio (LOTO)*.
"""

# Mostrar histórico
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"**Você:** {msg}")
    else:
        st.markdown(f"**AVA:** {msg}")

# Entrada
user_msg = st.text_input("Descreva o que está acontecendo na máquina:")

if st.button("Enviar") and user_msg.strip():
    messages = [
        {"role": "system", "content": system_prompt},
        *[
            {"role": r, "content": m}
            for r, m in st.session_state.chat_history
        ],
        {"role": "user", "content": user_msg},
    ]

    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            max_tokens=500
        )
        bot_reply = response.choices[0].message.content.strip()
    except Exception as e:
        bot_reply = f"⚠️ Erro ao acessar o modelo: {e}"

    st.session_state.chat_history.append(("user", user_msg))
    st.session_state.chat_history.append(("assistant", bot_reply))
    st.rerun()

