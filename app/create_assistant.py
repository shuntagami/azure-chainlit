from openai import AsyncAzureOpenAI
from settings import Config
import asyncio

async def main():
    openai_client = AsyncAzureOpenAI(
        api_key=Config.OPENAI_API_KEY,
        azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
        api_version=Config.OPENAI_API_VERSION,
    )

    instructions = """You are an assistant running data analysis on CSV files.

    You will use code interpreter to run the analysis.

    However, instead of rendering the charts as images, you will generate a plotly figure and turn it into json.
    You will create a file for each json that I can download through annotations.
    """

    tools = [{"type": "code_interpreter"}, {"type": "file_search"}]

    file = await openai_client.files.create(
        file=open("tesla-stock-price.csv", "rb"), purpose="assistants"
    )

    assistant = await openai_client.beta.assistants.create(
        model="gpt-35-turbo",
        name="Data Analysis Assistant",
        instructions=instructions,
        temperature=0.1,
        tools=tools,
        tool_resources={"code_interpreter": {"file_ids": [file.id]}},
    )

    print(f"Assistant created with id: {assistant.id}")

if __name__ == "__main__":
    asyncio.run(main())
