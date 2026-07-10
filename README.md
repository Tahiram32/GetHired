# GetHired

**Your personal, private, AI-powered career advocate.**

GetHired is a free tool designed to help you navigate a tough job market. It filters out ghost jobs, tracks your applications, helps tailor your resume to bypass automated filters, and gives you a safe space to practice for interviews.

Everything runs directly on your own computer. Your data, your resume, and your interview answers never leave your machine except to be securely processed by the AI.

---

## 🛠️ Step 1: Install the Prerequisites (Do this first!)
GetHired runs locally on your computer, which means your machine needs the basic tools to understand the code. If you do not install these first, the app will not work.

1. **Python (version 3.10 or higher)**
   * **Download Here:** [python.org/downloads](https://www.python.org/downloads/)
   * **IMPORTANT FOR WINDOWS:** When the installer opens, look at the very bottom of the window and check the box that says **"Add python.exe to PATH"** before you click Install.

2. **Node.js**
   * **Download Here:** [nodejs.org](https://nodejs.org/)
   * Download the "LTS" (Long Term Support) version and install it with the default settings.

---

## 🔑 Step 2: Get Your API Keys
GetHired uses AI and live search data to power the app. You need to give the app your personal "keys" to these services. It costs a few pennies per use, but you control the budget.

### How to get your OpenAI Key:
1. Go directly to this exact page: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in.
3. In the left menu, click **Settings > Billing** and add a minimum $5 balance (the app uses very little, but OpenAI requires a prepaid balance to work).
4. Go back to the **API keys** page.
5. Click the **"Create new secret key"** button. Name it "GetHired".
6. Copy the long string of text immediately (it starts with `sk-`). You will never be able to see it again!

### How to set them up in the app:
1. Open the `gethired` folder you downloaded.
2. Find the file named `env.example`.
3. Open it in Notepad or TextEdit and replace the placeholder text with your actual keys:
   ```text
   OPENAI_API_KEY=sk-your_long_openai_key_here
   SERPAPI_API_KEY=your_serpapi_api_key_here
   ```
4. Save the file.
5. **CRITICAL STEP:** Rename the file from `env.example` to exactly `.env` (make sure there is a dot at the beginning and no `.txt` at the end).

---

## 🚀 Step 3: Launching the App

### For Windows Users
Double-click the `start_windows.bat` file in the folder. 

**🚨 Important Security Warning:** 
Because you downloaded this from the internet, a massive bright blue screen might pop up saying **"Windows protected your PC."** 
* Do not panic. This is normal. 
* Click the small text that says **"More info"**.
* Click the button that says **"Run anyway"**.

A black terminal window will open and install everything automatically. Your web browser will open the app when it's ready. **Do not close the black window while using the app!**

### For Mac / Linux Users
Mac computers do not allow you to double-click these scripts by default. You need to tell your computer it is safe to run.

1. Open your **Terminal** application (press Cmd + Space, type "Terminal", and hit Enter).
2. Type `cd ` (with a space after it).
3. Drag and drop the `gethired` folder from your desktop into the Terminal window and press Enter.
4. Copy and paste these two commands, pressing Enter after each one:
   ```bash
   chmod +x start_mac_linux.sh
   ./start_mac_linux.sh
   ```

The script will install everything and open the app in your browser automatically.

---


---

## 🔄 How to Update the App
When we release new features or bug fixes, you don't want to lose your saved jobs or your API keys! To update safely:
1. Download the newest ZIP file from GitHub and extract it into a brand new folder.
2. Copy your `.env` file from your old folder and paste it into the new folder.
3. (Coming Soon) If we add a database file for your saved jobs, you will copy that over as well. 
4. Run the new `start_windows.bat` or `start_mac_linux.sh` file!

## 💡 What Can GetHired Do?

* **Anti-Scam Job Feed:** Search for local or remote jobs. The AI automatically scans job descriptions to warn you about potential scams or unverified listings.
* **Kanban Application Tracker:** Keep a visual board of your progress. The system will remind you to keep pushing because volume is key!
* **Resume Tailorer:** Paste a job description and upload your PDF resume. The AI will rewrite your bullet points to match the exact keywords the company is looking for.
* **Interview Coaching Engine:** Practice for your interview in a text-based chat. Get structured feedback and see exactly how a "Gold Standard" answer should look.
