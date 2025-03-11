from portkey_ai import Portkey
import os
from dotenv import load_dotenv

load_dotenv()


config = {
    "cache": { 
        "mode": "semantic",
        "max_age": 10000,
    },
    "retry": { 
    "attempts": 3,
    },
    # "output_guardrails": [{
    #     "default.contains": {"operator": "none", "words": ["Apple"]},
    #     "deny": True
    # }],


     "strategy": {
      "mode": "loadbalance"
        },
	"targets": [
		{
			"provider": "openai",
			"api_key": os.getenv('OPENAI_API_KEY'),
			"weight": 0.60,
			"override_params": {
				"model": "gpt-4o-mini"
			}
		},
		{
			"provider": "groq",
			"api_key": os.getenv('GROQ_API_KEY'),
			"weight": 0.40,
			"override_params": {
				"model": "llama-3.3-70b-specdec"
			}
		}
	],
    "before_request_hooks": [{
        "id": "pg-guardr-592882"
    }],
    "after_request_hooks": [{
        "id": "pg-output-3b67c3"
    }],
}


# Calling OpenAI
# portkey = Portkey(
#     virtual_key=os.getenv('VIRTUAL_KEY_OPENAI')
#     config=config
# )

portkey = Portkey(
    provider="openai", # or 'anthropic', 'bedrock', 'groq', etc
    Authorization=os.getenv('OPENAI_API_KEY'),
    config=config
    # base_url="http://localhost:8787/public"
)

response = portkey.chat.completions.create(
  messages = [{ "role": 'user', "content": 'what is 1 plus 1' }],
  model = 'gpt-4o-mini'
)

print(response.choices[0].message.content)

