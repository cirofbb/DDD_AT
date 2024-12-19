from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from typing import List
from summarization_1 import get_events



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