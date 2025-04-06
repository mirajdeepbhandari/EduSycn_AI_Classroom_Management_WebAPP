# import re
# from langchain_community.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.chains.summarize import load_summarize_chain
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
# from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate

# class PDFMCQGenerator:
#     def __init__(self, pdf_path, api_key):
#         self.pdf_path = pdf_path
#         self.llm_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
#         self.chunks = []
    
#     def doc_words_join(self):
#         loader = PyPDFLoader(self.pdf_path)
#         pages = loader.load_and_split()
#         whole_doc_text = ''
#         for i in range(len(pages)):
#             whole_doc_text += pages[i].page_content
#         return whole_doc_text

#     def split_text(self, text):
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
#         self.chunks = text_splitter.create_documents([text])
    
#     def generate_summary_and_mcqs(self):
#         chunks_prompt = """
#         Please summarize the below Document. The summary must be very clear with proper phrases and easy words:
#         Document:`{text}'
#         Summary:
#         """
        
#         map_prompt_template = PromptTemplate(input_variables=['text'], template=chunks_prompt)
        
#         system = """
#         You are tasked with generating a minimum of 20 multiple-choice questions (MCQs) based on the provided text. Each MCQ should be well-structured and follow the format below:

#         Question: [Clearly state the question in a concise and understandable manner.]
#         Options:
#         A) [Option 1]
#         B) [Option 2]
#         C) [Option 3]
#         D) [Option 4]
#         Correct Answer: [Specify the correct option]

#         Ensure that questions assess key concepts, facts, or inferences from the text. Options should be plausible and not overly obvious. Avoid ambiguous wording and ensure that each question has only one correct answer. Provide a mix of factual, conceptual, and application-based questions. Each question should be self-contained and understandable without additional context.

#         i wnat like this

#         **Question X:**
#         [Insert question here]
#         Options:
#         A) [Option A]
#         B) [Option B]
#         C) [Option C]
#         D) [Option D]

#         Correct Answer: [Correct option letter]


#         Note: Do not include any preamble. """

#         human = "{text}"

#         final_combine_prompt = ChatPromptTemplate.from_messages([
#             SystemMessagePromptTemplate.from_template(system),
#             HumanMessagePromptTemplate.from_template(human)
#         ])
        
#         summary_chain = load_summarize_chain(
#             llm=self.llm_model, 
#             chain_type='map_reduce', 
#             map_prompt=map_prompt_template, 
#             combine_prompt=final_combine_prompt,
#             verbose=False
#         )
        
#         output = summary_chain.invoke(self.chunks)
#         self.output_text = output['output_text']
#         return self.output_text
    
#     def run(self):
#         allwords = self.doc_words_join()
#         self.split_text(allwords)
#         return self.generate_summary_and_mcqs()



import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from tenacity import retry, wait_exponential, stop_after_attempt


class PDFMCQGenerator:
    def __init__(self, pdf_path, api_key):
        self.pdf_path = pdf_path
        self.llm_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        self.chunks = []

    async def doc_words_join(self):
        loader = PyPDFLoader(self.pdf_path)
        pages = loader.load_and_split()
        return ''.join([page.page_content for page in pages])

    def split_text(self, text):
        splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
        self.chunks = splitter.create_documents([text])

    def get_summary_chain(self):
        summary_prompt = """
        Please summarize the below Document. The summary must be very clear with proper phrases and easy words:
        Document:`{text}`
        Summary:
        """

        map_prompt_template = PromptTemplate(input_variables=['text'], template=summary_prompt)

        mcq_system_prompt = """
        You are tasked with generating a minimum of 20 multiple-choice questions (MCQs) based on the provided text. Each MCQ should be well-structured and follow the format below:

        **Question X:**
        [Insert question here]
        Options:
        A) [Option A]
        B) [Option B]
        C) [Option C]
        D) [Option D]

        Correct Answer: [Correct option letter]

        Ensure that questions assess key concepts, facts, or inferences from the text. Options should be plausible and not overly obvious. Avoid ambiguous wording and ensure that each question has only one correct answer. Provide a mix of factual, conceptual, and application-based questions. Each question should be self-contained and understandable without additional context.

        Note: Do not include any preamble.
        """

        human_template = "{text}"

        final_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(mcq_system_prompt),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

        return load_summarize_chain(
            llm=self.llm_model,
            chain_type='map_reduce',
            map_prompt=map_prompt_template,
            combine_prompt=final_prompt,
            return_intermediate_steps=False,
            verbose=False
        )

    # Retry mechanism for API rate limits, temporary failures
    # @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
    async def run_summary_chain(self, chain):
        return await chain.ainvoke(self.chunks)

    async def run(self):
        try:
            content = await self.doc_words_join()
            self.split_text(content)
            chain = self.get_summary_chain()
            result = await self.run_summary_chain(chain)
            return result['output_text']
        except Exception as e:
            return f"Error: {e}"
