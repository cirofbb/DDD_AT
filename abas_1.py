import streamlit as st
import statsbombpy as sb
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.schema import AIMessage, HumanMessage
from summarization_1 import *

from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from typing import List
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

def load_agent() -> AgentExecutor:
    """
    Load the agent with the given tool names
    """
    llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.2)
    
    football_prompt = """
    You are a helpful AI assistant tasked with analyzing a football match. 
    Your goal is to provide insights and perform analyses based on the match's events.
    The match is identified by its unique database ID: {match_id}. 

    The task involves multiple aspects:
    1. Analyze match details such as date, location, competition, and result.
    2. Provide context about the match's importance (e.g., stage, rivalry, stakes).
    3. Analyze and comment on the starting XI of both teams, including key players, tactical insights, or notable absences.
    4. Perform any other relevant tasks requested by the user regarding the match.

    You have access to the following tools: {tool_names}.
    Descriptions of tools: {tools}.

    ### Tools and Usage Instructions:
    - Each tool has a specific purpose, such as retrieving match details, analyzing lineups, or generating summaries.
    - To use a tool, respond exactly in this format:

    Thought: [Your reasoning about what action to take next]
    Action: [The name of the tool to use]
    Action Input: [The input required by the tool, such as the match_id or specific data]
    Observation: [The output or result from the tool]

    Example:
        Thought: I need to retrieve the basic details of the match to provide an overview.
        Action: get_match_details
        Action Input: {{"match_id": "12345", "competition_id": "123", "season_id": "02"}}
        Observation: Do I have the match details? If not, I will use the tool to retrieve them.
                     Otherwise, I will proceed with the analysis.

    ### Observations and Next Steps:
    - Based on the tool's output, decide on the next action or provide your analysis.
    - If more data is needed, use another tool or refine your analysis.
    - If the task is complete, provide a final answer.

    ### Stopping Condition:
    - When the analysis is complete, respond in this format:
    
    Thought: I have completed the analysis. No further tools are required.
    Final Answer: [Your final comprehensive analysis, summarizing all insights about the match.]

    ### Current Task:
    {input}

    ### Agent's Workspace:
    {agent_scratchpad}
    """
    prompt = PromptTemplate(
       input_variables=["match_id",
                        "input",
                        "agent_scratchpad",
                        "tool_names",
                        "tools"],
       template=football_prompt
    )
    tools = [get_events]
    agent = create_react_agent(llm, tools=tools, prompt=prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,
        verbose=True,
        max_iterations=10
    )

