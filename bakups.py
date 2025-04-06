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
    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))
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




@router.post("/generatemcq", response_class=HTMLResponse)
async def GenerateMcqPage(
    pdf_file: UploadFile = File(...),
    subject_id: str = Form(...),
    subject: str = Form(...),
    class_id: str = Form(...),
    is_auth= Depends(auth_required),
    is_allowed= Depends(teacherAllowed),
):
    # Create the directory if it doesn't exist
    directory_path = f"static/PDFProcessing/{class_id}/{subject_id}/{subject}"
    os.makedirs(directory_path, exist_ok=True)

    # Ensure a clean filename
    safe_filename = pdf_file.filename.replace("\\", "_").replace("/", "_")
    file_location = os.path.join(directory_path, safe_filename)

    # Save uploaded PDF file
    with open(file_location, "wb") as file:
        file.write(await pdf_file.read())

    # Generate MCQs from PDF
    api_key = os.getenv("GOOGLE_API_KEY")
    mcq_generator = PDFMCQGenerator(file_location, api_key)
    textout = await mcq_generator.run()  # <-- ✅ AWAIT the async call

    # Clean up uploaded file
    directory = os.path.dirname(file_location)
    if os.path.exists(directory):
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    # Redirect with query params
    query_params = f"?subject_id={subject_id}&subject={subject}&class_id={class_id}&mcq_output={textout}"
    return RedirectResponse(url=f"/mcq/generatemcq{query_params}", status_code=303)