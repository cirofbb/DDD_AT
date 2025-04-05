# Documentação da API FastAPI para resumo de partidas e perfis de jogadores

## Descrição
Este projeto implementa uma API usando o framework **FastAPI** que permite:

1. **Gerar resumos de partidas de futebol** com base em eventos registrados.
2. **Gerar perfis detalhados de jogadores** com base nos eventos específicos de uma partida.

A API integra funcionalidades de sumarização e manipulação de dados esportivos, utilizando as bibliotecas **StatsBombPy**, **Google Gemini** e **Pandas**.

---

## Instalação

### Pré-requisitos
- Python 3.8+
- Variável de ambiente `GEMINI_API_KEY` configurada com uma chave válida da API do Google Gemini.

### Passos de Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Certifique-se de configurar a variável de ambiente `GEMINI_API_KEY`:
   - No Linux/MacOS:
     ```bash
     export GEMINI_API_KEY="sua-chave-api"
     ```
   - No Windows (Command Prompt):
     ```cmd
     set GEMINI_API_KEY="sua-chave-api"
     ```

---

## Como Executar

1. Execute o servidor FastAPI:
   ```bash
   uvicorn main:app --reload
   ```

2. Acesse a interface de documentação no navegador em:
   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Redoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Endpoints

### **1. `/match_summary`**
- **Descrição**: Gera um resumo da partida com base nos eventos coletados.
- **Método**: `POST`
- **Payload**:
  ```json
  {
      "competition_id": 1,
      "season_id": 2023,
      "match_id": 123456,
      "style": "Formal"
  }
  ```
- **Resposta**:
  ```json
  {
      "summary": "Resumo da partida gerado com sucesso."
  }
  ```

### **2. `/player_profile`**
- **Descrição**: Retorna um perfil detalhado de um jogador específico em uma partida.
- **Método**: `POST`
- **Payload**:
  ```json
  {
      "match_id": 123456,
      "player_name": "Nome do Jogador"
  }
  ```
- **Resposta**:
  ```json
  {
      "player_profile": { "estatísticas": "detalhes do perfil" }
  }
  ```

### **3. `/`**
- **Descrição**: Verifica se a API está online.
- **Método**: `GET`
- **Resposta**:
  ```json
  {
      "message": "Aplicação tá ON!"
  }
  ```

---

## Estrutura de Arquivos

```plaintext
.
├── main.py                  # Ponto de entrada da aplicação FastAPI
├── rotas.py                 # Define as rotas e a lógica principal da API
├── summarization_1.py       # Contém funções para sumarização de partidas e perfis
├── abas_1.py                # Utilitário para buscar eventos de partidas
├── requirements.txt         # Lista de dependências do Python
└── README.md                # Documentação do projeto
```

---

## Dependências Principais
- **FastAPI**: Framework para construir APIs rápidas e robustas.
- **Uvicorn**: Servidor ASGI para rodar a aplicação FastAPI.
- **Pandas**: Manipulação de dados.
- **Numpy**: Suporte a operações numéricas.
- **StatsBombPy**: Biblioteca para acessar dados esportivos da StatsBomb.
- **Google Gemini**: API de IA generativa para sumarizações.

---
