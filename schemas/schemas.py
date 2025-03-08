from pydantic import BaseModel, Field
from typing import List

#Introduction
class Goals(BaseModel):
    Aims: str = Field(..., description="A detailed statement outlining the primary goal or vision of the document.")
    Objectives: List[str] = Field(..., description="A list of the main five key objectives that define the specific steps or milestones to achieve the main aim.")

class Introduction(BaseModel):
    MainTitle: str = Field(..., description="The main title of the document, which reflects the primary topic or subject matter covered within the document.")
    SubTitle: str = Field(..., description="A small one-line description supporting the main title.")
    Introduction: str = Field(..., description="""A brief overview or summary of the document, introducing its purpose, scope,
                             and any essential background information.The maximum length should be 100 words in a single paragraph.
                              Note that this length is based on the character count of the input text.""")
    Aims_Objectives: List[Goals] = Field(..., description="""Include the Aims and main five Objectives of the document. """)



# body

class BodySlides(BaseModel):
    Headings: str = Field(..., description="The title or heading for this slide, which introduces a specific section or topic within the slide content.")
    Bulletpoints: List[str] = Field(...,  description="""An list of bullet points that highlight key details
                                   or ideas related to the heading.Include only the main points,
                                   and provide well-explained, detailed points.""")

class Body(BaseModel):
    Pages: List[BodySlides] = Field(..., description="A list of slides, each containing a heading, description, and optional bullet points. This forms the body of the document.")


# conclusion
class Document(BaseModel):
    Summary: str = Field(..., description="A concise summary that highlights the key points, findings, or conclusions drawn from the document.")

class Conclusion(BaseModel):
    FinalSummary: Document = Field(..., description="The conclusion section of the document, which summarizes the content, provides recommendations, and offers final thoughts.")

#Final PPT
class FinalPPT(BaseModel):
    Introduction_: Introduction = Field(..., description="The introduction section of the document, including the main title, introduction, and aims/objectives if relevant.")
    Body_: Body = Field(..., description="The body section of the document, containing slides with headings, descriptions, and optional bullet points.")
    Conclusion_: Conclusion = Field(..., description="The conclusion section of the document, summarizing key points, recommendations, and final thoughts.")
