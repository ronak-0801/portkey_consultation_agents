from crewai import Agent, Task, Crew, Flow, LLM
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_core.tools import Tool
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
from crewai_tools import (
    SearchTools,               # For web searches
    FileTools,                # For file operations
    DataTools,                # For data analysis
    TextTools                 # For text processing
)
import os
import yaml

# Load configuration files
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Load configurations
agents_config = load_config('agents.yml')
tasks_config = load_config('tasks.yml')['tasks']


def createHeaders(api_key, virtual_key, trace_id):
    return {
        "x-portkey-api-key": api_key,
        "x-virtual-key": virtual_key,
        "x-trace-id": trace_id
    }

# Configure LLMs
gpt4_llm = LLM(
    model="openai/gpt-4o-mini",
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=PORTKEY_GATEWAY_URL,
    extra_headers=createHeaders(
        api_key=os.getenv('PORTKEY_API_KEY'),
        virtual_key=os.getenv('VIRTUAL_KEY_OPENAI'),
        trace_id="gpt4"
    )
)

gemini_llm = LLM(
    model="google/gemini-2.0-flash",
    api_key=os.getenv('GEMINI_API_KEY'),
    base_url=PORTKEY_GATEWAY_URL,
    extra_headers=createHeaders(
        api_key=os.getenv('PORTKEY_API_KEY'),
        virtual_key=os.getenv('VIRTUAL_KEY_GEMINI'),
        trace_id="gemini"
    )
)

# Creating Agents with essential tools
data_architect = Agent(
    role=agents_config['data_architect']['role'],
    goal=agents_config['data_architect']['goal'],
    backstory=agents_config['data_architect']['backstory'],
    tools=[
        FileTools.read_file(),          # For file reading
        FileTools.write_file(),         # For file writing
        DataTools.process_csv(),        # For CSV processing
    ],
    llm=gemini_llm
)

analytical_engine = Agent(
    role=agents_config['analytical_engine']['role'],
    goal=agents_config['analytical_engine']['goal'],
    backstory=agents_config['analytical_engine']['backstory'],
    tools=[
        DataTools.process_csv(),        # For data analysis
        SearchTools.search_internet(),   # For research
        WikipediaQueryRun()             # For background research
    ],
    llm=gemini_llm
)

visualization_specialist = Agent(
    role=agents_config['visualization_specialist']['role'],
    goal=agents_config['visualization_specialist']['goal'],
    backstory=agents_config['visualization_specialist']['backstory'],
    tools=[
        FileTools.read_file(),          # For reading data files
        DataTools.process_csv(),        # For data processing
        TextTools.write_markdown()       # For creating reports
    ],
    llm=gemini_llm
)

strategic_planner = Agent(
    role=agents_config['strategic_planner']['role'],
    goal=agents_config['strategic_planner']['goal'],
    backstory=agents_config['strategic_planner']['backstory'],
    tools=[
        SearchTools.search_internet(),   # For market research
        DuckDuckGoSearchRun(),          # For web search
        WikipediaQueryRun(),            # For background research
        TextTools.write_markdown()       # For report writing
    ],
    llm=gpt4_llm
)

# Creating Tasks
data_acquisition_task = Task(
    description=tasks_config['data_acquisition']['description'],
    expected_output=tasks_config['data_acquisition']['expected_output'],
    agent=data_architect
)

data_cleaning_task = Task(
    description=tasks_config['data_cleaning_and_transformation']['description'],
    expected_output=tasks_config['data_cleaning_and_transformation']['expected_output'],
    agent=data_architect,
    context=[data_acquisition_task]
)

data_analysis_task = Task(
    description=tasks_config['data_modeling_and_analysis']['description'],
    expected_output=tasks_config['data_modeling_and_analysis']['expected_output'],
    agent=analytical_engine,
    context=[data_cleaning_task]
)

dashboard_task = Task(
    description=tasks_config['interactive_dashboard_creation']['description'],
    expected_output=tasks_config['interactive_dashboard_creation']['expected_output'],
    agent=visualization_specialist,
    context=[data_analysis_task]
)

strategy_task = Task(
    description=tasks_config['strategic_recommendation_development']['description'],
    expected_output=tasks_config['strategic_recommendation_development']['expected_output'],
    agent=strategic_planner,
    context=[data_analysis_task, dashboard_task]
)

final_report_task = Task(
    description=tasks_config['final_report_generation']['description'],
    expected_output=tasks_config['final_report_generation']['expected_output'],
    agent=strategic_planner,
    context=[strategy_task, dashboard_task]
)

# Defining Flow
reporting_flow = Flow(
    tasks=[
        data_acquisition_task,
        data_cleaning_task,
        data_analysis_task,
        dashboard_task,
        strategy_task,
        final_report_task
    ]
)

# Creating Crew
reporting_crew = Crew(
    agents=[
        data_architect,
        analytical_engine,
        visualization_specialist,
        strategic_planner
    ],
    flows=[reporting_flow],
    verbose=True
)

def run_analysis(subject):
    """
    Run the analysis crew with a specific subject.
    
    Args:
        subject (str): The subject or topic to analyze
    
    Returns:
        dict: The results from the crew's analysis
    """
    try:
        # Create the task context with the subject
        task_context = f"""
        Analyze the following subject in detail: {subject}
        
        Focus on:
        1. Gathering and preparing relevant data
        2. Performing statistical analysis
        3. Creating visualizations
        4. Developing strategic recommendations
        
        Ensure all outputs are well-documented and conclusions are data-driven.
        """
        
        # Start the crew with the task context
        result = reporting_crew.kickoff(
            objective=task_context,
            context=f"Analysis subject: {subject}"
        )
        
        return result
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    subject = "Analysis of market trends in the renewable energy sector for 2024"
    try:
        results = run_analysis(subject)
        print("\nAnalysis Results:")
        print(results)
    except Exception as e:
        print(f"An error occurred during analysis: {str(e)}")
