import os
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from statsbombpy import sb
from dotenv import load_dotenv
import requests
import google.generativeai as genai
from langchain.tools import tool
import json

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def fetch_match_events(match_id: int):
    """
    Retorna os eventos de uma partida pelo ID.
    
    Args:
        match_id (int): ID da partida.

    Returns:
        list[dict]: Lista de eventos da partida.
    """
    try:
        return sb.events(match_id)
    except Exception as e:
        raise ValueError(f"Erro ao buscar eventos da partida: {e}")
    

def filter_key_events(events):
    """
    Filtra os eventos principais da partida (gols, assistências, cartões).

    Args:
        events (DataFrame): Dados dos eventos de uma partida.

    Returns:
        list[dict]: Lista de eventos importantes.
    """
    key_events = events[events['type'].isin(['Goal', 'Assist', 'Card'])]
    return key_events.to_dict('records')


@tool
def get_events(action_input) -> str:
    """
    Filtra os eventos principais da partida (gols, assistências, cartões).

    Args:
        action_input (str): JSON contendo o ID da partida.

    Returns:
        str: String dos principais eventos importantes.
    """
    entrada = json.loads(action_input)
    match_id = entrada['match_id']

    # Obter eventos com base no match_id
    eventos = sb.events(match_id)
    gols = eventos[eventos['shot_outcome'] == 'Goal'][['player', 'team', 'minute', 'shot_outcome', 'shot_technique', 'team']]
    gols = gols.dropna(axis=1, how='all')
    assist = eventos[eventos['pass_goal_assist']==True]
    assist = assist.dropna(axis=1, how='all')
    chutes_gol = eventos[eventos['shot_outcome'] == 'Saved'][['minute','period','team', 'player']]
    chutes_gol = chutes_gol.dropna(axis=1, how='all')

    gols_df = gols.apply(
        lambda row: ', '.join([f"{col}: {row[col]}" for col in gols.columns]),
        axis=1
    ).tolist()

    assist_df = assist.apply(
        lambda row: ', '.join([f"{col}: {row[col]}" for col in assist.columns]),
        axis=1
    ).tolist()

    chutes_gol_df = chutes_gol.apply(
        lambda row: ', '.join([f"{col}: {row[col]}" for col in chutes_gol.columns]),
        axis=1
    ).tolist()

    # Converter a lista em uma string
    gols_str = "\n".join(gols_df)
    assist_str = "\n".join(assist_df)
    chutes_gol_str = "\n".join(chutes_gol_df)
    eventos_str = gols_str + assist_str + chutes_gol_str

    return eventos_str




def summarize_match(events: list, competition_id, season_id, match_id, style="Formal") -> str:
    """
    Gera uma sumarização dos eventos da partida usando Gemini.

    Args:
        events (list[dict]): Lista de eventos importantes da partida.
        style (str): Estilo de narração ('Formal', 'Humorístico', 'Técnico').

    Returns:
        str: Texto sumarizado da partida.
    """
    # Criação do prompt baseado nos eventos e no estilo de narração
    prompt = f"Estilo de narração: {style}\n\n"
    prompt += "Resumo dos eventos da partida:\n"
    
    for event in events:
        prompt += f"{event['minute']}': {event['type']['name']} por {event['player']['name']}\n"

    prompt += "\nResuma a partida de forma clara e amigável."
    
    # Detalhes da partida
    detalhes = sb.matches(competition_id=competition_id, season_id=season_id)
    detalhes = detalhes[detalhes['match_id']==int(match_id)]

    detalhes_df = detalhes.apply(
    lambda row: ', '.join([f"{col}: {row[col]}" for col in detalhes.columns]),
    axis=1).tolist()

    # Converter a lista em uma string (exemplo: separando por quebra de linha)
    detalhes_str = "\n".join(detalhes_df)

    # Adicionar ao prompt
    prompt += f"\nDetalhes da partida:\n{detalhes_str}"

    # Chamada ao modelo Gemini para gerar o resumo
    response = model.generate_content(prompt)

    return response.text

def summarize_player_profile(events, player_id):
    """
    Gera o perfil detalhado de um jogador com base nos eventos de uma partida.

    Args:
        events (list[dict]): Lista de eventos da partida.
        player_id (int): ID do jogador.

    Returns:
        dict: Dados detalhados do jogador (nome, estatísticas, etc.).
    """
    player_events = [event for event in events if event.get('player', {}).get('id') == player_id]
    if not player_events:
        raise ValueError("Nenhum dado disponível para o jogador selecionado.")

    # Estatísticas do jogador
    passes = sum(1 for event in player_events if event['type']['name'] == "Pass")
    shots = sum(1 for event in player_events if event['type']['name'] == "Shot")
    tackles = sum(1 for event in player_events if event['type']['name'] == "Tackle")
    minutes_played = max(event['minute'] for event in player_events)

    # Nome do jogador
    player_name = player_events[0]['player']['name']

    return {
        "name": player_name,
        "passes": passes,
        "shots": shots,
        "tackles": tackles,
        "minutes_played": minutes_played
    }
