 📊 YouTube Data Dashboard — Streamlit

A clean and lightweight **YouTube Analytics Dashboard** built using **Streamlit** and the **YouTube Data API v3**.  
Paste any YouTube Channel ID and instantly get insights like subscribers, total views, top videos, thumbnails, KPIs, and interactive charts.



🚀 Features

✔ **Channel Overview**  
- Subscribers  
- Total views  
- Total video count  
- Channel logo + description  

✔ Latest Videos (with thumbnails)**  
- View count  
- Likes  
- Comments  
- Published date  
- Direct watch link  

✔ Analytics & KPIs**  
- Top-performing video  
- Average views per video  
- Total views in current sample  

✔ Interactive Charts**  
- Views trend by publish date  
- Plotly-powered dynamic visualizations  

✔ Export Features**  
- Download full video stats as CSV  

✔ Environment-Based API Key**  
- Secure `.env` handling with `python-dotenv`

 🛠️ Tech Stack

- Python 3**
- Streamlit** (UI)
- YouTube Data API v3**
- Plotly** (charts)
- Pandas** (data processing)
  Requests** & **google-api-python-client**


📂 Project Structure

├── app.py
├── .env (not committed)
├── .gitignore
├── requirements.txt
├── README.md
└── screenshot.png / demo.gif

⚙️ Setup Instructions

1️⃣ Clone the Repository**

https://github
.com/Hashir4m4/Building-a-YouTube-Data-Dashboard-using-streamlit-.git

Create Virtual Environment

python -m venv venv
venv\Scripts\activate

Install Dependencies
pip install -r requirements.txt


Set Up Your API Key

YOUTUBE_API_KEY=YOUR_API_KEY_HERE

Run the Dashboard
streamlit run app.py


🔍 How to Get a YouTube API Key

1 Go to Google Cloud Console
2 Create a new project
3 Enable YouTube Data API v3
4 Go to Credentials → Create API Key
5 Add it to .env
6 Run the app

🙌 Acknowledgements

*YouTube Data API v3
*Streamlit Community
*Python Open Source ecosystem


🧩 Future Enhancements

1 OAuth2 login for full YouTube Analytics API (watch time, impressions, CTR)
2 Daily stats tracking & database storage
3 Dark mode UI
4 Multi-channel analytics
5 Creator-level summary pages
