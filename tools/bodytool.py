import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from schemas.schemas import Body
load_dotenv()

# Access the variables
api_key = os.getenv("GOOGLE_API_KEY")

def giveBody(content: str) -> dict:
    """
    This tool generates the body from the content given by the user.

    Args:
    content: This is the text content which is a document.
    """

    # Initialize the LLM model
    llm2 = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

    # Structured output for Body
    structured_llm2 = llm2.with_structured_output(Body)

    # Define the chat template
    chat_template2 = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant designed to analyze the text given by the user and provide the title, body based on the user-provided schema."),
            ("human", "From the below text, analyze properly and provide the proper body part:\n{text}")
        ]
    )

    # Combine the chat template with structured output
    llm_f2 = chat_template2 | structured_llm2

    # Get the result from the model
    result2 = llm_f2.invoke({"text": content})

    # Return the result
    return {"Body": result2.model_dump()}
