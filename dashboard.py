import streamlit as st
import json
import abas_1
from statsbombpy import sb
from summarization_1 import fetch_match_events, filter_key_events, summarize_match

# Função sem cache para carregar as competições
def fetch_competitions() -> dict:
    """
    Carrega os dados das competições da API StatsBomb.
    Retorna um dicionário com as informações das competições.
    """
    return sb.competitions(fmt='dict')

# Carregamento inicial dos dados
competitions_data = fetch_competitions()

# Estrutura principal
st.title("Análise de Partidas de Futebol")
st.write("Navegue pelas opções abaixo para selecionar competição, temporada e partida.")

# Organização dos menus como containers para maior clareza
with st.container():
    st.header("Seleção de Competição e Temporada")
    col1, col2 = st.columns(2)

    # Seleção da competição
    with col1:
        available_competitions = list({entry['competition_name'] for entry in competitions_data.values()})
        competition_choice = st.selectbox("Escolha a Competição", available_competitions)

        competition_id = next(
            (entry['competition_id'] for entry in competitions_data.values()
             if entry['competition_name'] == competition_choice),
            None
        )

    # Seleção da temporada
    with col2:
        filtered_seasons = [
            (entry['season_name'], entry['season_id'])
            for entry in competitions_data.values()
            if entry['competition_name'] == competition_choice
        ]

        season_names = [season[0] for season in filtered_seasons]
        season_id_map = {season[0]: season[1] for season in filtered_seasons}

        season_choice = st.selectbox("Escolha a Temporada", season_names)
        season_id = season_id_map.get(season_choice)

# Obter partidas disponíveis para competição e temporada selecionadas
if competition_id and season_id:
    matches_data = sb.matches(competition_id=competition_id, season_id=season_id, fmt='dict')
    match_options = [
        {
            "match_id": match['match_id'],
            "display_name": f"{match['home_team']['home_team_name']} vs {match['away_team']['away_team_name']}"
        }
        for match in matches_data.values()
    ]

    match_display_names = [match['display_name'] for match in match_options]
    match_id_map = {match['display_name']: match['match_id'] for match in match_options}

    selected_match_name = st.selectbox("Escolha a Partida", match_display_names)
    selected_match_id = match_id_map.get(selected_match_name)

    # Escolha de estilo de narração
    with st.expander("Estilo de Narração"):
        narration_style = st.radio(
            "Selecione o estilo do narrador:",
            ('Formal', 'Humorístico', 'Técnico')
        )

    # Detalhes da partida e exibição de abas
    if selected_match_id:
        # Obter eventos da partida
        try:
            events = fetch_match_events(selected_match_id)
            key_events = filter_key_events(events)

            # Sumarizar os eventos
            summary = summarize_match(key_events, 
                                      competition_id=competition_id, 
                                      season_id=season_id, 
                                      match_id=selected_match_id, 
                                      style=narration_style)

            # Exibir sumarização no Streamlit
            st.subheader("Sumarização da Partida")
            st.write(summary)

        except Exception as e:
            st.error(f"Erro ao gerar sumarização: {e}")
        
        selected_match = matches_data[selected_match_id]

        match_details = {
            'Data': selected_match.get('match_date', 'N/A'),
            'Competição': selected_match.get('competition', {}).get('competition_name', 'N/A'),
            'Estádio': selected_match.get('stadium', {}).get('name', 'N/A'),
            'Times': f"{selected_match.get('home_team', {}).get('home_team_name', 'N/A')} vs "
                     f"{selected_match.get('away_team', {}).get('away_team_name', 'N/A')}",
            'Placar': f"{selected_match.get('home_score', 'N/A')} - {selected_match.get('away_score', 'N/A')}",
            'Técnico (Casa)': selected_match.get('home_team', {}).get('managers', [{}])[0].get('name', 'N/A'),
            'Técnico (Visitante)': selected_match.get('away_team', {}).get('managers', [{}])[0].get('name', 'N/A')
        }

        st.subheader("Detalhes da Partida")
        st.json(match_details)

        # Armazenar estado para abas
        st.session_state['match_info'] = match_details
        st.session_state['match_id'] = selected_match_id
        st.session_state['narration_style'] = narration_style

        # Abas para análise
        stats_tab, qa_tab = st.tabs(
            ["Estatísticas do Jogador", "Perguntas & Respostas"]
        )

        abas_1.render_player_profile(stats_tab)
        #st.write(selected_match_id)
        #selected_match_id = int(selected_match_id)
        abas_1.match_qa_tab(qa_tab, selected_match_id)
else:
    st.warning("Por favor, selecione uma competição e temporada para continuar.")
