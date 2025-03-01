import re
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate

class SummarizePDF:
    def __init__(self, pdf_path, api_key):
        self.pdf_path = pdf_path
        self.llm_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        self.chunks = []
    
    def doc_words_join(self):
        loader = PyPDFLoader(self.pdf_path)
        pages = loader.load_and_split()
        whole_doc_text = ''
        for i in range(len(pages)):
            whole_doc_text += pages[i].page_content
        return whole_doc_text

    def split_text(self, text):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
        self.chunks = text_splitter.create_documents([text])
    
    def generate_summary_and_topics(self):
        chunks_prompt = """
        Please summarize the below Document. The summary must be very clear with proper phrases and easy words:
        Document:`{text}'
        Summary:
        """
        
        map_prompt_template = PromptTemplate(input_variables=['text'], template=chunks_prompt)
        
        system =  """Identify the key topics from the provided text and structure them as follows:

                    - **Introduction:** A brief overview of the topic.  
                    - **Description:** A concise explanation covering essential details.  
                    - **Key Points:** A bullet-point list highlighting the most important aspects.  

                    Ensure that each topic captures the most critical elements of the document. Keep descriptions clear, precise, and free of unnecessary elaboration.  

                    Note: Do not include any introductory text or preamble in the output."""
        
        human = "{text}"

        final_combine_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system),
            HumanMessagePromptTemplate.from_template(human)
        ])
        
        summary_chain = load_summarize_chain(
            llm=self.llm_model, 
            chain_type='map_reduce', 
            map_prompt=map_prompt_template, 
            combine_prompt=final_combine_prompt,
            verbose=False
        )
        
        output = summary_chain.invoke(self.chunks)
        self.output_text = output['output_text']
        return self.output_text
    
    def run(self):
        allwords = self.doc_words_join()
        self.split_text(allwords)
        return self.generate_summary_and_topics()

