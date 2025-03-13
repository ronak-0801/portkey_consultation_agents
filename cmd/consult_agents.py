import json
from crewai import Agent, Process, Task, Crew, LLM
from crewai_tools.tools import FileReadTool
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
import os
from slack_config import send_slack_message
import uuid




config = {
    "cache": { 
        "mode": "semantic",
        "max_age": 10000,
    },
    "retry": { 
    "attempts": 3,
    "on_status_codes": [404,429,500,502,503,504]
    },
    "before_request_hooks": [{
		"id": "pg-guardr-592882"
	}],
    "strategy": {
      "mode": "loadbalance"
    },
	"targets": [
		{
			"provider": "openai",
            # "virtual_key": os.getenv('VIRTUAL_KEY_OPENAI'),
			"api_key": os.getenv('OPENAI_API_KEY'),
			"weight": 1,
			"override_params": {
				"model": "gpt-4o-mini"
			}
		},
		{
			"provider": "groq",
            # "virtual_key": os.getenv('VIRTUAL_KEY_GROQ'),
			"api_key": os.getenv('GROQ_API_KEY'),
			"weight": 0,
			"override_params": {
				"model": "llama-3.3-70b-specdec"
			}
		}
	]
    # "strategy": {
    #   "mode": "fallback"
    # },
    # "targets": [
    #     {
    #         "provider": "openai",
    #         "virtual_key": "openai-c8972a",
    #         "override_params": {
    #             "model": "gpt-4o-mini"
    #         }
    #     }
    # ]   

}



llm = LLM(
    provider="openai",
    model="gpt-4o-mini",
    base_url="http://localhost:8787/v1",
    extra_headers=createHeaders(
        api_key=os.getenv('PORTKEY_API_KEY'),
        # virtual_key=os.getenv('VIRTUAL_KEY_OPENAI'),
        trace_id=str(uuid.uuid4()),
        config=json.dumps(config)
    )
)

csv_tool = FileReadTool(file_path='supermarket_sales - Sheet1.csv')


dataset_inference_agent = Agent(
    role="Dataset Context Specialist",
    goal=(
        "Perform an exhaustive analysis of the dataset to understand its full context and business implications. "
        "Extract detailed insights about sales patterns, customer behavior, and business performance metrics. "
        "Identify key business KPIs and potential areas for optimization."
    ),
    backstory=(
        "You are a senior data scientist with extensive experience in retail analytics and business intelligence. "
        "Your expertise lies in transforming raw data into actionable business insights, with a particular focus "
        "on customer behavior analysis and sales performance optimization."
    ),
    tools=[csv_tool],
    llm=llm,
    verbose=True
)


data_analysis_agent = Agent(
    role="Data Analysis Specialist",
    goal=(
        "Conduct a comprehensive statistical analysis of the dataset including:\n"
        "• Detailed distribution analysis of all numerical variables\n"
        "• Advanced correlation analysis between different metrics\n"
        "• Time-based trend analysis of sales and customer behavior\n"
        "• Customer segmentation analysis\n"
        "• Product performance analysis\n"
        "• Payment method analysis and its impact on sales\n"
        "• Branch performance comparison\n"
        "Generate both summary and detailed statistics for all key metrics."
    ),
    backstory=(
        "You are an expert data analyst with deep expertise in retail analytics and statistical analysis. "
        "You excel at finding hidden patterns in data and presenting complex analytical findings in a clear, "
        "actionable format. Your analysis has helped numerous retail businesses optimize their operations."
    ),
    tools=[csv_tool],
    llm=llm,
    verbose=True
)


visualization_agent = Agent(
    role="Advanced Visualization Specialist",
    goal=(
        "Create a comprehensive suite of visualizations that tell a complete story about the business, including:\n"
        "• Sales trends over time with seasonal patterns\n"
        "• Customer segmentation and behavior patterns\n"
        "• Product performance analysis\n"
        "• Branch comparison visualizations\n"
        "• Payment method impact analysis\n"
        "• Correlation matrices for all relevant metrics\n"
        "• Distribution plots for key variables\n"
        "Save all visualizations in high resolution in the 'graphs/' directory with clear naming conventions."
    ),
    backstory=(
        "You are a visualization expert with extensive experience in business intelligence and data storytelling. "
        "Your expertise spans multiple visualization libraries including matplotlib, seaborn, and plotly. "
        "You know how to create compelling visual narratives that drive business decisions."
    ),
    tools=[csv_tool],
    llm=llm,
    verbose=True,
    allow_delegation=True,
    allow_code_execution=True 
)


