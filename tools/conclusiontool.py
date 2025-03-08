import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from schemas.schemas import Conclusion
load_dotenv()

# Access the variables
api_key = os.getenv("GOOGLE_API_KEY")

def giveConclusion(content: str) -> dict:
    """
    This tool generates the conclusion from the content given by the user.

    Args:
    content: This is the text content which is a document.
    """

    # Initialize the LLM model
    llm3 = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

    # Structured output for Conclusion
    structured_llm3 = llm3.with_structured_output(Conclusion)

    # Define the chat template
    chat_template3 = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant designed to analyze the text given by the user and provide the title, conclusion based on the user-provided schema."),
            ("human", "From the below text, analyze properly and provide the proper conclusion part:\n{text}")
        ]
    )

    # Combine the chat template with structured output
    llm_f3 = chat_template3 | structured_llm3

    # Get the result from the model
    result3 = llm_f3.invoke({"text": content})

    # Return the result
    return {"Conclusion": result3.model_dump()}