def render_player_profile(tab):
    """Renderiza o perfil do jogador"""
    selected_match_id = st.session_state.get('match_id')

    if not selected_match_id:
        tab.error("Nenhuma partida foi selecionada.")
        return

    try:
        # Obtenha eventos da partida
        events = fetch_match_events(selected_match_id)

        # Transformar o DataFrame em uma lista de dicionários, se necessário
        if isinstance(events, pd.DataFrame):
            events = events.to_dict('records')

        # Verifique se os dados estão no formato esperado
        if not isinstance(events, list):
            tab.error("Os dados retornados não estão no formato esperado. Esperado: lista de eventos.")
            return

        if not events:
            tab.error("Não há eventos disponíveis para esta partida.")
            return

        # Filtrar jogadores únicos, ignorando valores NaN
        players = {}
        for event in events:
            player_id = event.get('player_id')
            player_name = event.get('player')
            if player_id and player_name and pd.notna(player_id) and pd.notna(player_name):
                players[player_id] = player_name

        if not players:
            tab.error("Nenhum jogador válido foi encontrado nos eventos da partida.")
            return

        # Seleção de jogador
        player_names = list(players.values())
        player_choice1 = tab.selectbox("Selecione o 1º Jogador", player_names, key='Jogador 1')
        player_choice2 = tab.selectbox("Selecione o 2º Jogador", player_names, key='Jogador 2')

        # Encontre o ID correspondente ao jogador
        player_id1 = next(pid for pid, name in players.items() if name == player_choice1)
        player_id2 = next(pid for pid, name in players.items() if name == player_choice2)

        # Estatísticas do jogador
        def calculate_stats(player_id):
            return {
                'Passes': sum(1 for event in events if event.get('player_id') == player_id and event.get('type') == 'Pass'),
                'Finalizações': sum(1 for event in events if event.get('player_id') == player_id and event.get('type') == 'Shot'),
                'Desarmes': sum(1 for event in events if event.get('player_id') == player_id and event.get('type') == 'Tackle'),
                'Minutos jogados': sum(event.get('minute', 0) for event in events if event.get('player_id') == player_id),
            }
        
        
        player_stats1 = calculate_stats(player_id1)
        player_stats2 = calculate_stats(player_id2)

        # Combinar estatísticas em um DataFrame
        stats_df = pd.DataFrame({
            "Estatísticas": list(player_stats1.keys()),
            player_choice1: list(player_stats1.values()),
            player_choice2: list(player_stats2.values()),
        })

        # Exibir tabela interativa
        tab.dataframe(stats_df)

        # Visualizações gráficas
        fig = px.bar(
            stats_df.melt(id_vars=["Estatísticas"], var_name="Jogador", value_name="Valor"),
            x="Estatísticas",
            y="Valor",
            color="Jogador",
            barmode="group",
            title="Comparação de Estatísticas"
        )
        tab.plotly_chart(fig)

    except Exception as e:
        tab.error(f"Erro ao carregar o perfil do jogador: {e}")



def match_qa_tab(tab, match_id):
    """Renderiza a seção de Perguntas & Respostas"""
    msgs = StreamlitChatMessageHistory()


    if "memory" not in st.session_state:
        st.session_state["memory"] = ConversationBufferMemory(messages=msgs, memory_key="chat_history", return_messages=True)

    memory = st.session_state.memory

    with st.container(border=False):
        st.chat_input(key="user_input", on_submit=memorize_message) 
        if user_input := st.session_state.user_input:
            chat_history = st.session_state["memory"].chat_memory.messages
            for msg in chat_history:
                if isinstance(msg, HumanMessage):
                    with st.chat_message("user"):
                        st.write(f"{msg.content}")
                elif isinstance(msg, AIMessage):
                    with st.chat_message("assistant"):
                        st.write(f"{msg.content}")
                        
            with st.spinner("Agent is responding..."):
                try:
                    # Load agent
                    agent = load_agent()
                    
                    # Cache tools to avoid redundant calls
                    tools = [get_events]
                    tool_names = [tool.name for tool in tools]
                    tool_descriptions = [tool.description for tool in tools]

                    # Prepare input for the agent
                    input_data = {
                        "match_id": match_id,
                        "input": user_input,
                        "agent_scratchpad": "",
                        "tool_names": tool_names,
                        "tools": tool_descriptions,
                    }

                    # Debug: Print input to verify structure (optional)
                    #st.write(f"Input to agent: {input_data}")

                    # Invoke agent
                    response = agent.invoke(input=input_data, handle_parsing_errors=True)

                    # Validate response
                    if isinstance(response, dict) and "output" in response:
                        output = response.get("output")
                    else:
                        output = "Sorry, I couldn't understand your request. Please try again."

                    # Add response to chat memory
                    st.session_state["memory"].chat_memory.add_message(AIMessage(content=output))

                    # Display response in chat
                    with st.chat_message("assistant"):
                        st.write(output)

                except Exception as e:
                    # Handle and display errors gracefully
                    st.error(f"Error during agent execution: {str(e)}")
                    st.write("Ensure that your inputs and agent configuration are correct.")

def memorize_message():
    user_input = st.session_state["user_input"]
    st.session_state["memory"].chat_memory.add_message(HumanMessage(content=user_input))

# Função para configurar ou atualizar as informações da partida
def update_match_info(match_data):
    """Atualiza as informações da partida no session_state."""
    st.session_state['match_info'] = match_data
