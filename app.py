import streamlit as st
from openai import OpenAI

# --- CONFIGURAÇÕES ---
client = OpenAI(api_key="SEU_OPENAI_API_KEY")
MODEL = "gpt-4o-mini"  # ou outro modelo disponível

# --- UI ---
st.set_page_config(page_title="Agente de Suporte Industrial", layout="wide")
st.title("🤖 Agente Inteligente para Vazamentos & Falhas Mecânicas")
st.write("""
Agente especializado em **triagem e orientação inicial** para incidentes como vazamentos,
superaquecimento, vibrações anormais e falhas de máquinas.

⚠️ **Segurança humana > produção.**  
Este assistente **não substitui** manutenção presencial.
""")

# Histórico
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

system_prompt = """
Você é AVA — Assistente Virtual de Apoio Industrial.
Seu foco é segurança e resposta inicial a incidentes industriais.

Regras:
1. Sempre pergunte primeiro sobre segurança e se há pessoas em risco.
2. Oriente ações imediatas de contenção (sem assumir dados não fornecidos).
3. Explique possíveis causas com linguagem clara.
4. Indique quando é necessário aplicar LOTO (Lockout/Tagout).
5. Se houver risco humano → orientar evacuação imediata.
"""

# Mostrar histórico
for r, msg in st.session_state.chat_history:
    if r == "user":
        st.markdown(f"**Você:** {msg}")
    else:
        st.markdown(f"**AVA:** {msg}")

user_msg = st.text_input("Descreva a situação ou problema:")

if st.button("Enviar") and user_msg.strip():

    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": r, "content": m} for r, m in st.session_state.chat_history]
    messages.append({"role": "user", "content": user_msg})

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500
        )
        bot_reply = resp.choices[0].message.content.strip()

    except Exception as e:
        bot_reply = f"⚠️ Erro ao consultar modelo: {e}"

    st.session_state.chat_history.append(("user", user_msg))
    st.session_state.chat_history.append(("assistant", bot_reply))

    st.rerun()


