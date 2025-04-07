# from langchain_community.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains.summarize import load_summarize_chain
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate

# class PDFProcessor:
#     def __init__(self, api_key):
#         self.api_key = api_key
#         self.llm_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=self.api_key)
#         self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
#         self.summary_chain = self._initialize_summary_chain()
    
#     def _initialize_summary_chain(self):
#         chunks_prompt = """
#         Please summarize the below Document. The summary must be very clear with proper phrases and easy words:
#         Document:`{text}'
#         Summary:
#         """
#         map_prompt_template = PromptTemplate(input_variables=['text'], template=chunks_prompt)
         
#         system_prompt = """
#         Your task is to carefully analyze the given text chunks and capture all the important details. 
#         Ensure that no information is missed and present everything in clear, continuous text.
#         """
#         human_prompt = "{text}"
        
#         final_combine_prompt = ChatPromptTemplate.from_messages([
#             SystemMessagePromptTemplate.from_template(system_prompt),
#             HumanMessagePromptTemplate.from_template(human_prompt)
#         ])
        
#         return load_summarize_chain(
#             llm=self.llm_model, 
#             chain_type='map_reduce', 
#             map_prompt=map_prompt_template, 
#             combine_prompt=final_combine_prompt,
#             verbose=False
#         )
    
#     def extract_text(self, file_path):
#         loader = PyPDFLoader(file_path)
#         pages = loader.load_and_split()
#         return "".join(page.page_content for page in pages)
    
#     def summarize(self, file_path):
#         full_text = self.extract_text(file_path)
#         chunks = self.text_splitter.create_documents([full_text])
#         result = self.summary_chain.invoke(chunks)
#         return result['input_documents'][0].page_content




from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate

class AsyncPDFProcessor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.llm_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=self.api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
        self.summary_chain = self._initialize_summary_chain()
    
    def _initialize_summary_chain(self):
        chunks_prompt = """
        Please summarize the below Document. The summary must be very clear with proper phrases and easy words:
        Document:`{text}`
        Summary:
        """
        map_prompt_template = PromptTemplate(input_variables=['text'], template=chunks_prompt)
         
        system_prompt = """
        Your task is to carefully analyze the given text chunks and capture all the important details. 
        Ensure that no information is missed and present everything in clear, continuous text.
        """
        human_prompt = "{text}"
        
        final_combine_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt)
        ])
        
        return load_summarize_chain(
            llm=self.llm_model, 
            chain_type='map_reduce', 
            map_prompt=map_prompt_template, 
            combine_prompt=final_combine_prompt,
            verbose=False
        )
    
    async def extract_text(self, file_path):
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        return "".join(page.page_content for page in pages)
    
    async def summarize(self, file_path):
        full_text = await self.extract_text(file_path)
        chunks = self.text_splitter.create_documents([full_text])
        result = await self.summary_chain.ainvoke(chunks)
        return result['output_text']

