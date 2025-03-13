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
    "strategy": {
      "mode": "loadbalance"
    },
	"targets": [
		{
			"provider": "openai",
			"virtual_key": os.getenv("VIRTUAL_KEY_OPENAI"),
			"weight": 0.10,
			"override_params": {
				"model": "gpt-4o-mini"
			}
		},
		{
			"provider": "groq",
			"virtual_key": os.getenv("VIRTUAL_KEY_GROQ"),
			"weight": 0.90,
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
portkey = Portkey(
    virtual_key=os.getenv('VIRTUAL_KEY_OPENAI'),
    config=config
)

response = portkey.chat.completions.create(
  messages = [{ "role": 'user', "content": 'Write a greeting msg in one line' }],
  model = 'gpt-4o-mini'
)

print(response.choices[0].message.content)