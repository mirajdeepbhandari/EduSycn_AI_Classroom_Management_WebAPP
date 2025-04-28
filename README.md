

<h1 align="center">EduSync AI Classroom Management WebApp</h1>
<h3 align="center">An AI-powered platform for modern classroom management and educational synchronization</h3>

## Steps to Run The Application

- 🔍 **Clone the repository**
  ```bash
  1) git clone https://github.com/mirajdeepbhandari/EduSycn_AI_Classroom_Management_WebAPP.git
  ```

- 🐍 **Create virtual environment**
  ```cmd
  2) python -m venv ./myvenv
  ```

- ⚡ **Activate the environment**
  ```
  3) In Windows CMD:
   myvenv\Scripts\activate.bat
  ```

- 📦 **Install dependencies**
  ```bash
  4) pip install -r requirements.txt
  ```

- 🔑 **Configure API key**
  ```
  5) Create a .env file in the root directory and add:
    GOOGLE_API_KEY=your_api_key_here
  ```
  Get your API key from [Google AI Studio](https://aistudio.google.com/apikey)

- 🤖 **Setup sentiment analysis model**
  ```bash
  6) clone the model repo go inside the model main folder move the inner sentimentModel directory to the static folder of project folder
     git clone https://huggingface.co/mirajbhandari/sentimentModel
  
  ```

- 🗄️ **Install database server**
  
  Download and install [XAMPP](https://www.apachefriends.org/download.html)

- 📊 **Configure database**
  ```
  7)  Create database named 'edusync_f'
  8) Import the edusync_f.sql file
  ```

- 🚀 **Start services**
  ```
  9) Start XAMPP Apache and MySQL services
  ```

- 🌐 **Run the server**
  ```bash
  10) uvicorn main:app
  ```

  ## About the Directiory Structure

