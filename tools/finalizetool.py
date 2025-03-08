import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from schemas.schemas import FinalPPT
from state.state import ContentState
load_dotenv()

# Access the variables
api_key = os.getenv("GOOGLE_API_KEY")

def Finalize(state : ContentState) -> dict:
    """
    This tool checks if the given content contains any duplicated text, concepts, or ideas without modifying the content.

    Args:
    state: A structured result indicating whether duplication exists in the document.

    """

    # Initialize the LLM model
    llm4 = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

    # Structured output for duplication check
    structured_llm4 = llm4.with_structured_output(FinalPPT)

    # Define the chat template
    chat_template4 = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant designed to analyze the text given by the user and check if it contains duplicated concepts or ideas."),
            ("human", "From the below text, analyze it properly and determine if any duplicated concepts are present. Do not modify the content, just indicate whether duplication exists:\n{text}")
        ]
    )

    # Combine the chat template with structured output
    llm_f4 = chat_template4 | structured_llm4

    def join_dict_values(d):
      if isinstance(d, dict):
          return " ".join(join_dict_values(v) for v in d.values())
      elif isinstance(d, list):
          return " ".join(join_dict_values(v) for v in d)
      elif isinstance(d, str):
          return d
      else:
          return ""

    outputt=[state['Introduction'],state['Body'],state['Conclusion']]

    # Join all values into a single string
    content = " ".join(join_dict_values(d) for d in outputt)

    # Get the result from the model
    result4 = llm_f4.invoke({"text": content})

    # Return the result
    return {"FinalResult": result4.model_dump()}