markdown_report_agent = Agent(
    role="Executive Report Specialist",
    goal=(
        "Create a comprehensive, executive-level report that includes:\n"
        "• Detailed executive summary\n"
        "• In-depth analysis of all key business metrics\n"
        "• Customer behavior insights\n"
        "• Product performance analysis\n"
        "• Branch comparison results\n"
        "• Clear actionable recommendations\n"
        "• Future optimization opportunities\n"
        "Ensure all visualizations are properly embedded and explained in context."
    ),
    backstory=(
        "You are a senior business analyst who specializes in creating executive-level reports. "
        "Your reports are known for being comprehensive yet clear, combining data-driven insights "
        "with actionable business recommendations. You excel at presenting complex analysis in a "
        "format that drives decision-making."
    ),
    tools=[csv_tool],
    llm=llm,
    verbose=True
)


dataset_inference_task = Task(
    description="Analyze the dataset to determine its context, purpose, and structure.",
    expected_output="A descriptive overview of the dataset's structure and purpose.",
    agent=dataset_inference_agent
)

data_analysis_task = Task(
    description="Perform a comprehensive analysis of the dataset to identify missing values, incorrect data types, and potential outliers.",
    expected_output="A summary of missing values, standardized data types, and statistical metrics.",
    agent=data_analysis_agent
)

visualization_task = Task(
    description=(
        "Load the dataset and generate visualizations using matplotlib and seaborn. "
        "Save all visualizations as PNG files in the 'graphs/' directory. "
        "Use appropriate titles and labels for clarity."
    ),
    expected_output="A set of annotated graphs saved in the 'graphs/' directory.",
    agent=visualization_agent
)


markdown_report_task = Task(
    description=(
        "Create a detailed markdown report summarizing all analysis and visualizations. "
        "Ensure that images from the 'graphs/' directory are embedded using Markdown syntax like:\n"
        "\n"
        "![Graph Title](graphs/filename.png)"
    ),
    expected_output="A polished markdown report with embedded graphs and actionable insights.",
    agent=markdown_report_agent,
    context=[dataset_inference_task, data_analysis_task, visualization_task],
    output_file='report.md'
)


csv_analysis_crew = Crew(
    agents=[
        dataset_inference_agent,
        data_analysis_agent,
        visualization_agent,
        markdown_report_agent
    ],
    tasks=[dataset_inference_task, data_analysis_task, visualization_task, markdown_report_task],
    process=Process.sequential,
    verbose=True
)


    
if __name__ == "__main__":
    subject = "Analysis of market trends in the renewable energy sector for 2024"
    
    results = csv_analysis_crew.kickoff()
    
    if results:
        print("\n=== Analysis Completed Successfully ===")
        print(results)
        
        # Format the results into a readable message
        slack_message = (
            "🎉 *Supermarket Sales Analysis Completed Successfully*\n\n"
            "The analysis report has been generated with:\n"
            "• Statistical analysis\n"
            "• Data visualizations\n"
            "• Actionable insights\n\n"
            f"*Analysis Results*:\n```{str(results)}```\n\n"
            "📊 Check the `graphs/` directory for visualizations\n"
            "📝 Full report available in `report.md`"
        )
        
        slack_response = send_slack_message(slack_message)
        if slack_response and slack_response.get('ok'):
            print("Successfully sent results to Slack")
        else:
            print("Failed to send results to Slack:", slack_response.get('error') if slack_response else "No response")
    else:
        print("\n=== Analysis Failed. Please check logs. ===")
        # Send failure notification to Slack
        send_slack_message("❌ Supermarket Sales Analysis failed. Please check the logs.")
