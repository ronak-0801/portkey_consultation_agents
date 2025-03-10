from crewai import Agent, Task, Crew, Process
from crewai_tools import (
    SerperDevTool,
    FileReadTool,
    FileWriteTool,
    WebsiteSearchTool,
    DirectoryReadTool,
    DuckDuckGoSearchTool,
    WikipediaSearchTool
)
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize tools
search_tool = DuckDuckGoSearchTool()
wiki_tool = WikipediaSearchTool()
serper_tool = SerperDevTool(api_key=os.getenv('SERPER_API_KEY'))
web_search_tool = WebsiteSearchTool()
file_read_tool = FileReadTool()
file_write_tool = FileWriteTool()
directory_tool = DirectoryReadTool()

# Configure LLMs
gpt4_llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=os.getenv('OPENAI_API_KEY')
)

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.7,
    google_api_key=os.getenv('GOOGLE_API_KEY')
)

# Creating Agents
data_architect = Agent(
    role="Data Architect",
    goal="Gather, structure, and prepare data for analysis",
    backstory="""You are an experienced Data Architect with expertise in data collection,
    cleaning, and preparation. You ensure data quality and create efficient data structures.""",
    tools=[
        serper_tool,
        search_tool,
        web_search_tool,
        file_read_tool,
        file_write_tool
    ],
    llm=gemini_llm,
    verbose=True
)

analytical_engine = Agent(
    role="Analytical Engine",
    goal="Analyze data and extract meaningful insights",
    backstory="""You are an advanced analytical engine specialized in statistical analysis,
    pattern recognition, and data interpretation.""",
    tools=[
        serper_tool,
        wiki_tool,
        file_read_tool,
        directory_tool
    ],
    llm=gemini_llm,
    verbose=True
)

visualization_specialist = Agent(
    role="Visualization Specialist",
    goal="Create compelling and informative data visualizations",
    backstory="""You are a visualization expert who transforms complex data into
    clear, engaging, and interactive visual representations.""",
    tools=[
        search_tool,
        web_search_tool,
        file_write_tool
    ],
    llm=gemini_llm,
    verbose=True
)

strategic_planner = Agent(
    role="Strategic Planner",
    goal="Develop strategic recommendations based on analysis",
    backstory="""You are a strategic planning expert who transforms insights into
    actionable recommendations and strategic initiatives.""",
    tools=[
        serper_tool,
        wiki_tool,
        web_search_tool,
        file_read_tool,
        file_write_tool
    ],
    llm=gpt4_llm,
    verbose=True
)

def create_tasks(subject):
    """Create tasks for the analysis crew based on the subject."""
    
    data_acquisition_task = Task(
        description=f"""
        Gather comprehensive data about {subject}.
        Include market data, trends, and relevant statistics.
        Ensure data is from reliable sources and properly cited.
        Save the gathered data to a file for further processing.
        """,
        agent=data_architect
    )

    data_cleaning_task = Task(
        description=f"""
        Clean and prepare the gathered data about {subject}.
        Handle missing values, outliers, and standardize formats.
        Create a structured dataset ready for analysis.
        Save the cleaned data to a separate file.
        """,
        agent=data_architect,
        context=[data_acquisition_task]
    )

    data_analysis_task = Task(
        description=f"""
        Perform detailed analysis of the prepared data about {subject}.
        Include statistical analysis, trend identification, and pattern recognition.
        Generate key insights and findings.
        Document your analysis methodology and results.
        """,
        agent=analytical_engine,
        context=[data_cleaning_task]
    )

    dashboard_task = Task(
        description=f"""
        Create interactive visualizations for the analysis of {subject}.
        Include key metrics, trends, and comparative analyses.
        Ensure visualizations are clear, informative, and engaging.
        Save visualizations in appropriate formats.
        """,
        agent=visualization_specialist,
        context=[data_analysis_task]
    )

    strategy_task = Task(
        description=f"""
        Develop strategic recommendations based on the analysis of {subject}.
        Include actionable insights, risk assessment, and implementation guidelines.
        Consider market context and competitive landscape.
        Create a comprehensive strategic report.
        """,
        agent=strategic_planner,
        context=[data_analysis_task, dashboard_task]
    )

    return [
        data_acquisition_task,
        data_cleaning_task,
        data_analysis_task,
        dashboard_task,
        strategy_task
    ]

def run_analysis(subject):
    """
    Run the analysis crew with a specific subject.
    
    Args:
        subject (str): The subject or topic to analyze
    
    Returns:
        str: The results from the crew's analysis
    """
    try:
        # Create crew with tasks
        tasks = create_tasks(subject)
        
        crew = Crew(
            agents=[
                data_architect,
                analytical_engine,
                visualization_specialist,
                strategic_planner
            ],
            tasks=tasks,
            verbose=2,
            process=Process.sequential
        )

        # Start the crew with the task context
        result = crew.kickoff()
        
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
