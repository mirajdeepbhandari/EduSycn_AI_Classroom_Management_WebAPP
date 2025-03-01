from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, Enum, ForeignKey, Date, TIMESTAMP, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Database URL (update credentials accordingly)
DATABASE_URL = "mysql+pymysql://root:@127.0.0.1/edusync_f"

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
    teacher_id = Column(Integer, ForeignKey('teacher.teacher_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('classroom.class_id',ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.subject_id',ondelete='CASCADE'), nullable=False)
    assignment_title = Column(String(255), nullable=False)
    assignment_description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    link = Column(Text, nullable=False)




class Classroom(Base):
    __tablename__ = 'classroom'

    class_id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(255), nullable=False)


class ClassSubject(Base):
    __tablename__ = 'class_sub'

    class_subject_id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey('classroom.class_id', ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.subject_id', ondelete='CASCADE'), nullable=False)


class Comment(Base):
    __tablename__ = 'comments'

    comment_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.post_id', ondelete='CASCADE'), nullable=False) 
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=True)


class Like(Base):
    __tablename__ = 'likes'

    like_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.post_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)


class Post(Base):
    __tablename__ = 'post'

    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id',ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.subject_id',ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('classroom.class_id',ondelete='CASCADE'), nullable=False)
    post_content = Column(Text, nullable=False)
    post_date = Column(TIMESTAMP, nullable=False, default=func.now())
    filelink = Column(Text, nullable=False)


class Student(Base):
    __tablename__ = 'student'

    student_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id',ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('classroom.class_id',ondelete='CASCADE'), nullable=False)
    is_notifyread = Column(String(10), nullable=False, default='no')



class Subject(Base):
    __tablename__ = 'subject'

    subject_id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(255), nullable=False)
 


class Submission(Base):
    __tablename__ = 'submission'

    submission_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('assignment.assignment_id',ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('student.student_id',ondelete='CASCADE'), nullable=False)
    submission_date = Column(TIMESTAMP, nullable=False, default=func.now())
    file_path = Column(String(255), nullable=False)
    remarks = Column(Text, nullable=False)


class Teacher(Base):
    __tablename__ = 'teacher'

    teacher_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.user_id',ondelete='CASCADE'), nullable=False)


class TeacherClass(Base):
    __tablename__ = 'teacher_class'

    tc_id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey('teacher.teacher_id',ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('classroom.class_id',ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.subject_id',ondelete='CASCADE'), nullable=False)



class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    number = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(Enum('teacher', 'student','admin'), nullable=True)
    status = Column(String(20), nullable=False, default='pending')



class Chatroom(Base):
    __tablename__ = 'chatroom'

    chat_id = Column(Integer, primary_key=True, index=True)
    created_date = Column(Date, nullable=False, default=func.now())
    user1_id = Column(Integer, ForeignKey('user.user_id',ondelete='CASCADE'), nullable=False)
    user2_id = Column(Integer, ForeignKey('user.user_id',ondelete='CASCADE'), nullable=False)



class Message(Base):
    __tablename__ = 'message'

    msg_id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(Date, nullable=False, default=func.now())
    chat_id = Column(Integer, ForeignKey('chatroom.chat_id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey('user.user_id',ondelete='CASCADE'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('user.user_id',ondelete='CASCADE'), nullable=False)
    status = Column(String(10), nullable=False, default="unread")

    

class Notification(Base):
    __tablename__ = 'notification'  # Replace with the actual table name

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    which_class=Column(Integer, nullable=False)


class McqMarks(Base):
    __tablename__ = 'mcq_marks'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('student.student_id',ondelete='CASCADE'), nullable=False)
    user_name = Column(String(255), nullable=False)
    class_id = Column(Integer, ForeignKey('classroom.class_id',ondelete='CASCADE'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subject.subject_id',ondelete='CASCADE'), nullable=False)
    marks = Column(Integer, nullable=False)
    percentage = Column(Float(precision=2), nullable=False)
    is_taken = Column(String(10), nullable=False, default='no')



try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(" please check the database connection")   

    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

