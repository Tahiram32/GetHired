# GetHired

**Your personal, private, AI-powered career advocate.**

GetHired is a free tool designed to help you navigate a tough job market. It filters out ghost jobs, tracks your applications, helps tailor your resume to bypass automated filters, and gives you a safe space to practice for interviews.

Everything runs directly on your own computer. Your data, your resume, and your interview answers never leave your machine except to be securely processed by the AI.

---

## 🚀 How to Start the App (Zero Tech Skills Required!)

You don't need to be a programmer to use this. Just follow these simple steps:

### 1. The One-Time Setup (API Keys)
GetHired uses two services to find jobs and analyze your resume. You need to give the app your personal "keys" to these services.
1. Create a file named `.env` in this exact folder (the `gethired` folder).
2. Open it in a basic text editor (like Notepad or TextEdit).
3. Paste the following two lines into the file:
   ```text
   OPENAI_API_KEY=your_openai_api_key_here
   SERPAPI_API_KEY=your_serpapi_api_key_here
   ```
4. Replace the placeholders with your actual keys (you can get them for free at OpenAI and SerpAPI) and save the file.

### 2. Launching the App
**For Windows Users:**
Just double-click the `start_windows.bat` file in this folder. 
A black window will open and do all the heavy lifting for you. It might take a minute or two the very first time. Once it's ready, your web browser will automatically open to the app!

**For Mac / Linux Users:**
1. Open your "Terminal" application.
2. Drag and drop the `start_mac_linux.sh` file into the Terminal window and press Enter. 
   *(If it says "Permission denied", type `chmod +x start_mac_linux.sh` and press Enter, then try again).*
3. The app will install everything it needs and automatically open your web browser.

**Important Note:** 
Do not close the black terminal window while you are using GetHired! Closing it will turn off the app. When you are done for the day, you can close the window to shut everything down safely.

---

## 🛠️ System Requirements
If the app refuses to open, you might need to install two standard programs on your computer first:
1. **Python** (version 3.10 or higher): [Download Here](https://www.python.org/downloads/) *(Windows users: Check "Add python.exe to PATH" during installation!)*
2. **Node.js**: [Download Here](https://nodejs.org/)

---

## 💡 What Can GetHired Do?

* **Anti-Scam Job Feed:** Search for local or remote jobs. The AI automatically scans job descriptions to warn you about potential scams or unverified listings.
* **Kanban Application Tracker:** Keep a visual board of your progress. The system will remind you to keep pushing because volume is key!
* **Resume Tailorer:** Paste a job description and upload your PDF resume. The AI will rewrite your bullet points to match the exact keywords the company is looking for.
* **Interview Coaching Engine:** Practice for your interview in a text-based chat. Get structured feedback and see exactly how a "Gold Standard" answer should look.

*Built to help you land the job.*
