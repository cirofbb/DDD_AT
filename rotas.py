from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from statsbombpy import sb
import google.generativeai as genai
import os
import pandas as pd
import numpy as np
from summarization_1 import summarize_match, summarize_player_profile
from abas_1 import fetch_match_events

# Configuração do modelo Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

router = APIRouter()

class MatchSummaryRequest(BaseModel):
    competition_id: int
    season_id: int
    match_id: int
    style: Optional[str] = "Formal"

class PlayerProfileRequest(BaseModel):
    match_id: int
    player_name: str

# Rota para sumarização da partida
@router.post('/match_summary')
def match_summary(request: MatchSummaryRequest):
    try:
        # Obtém eventos da partida
        events = fetch_match_events(request.match_id)

        # Verifica se os eventos foram obtidos
        if not events:
            raise HTTPException(status_code=404, detail="Eventos da partida não encontrados.")

        # Gera o resumo
        summary = summarize_match(
            events=events,
            competition_id=request.competition_id,
            season_id=request.season_id,
            match_id=request.match_id,
            style=request.style
        )
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o resumo da partida: {str(e)}")


# Rota para o perfil do jogador
@router.post('/player_profile')
def player_profile(request: PlayerProfileRequest):
    try:
        events = sb.events(match_id=request.match_id)
        player_events = events[events['player'] == request.player_name]

        if player_events.empty:
            raise HTTPException(status_code=404, detail="Nenhum evento encontrado para o jogador selecionado.")

        # Substituindo valores infinitos e NaN por None
        player_events = player_events.replace([np.inf, -np.inf], None).where(pd.notnull(player_events), None)

        # Convertendo os dados para JSON
        player_profile = summarize_player_profile(events=player_events.to_dict("records"), player_id=request.player_name)

        return player_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o perfil do jogador: {str(e)}")