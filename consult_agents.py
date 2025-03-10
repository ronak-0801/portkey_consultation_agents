import warnings
warnings.filterwarnings('ignore')  # Suppress all warnings

import os
os.environ['PYTHONWARNINGS'] = 'ignore'  # Suppress warnings at environment level

from crewai import Agent, Task, Crew, Flow, Process, LLM
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
import yaml
import nbformat
from pydantic import BaseModel

# Output model for final report
class ReportOutput(BaseModel):
    content: str
    summary: str | None = None

# Load configuration files
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def save_as_notebook(content, file_path="final_report.ipynb"):
    """
    Converts content into a Jupyter Notebook and saves it.
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
    return file_path

def create_analysis_crew(subject, csv_path=None):
    """
    Creates a CrewAI setup for data analysis on the specified subject.
    
    Args:
        subject (str): The topic to analyze
        csv_path (str): Path to the CSV file to analyze
    """
    # Load configurations
    agents_config = load_config('agents.yml')
    tasks_config = load_config('tasks.yml')['tasks']
    
    # Convert relative path to absolute path
    if csv_path:
        csv_path = os.path.abspath(csv_path)
    else:
        csv_path = os.path.abspath("supermarket_sales - Sheet1.csv")
    
    # Verify file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    
    print(f"Using CSV file at: {csv_path}")
    
    # Configure LLMs
    gpt4_llm = LLM(
        provider="openai",
        model="gpt-4o-mini",
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
        model="gpt-4o-mini",
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=PORTKEY_GATEWAY_URL,
        extra_headers=createHeaders(
            api_key=os.getenv('PORTKEY_API_KEY'),
            virtual_key=os.getenv('VIRTUAL_KEY_OPENAI'),
            trace_id="gpt4_2"
        )
    )

    # Create tools with CSV path
    file_read_tool = FileReadTool(file_path=csv_path)
    file_writer_tool = FileWriterTool()
    csv_search_tool = CSVSearchTool(
        csv=csv_path
    )
    website_search_tool = WebsiteSearchTool()
    
    # Create search tools
    wikipedia = WikipediaAPIWrapper()
    wikipedia_tool = Tool(
        name="Wikipedia",
        description="Search Wikipedia articles",
        func=wikipedia.run
    )

    ddg_search = DuckDuckGoSearchRun()
    ddg_tool = Tool(
        name="DuckDuckGo Search",
        description="Search the web using DuckDuckGo",
        func=ddg_search.run
    )

    # Create agents
    data_architect = Agent(
        role=agents_config['data_architect']['role'],
        goal=agents_config['data_architect']['goal'],
        backstory=agents_config['data_architect']['backstory'],
        tools=[file_read_tool, file_writer_tool, csv_search_tool],
        llm=gemini_llm
    )

    analytical_engine = Agent(
        role=agents_config['analytical_engine']['role'],
        goal=agents_config['analytical_engine']['goal'],
        backstory=agents_config['analytical_engine']['backstory'],
        tools=[csv_search_tool, website_search_tool, wikipedia_tool],
        llm=gemini_llm
    )

    visualization_specialist = Agent(
        role=agents_config['visualization_specialist']['role'],
        goal=agents_config['visualization_specialist']['goal'],
        backstory=agents_config['visualization_specialist']['backstory'],
        tools=[file_read_tool, csv_search_tool, file_writer_tool],
        llm=gemini_llm
    )

    strategic_planner = Agent(
        role=agents_config['strategic_planner']['role'],
        goal=agents_config['strategic_planner']['goal'],
        backstory=agents_config['strategic_planner']['backstory'],
        tools=[website_search_tool, ddg_tool, wikipedia_tool, file_writer_tool],
        llm=gpt4_llm
    )

    # Update task descriptions with the subject
    for key in tasks_config:
        tasks_config[key]['description'] += f"\nSubject: {subject}"

    # Create tasks with proper dependencies
    data_acquisition_task = Task(
        description=tasks_config['data_acquisition']['description'].strip(),
        expected_output=tasks_config['data_acquisition']['expected_output'].strip(),
        agent=data_architect
    )

    data_cleaning_task = Task(
        description=tasks_config['data_cleaning_and_transformation']['description'].strip(),
        expected_output=tasks_config['data_cleaning_and_transformation']['expected_output'].strip(),
        agent=data_architect,
        context=[data_acquisition_task]
    )

    data_validation_task = Task(
        description=tasks_config['data_validation_and_quality_checks']['description'].strip(),
        expected_output=tasks_config['data_validation_and_quality_checks']['expected_output'].strip(),
        agent=data_architect,
        context=[data_cleaning_task]
    )

    data_analysis_task = Task(
        description=tasks_config['data_modeling_and_analysis']['description'].strip(),
        expected_output=tasks_config['data_modeling_and_analysis']['expected_output'].strip(),
        agent=analytical_engine,
        context=[data_validation_task]
    )

    dashboard_task = Task(
        description=tasks_config['interactive_dashboard_creation']['description'].strip(),
        expected_output=tasks_config['interactive_dashboard_creation']['expected_output'].strip(),
        agent=visualization_specialist,
        context=[data_analysis_task]
    )

    strategy_task = Task(
        description=tasks_config['strategic_recommendation_development']['description'].strip(),
        expected_output=tasks_config['strategic_recommendation_development']['expected_output'].strip(),
        agent=strategic_planner,
        context=[data_analysis_task, dashboard_task]
    )

    final_report_task = Task(
        description=tasks_config['final_report_generation']['description'].strip(),
        expected_output=tasks_config['final_report_generation']['expected_output'].strip(),
        agent=strategic_planner,
        context=[strategy_task, dashboard_task],
        output_pydantic=ReportOutput
    )

    # Define analysis workflow
    analysis_flow = Flow(
        name="Data Analysis Flow",
        description=f"Complete analysis workflow for: {subject}",
        tasks=[
            data_acquisition_task,
            data_cleaning_task, 
            data_validation_task,
            data_analysis_task,
            dashboard_task, 
            strategy_task,
            final_report_task
        ]
    )

    # Create the crew
    analysis_crew = Crew(
        agents=[data_architect, analytical_engine, visualization_specialist, strategic_planner],
        tasks=[
            data_acquisition_task,
            data_cleaning_task, 
            data_validation_task,
            data_analysis_task,
            dashboard_task, 
            strategy_task,
            final_report_task
        ],
        flows=[analysis_flow],
        verbose=True,
        process=Process.sequential  # Can be changed to hierarchical or parallel
    )

    return analysis_crew, final_report_task

def run_analysis(subject, csv_path=None):
    """
    Runs the analysis process using CrewAI and saves the output as a Jupyter Notebook.
    
    Args:
        subject (str): The topic to analyze.
        csv_path (str): Path to the CSV file to analyze
        
    Returns:
        str: Path to the generated Jupyter Notebook.
    """
    try:
        print(f"Starting analysis on: {subject}")
        print(f"Using CSV file: {csv_path}")
        
        # Create the crew and get the final task
        crew, final_task = create_analysis_crew(subject, csv_path)
        
        # Run the crew (this will execute all tasks in the proper order)
        result = crew.kickoff()
        
        # Save the output as a notebook
        notebook_path = save_as_notebook(result, "final_report.ipynb")
        
        print(f"Analysis completed successfully!")
        return notebook_path
        
    except Exception as e:
        import traceback
        print(f"❌ Error during analysis: {str(e)}")
        print("Error type:", type(e))
        print("Full traceback:")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Define the subject for analysis and CSV path
    subject = "Give me sales analysis of branch C"
    
    # Option 1: If CSV is in the same directory as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "supermarket_sales - Sheet1.csv")
    
    # Option 2: Or provide full path
    # csv_path = "/full/path/to/supermarket_sales - Sheet1.csv"
    
    # Run the analysis
    notebook_path = run_analysis(subject, csv_path)
    
    if notebook_path:
        print(f"\n=== Analysis Completed Successfully ===")
        print(f"Results saved to: {notebook_path}")
    else:
        print(f"\n=== Analysis Failed. Please check logs. ===")