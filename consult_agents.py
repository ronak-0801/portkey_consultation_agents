from crewai import Agent, Task, Crew, Flow, LLM
from crewai_tools.tools import (
    FileReadTool,
    FileWriterTool,
    CSVSearchTool,
    WebsiteSearchTool
)
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from portkey_ai import Portkey, PORTKEY_GATEWAY_URL, createHeaders
import os
import yaml
import nbformat
from pydantic import BaseModel

# Add this class near the top of the file, after imports
class ReportOutput(BaseModel):
    content: str
    summary: str | None = None

# Load configuration files
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Load configurations
agents_config = load_config('agents.yml')
tasks_config = load_config('tasks.yml')['tasks']


# Update the LLM configuration
gpt4_llm = LLM(
    provider="openai",
    model="gpt-4o-mini",     # Changed to gpt-4o-mini
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=PORTKEY_GATEWAY_URL,
    extra_headers=createHeaders(
        api_key=os.getenv('PORTKEY_API_KEY'),
        virtual_key=os.getenv('VIRTUAL_KEY_OPENAI'),
        trace_id="gpt4"
    )
)

gemini_llm = LLM(
    provider="openai",
    model="gpt-4o-mini",     # Changed to gpt-4o-mini
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=PORTKEY_GATEWAY_URL,
    extra_headers=createHeaders(
        api_key=os.getenv('PORTKEY_API_KEY'),
        virtual_key=os.getenv('VIRTUAL_KEY_OPENAI'),
        trace_id="gpt4_2"
    )
)

# Creating Agents with essential tools
data_architect = Agent(
    role=agents_config['data_architect']['role'],
    goal=agents_config['data_architect']['goal'],
    backstory=agents_config['data_architect']['backstory'],
    tools=[
        FileReadTool(),
        FileWriterTool(),
        CSVSearchTool(),
    ],
    llm=gemini_llm
)

# Create Wikipedia tool
wikipedia = WikipediaAPIWrapper()
wikipedia_tool = Tool(
    name="Wikipedia",
    description="Search Wikipedia articles",
    func=wikipedia.run
)

# Create search tools
ddg_search = DuckDuckGoSearchRun()
ddg_tool = Tool(
    name="DuckDuckGo Search",
    description="Search the web using DuckDuckGo",
    func=ddg_search.run
)

analytical_engine = Agent(
    role=agents_config['analytical_engine']['role'],
    goal=agents_config['analytical_engine']['goal'],
    backstory=agents_config['analytical_engine']['backstory'],
    tools=[
        CSVSearchTool(),
        WebsiteSearchTool(),
        wikipedia_tool
    ],
    llm=gemini_llm
)

visualization_specialist = Agent(
    role=agents_config['visualization_specialist']['role'],
    goal=agents_config['visualization_specialist']['goal'],
    backstory=agents_config['visualization_specialist']['backstory'],
    tools=[
        FileReadTool(),
        CSVSearchTool(),
        FileWriterTool()
    ],
    llm=gemini_llm
)

strategic_planner = Agent(
    role=agents_config['strategic_planner']['role'],
    goal=agents_config['strategic_planner']['goal'],
    backstory=agents_config['strategic_planner']['backstory'],
    tools=[
        WebsiteSearchTool(),
        ddg_tool,
        wikipedia_tool,
        FileWriterTool()
    ],
    llm=gpt4_llm
)

# Creating Tasks
data_acquisition_task = Task(
    description=str(tasks_config['data_acquisition']['description']).strip(),  # Convert to string and strip whitespace
    expected_output=str(tasks_config['data_acquisition']['expected_output']).strip(),
    agent=data_architect
)

data_cleaning_task = Task(
    description=str(tasks_config['data_cleaning_and_transformation']['description']).strip(),
    expected_output=str(tasks_config['data_cleaning_and_transformation']['expected_output']).strip(),
    agent=data_architect,
    context=[data_acquisition_task]
)

data_analysis_task = Task(
    description=str(tasks_config['data_modeling_and_analysis']['description']).strip(),
    expected_output=str(tasks_config['data_modeling_and_analysis']['expected_output']).strip(),
    agent=analytical_engine,
    context=[data_cleaning_task]
)

dashboard_task = Task(
    description=str(tasks_config['interactive_dashboard_creation']['description']).strip(),
    expected_output=str(tasks_config['interactive_dashboard_creation']['expected_output']).strip(),
    agent=visualization_specialist,
    context=[data_analysis_task]
)

