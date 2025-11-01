from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from qwen_oauth_to_openapi import get_openapi_credentials

# Get credentials
creds = get_openapi_credentials()

# Use OpenAILike instead of OpenAIChat
model = OpenAILike(
    id=creds['model'],
    api_key=creds['api_key'],
    base_url=creds['base_url']
)

# Create agent
agent = Agent(
    model=model,
    name="Dublin Expert",
    instructions=["You are a Dublin travel expert."],
    markdown=True,
    use_json_mode=True
    
)

# Test
response = agent.run("Tell me about Dublin's best pubs in json")
print(response.content)

