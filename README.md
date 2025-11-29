# IPL Auction Management System

A comprehensive web-based application to simulate and manage a mock IPL (Indian Premier League) auction. Built with Python and Flask, this system allows users to manage teams, auction players, and analyze squad strengths in real-time.

## 🚀 Features

### 1. Auction Dashboard
- **Live Auctioning**: Real-time interface to sell players to teams or mark them as unsold.
- **Dynamic Budgeting**: Automatically updates team purses as players are bought.
- **Player Categorization**: Organized views for Batsmen, Bowlers, Wicketkeepers, and All-rounders.

### 2. Team Management
- **Squad Overview**: Detailed view of every team's current squad composition.
- **Financial Tracking**: Track spending across different player categories.
- **Reset Functionality**: Ability to reset specific teams or the entire auction to start fresh.

### 3. Player Management
- **Add Custom Players**: Form to add new players with detailed stats (Runs, Wickets, Strike Rate, etc.).
- **Player Database**: JSON-based storage for persistence without needing a heavy database.
- **Stats Tracking**: Comprehensive stats for every player used for evaluation.

### 4. Smart Analytics & Evaluation
- **Team Grading**: Automatic grading system (A+, A, B, etc.) based on squad balance.
- **SWOT Analysis**: Automated analysis identifying Strengths and Weaknesses (e.g., "Strong batting lineup", "Missing specialist wicketkeeper").
- **Comparative Stats**: Compare teams based on average batting average, economy rates, and more.

## 🛠️ Tech Stack
- **Backend**: Python 3.x, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Data Storage**: JSON (File-based persistence)

## 💻 Installation & Usage

Follow these steps to set up and run the project locally.

### Prerequisites
- Python 3.x installed on your system.
- Git installed.

### Steps

1.  **Clone the Repository**
    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd <REPOSITORY_NAME>
    ```

2.  **Create a Virtual Environment (Optional but Recommended)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install flask
    ```

4.  **Run the Application**
    ```bash
    python main.py
    ```

5.  **Access the App**
    Open your web browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 📂 Project Structure
```
├── app.py              # Main application logic and routes
├── main.py             # Entry point to run the server
├── data/               # JSON files storing Players and Teams data
├── templates/          # HTML templates for the frontend
└── static/             # CSS and JavaScript files
```

## 🤝 Contributing
Feel free to fork this repository and submit pull requests. You can also open issues for bugs or feature suggestions.