strategy_task = Task(
    description=str(tasks_config['strategic_recommendation_development']['description']).strip(),
    expected_output=str(tasks_config['strategic_recommendation_development']['expected_output']).strip(),
    agent=strategic_planner,
    context=[data_analysis_task, dashboard_task]
)

final_report_task = Task(
    description=str(tasks_config['final_report_generation']['description']).strip(),
    expected_output=str(tasks_config['final_report_generation']['expected_output']).strip(),
    agent=strategic_planner,
    context=[strategy_task, dashboard_task],
    output_pydantic=ReportOutput
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

def save_as_notebook(content, file_path="final_report.ipynb"):
    """
    Converts content into a Jupyter Notebook and saves it.

    Args:
        content (str): The markdown or structured content from the AI pipeline.
        file_path (str): The output notebook filename.
    """
    notebook = nbformat.v4.new_notebook()
    
    # Handle both string and ReportOutput types
    content_str = content.content if isinstance(content, ReportOutput) else content
    
    # Create a Markdown cell for the report
    markdown_cell = nbformat.v4.new_markdown_cell(content_str)
    
    # Optional: Add a code cell
    code_cell = nbformat.v4.new_code_cell("print('Notebook Generated Successfully')")

    # Append cells to the notebook
    notebook.cells.extend([markdown_cell, code_cell])

    # Save as an .ipynb file
    with open(file_path, "w") as f:
        nbformat.write(notebook, f)

    print(f"✅ Notebook saved as {file_path}")

def run_analysis(subject):
    """
    Runs the analysis process and saves the final output as a Jupyter Notebook.

    Args:
        subject (str): The topic to analyze.

    Returns:
        str: Path to the generated Jupyter Notebook.
    """
    try:
        print("Starting analysis with subject:", subject)
        
        # Update task descriptions with the subject
        for task in [data_acquisition_task, data_cleaning_task, data_analysis_task, 
                    dashboard_task, strategy_task, final_report_task]:
            if not task.description.endswith(f"Subject: {subject}"):
                task.description += f"\nSubject: {subject}"
        
        print("Tasks updated with subject")
        
        # Direct execution of tasks without using Crew or Flow
        print("Starting direct task execution...")
        
        # Execute data acquisition task
        print("Executing data acquisition task...")
        data_acquisition_output = data_architect.execute_task(data_acquisition_task)
        print("Data acquisition completed")
        
        # Execute data cleaning task with context
        print("Executing data cleaning task...")
        data_cleaning_task.context = [data_acquisition_output]
        data_cleaning_output = data_architect.execute_task(data_cleaning_task)
        print("Data cleaning completed")
        
        # Execute data analysis task with context
        print("Executing data analysis task...")
        data_analysis_task.context = [data_cleaning_output]
        data_analysis_output = analytical_engine.execute_task(data_analysis_task)
        print("Data analysis completed")
        
        # Execute dashboard creation task with context
        print("Executing dashboard creation task...")
        dashboard_task.context = [data_analysis_output]
        dashboard_output = visualization_specialist.execute_task(dashboard_task)
        print("Dashboard creation completed")
        
        # Execute strategy development task with context
        print("Executing strategy task...")
        strategy_task.context = [data_analysis_output, dashboard_output]
        strategy_output = strategic_planner.execute_task(strategy_task)
        print("Strategy development completed")
        
        # Execute final report generation task with context
        print("Executing final report task...")
        final_report_task.context = [strategy_output, dashboard_output]
        final_output = strategic_planner.execute_task(final_report_task)
        print("Final report generation completed")
        
        # Save the final output as a Jupyter Notebook
        notebook_path = "final_report.ipynb"
        save_as_notebook(final_output, notebook_path)
        print(f"Final report saved to {notebook_path}")
        
        return notebook_path

    except Exception as e:
        import traceback
        print(f"❌ Error during analysis: {str(e)}")
        print("Error type:", type(e))
        print("Full traceback:")
        print(traceback.format_exc())
        return None
    
if __name__ == "__main__":
    subject = "Analysis of market trends in the renewable energy sector for 2024"
    
    results = run_analysis(subject)
    
    if results:
        print("\n=== Analysis Completed Successfully ===")
        print(results)
    else:
        print("\n=== Analysis Failed. Please check logs. ===")
