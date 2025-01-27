from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, Date, TIMESTAMP, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Database URL (update credentials accordingly)
DATABASE_URL = "mysql+pymysql://root:@127.0.0.1/edusync"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Models
class Assignment(Base):
    __tablename__ = 'assignment'

    assignment_id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey('teacher.teacher_id'), nullable=True)
    class_id = Column(Integer, ForeignKey('classroom.class_id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('subject.subject_id'), nullable=True)
    assignment_title = Column(String(255), nullable=True)
    assignment_description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    link = Column(Text, nullable=False)

    teacher = relationship("Teacher", back_populates="assignments")
    classroom = relationship("Classroom", back_populates="assignments")
    subject = relationship("Subject", back_populates="assignments")


class Classroom(Base):
    __tablename__ = 'classroom'

    class_id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(255), nullable=False)

    assignments = relationship("Assignment", back_populates="classroom")
    students = relationship("Student", back_populates="classroom")
    teacher_classes = relationship("TeacherClass", back_populates="classroom")


class ClassSubject(Base):
    __tablename__ = 'class_sub'

    class_subject_id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey('classroom.class_id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('subject.subject_id'), nullable=True)


class Comment(Base):
    __tablename__ = 'comments'

    comment_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=True)
    content = Column(Text, nullable=True)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Like(Base):
    __tablename__ = 'likes'

    like_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.post_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=False)


class Post(Base):
    __tablename__ = 'post'

    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('subject.subject_id'), nullable=True)
    class_id = Column(Integer, ForeignKey('classroom.class_id'), nullable=True)
    post_content = Column(Text, nullable=True)
    post_date = Column(TIMESTAMP, nullable=False, default=func.now())
    filelink = Column(Text, nullable=False)

    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Student(Base):
    __tablename__ = 'student'

    student_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=True)
    class_id = Column(Integer, ForeignKey('classroom.class_id'), nullable=True)

    user = relationship("User", back_populates="student")
    classroom = relationship("Classroom", back_populates="students")


class Subject(Base):
    __tablename__ = 'subject'

    subject_id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(255), nullable=False)

    assignments = relationship("Assignment", back_populates="subject")


class Submission(Base):
    __tablename__ = 'submission'

    submission_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('assignment.assignment_id'), nullable=True)
    student_id = Column(Integer, ForeignKey('student.student_id'), nullable=True)
    submission_date = Column(TIMESTAMP, nullable=False, default=func.now())
    file_path = Column(String(255), nullable=True)
    remarks = Column(Text, nullable=True)


class Teacher(Base):
    __tablename__ = 'teacher'

    teacher_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id'), nullable=True)

    user = relationship("User", back_populates="teacher")
    assignments = relationship("Assignment", back_populates="teacher")


class TeacherClass(Base):
    __tablename__ = 'teacher_class'

    tc_id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey('teacher.teacher_id'), nullable=True)
    class_id = Column(Integer, ForeignKey('classroom.class_id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('subject.subject_id'), nullable=True)

    classroom = relationship("Classroom", back_populates="teacher_classes")


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    number = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(Enum('teacher', 'student'), nullable=False)

    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    student = relationship("Student", uselist=False, back_populates="user")
    teacher = relationship("Teacher", uselist=False, back_populates="user")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()