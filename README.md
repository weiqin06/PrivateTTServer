# Private PingPong Rating System

A lightweight web-based PingPong match tracking and ranking system. It features an ELO rating algorithm, detailed match result logging (e.g., 3:2), and a comprehensive admin dashboard. 

Idea comes from wei.qin. Code credit goes to Gemini......

## Features

- **ELO Rating Algorithm**: Automatically calculates point gains/losses based on player skill differences.
- **Detailed Match Recording**: Log specific game scores and select opponents from a registered player list via a dropdown menu.
- **Admin Dashboard**: Manage users directly—edit ratings, reset passwords, or delete accounts.
- **Skill Initialization**: New users can choose their initial skill level (Beginner, Intermediate, Advanced).
- **Global Rankings**: A real-time leaderboard showing player standings.
- **User Authentication**: Secure login and registration system with hashed passwords.

---

## Deployment Guide

### Prerequisites

- Python 3.x installed.
- `pip` (Python package manager).

## How to Use

### 1. Download and Extract
Download the project package and extract the files to your local directory.

### 2. Install Dependencies
Open your terminal or command prompt and install the required web framework:
```bash
pip install flask
```

### 3. Initialize the Database
Run the database initialization script. This step creates the necessary tables and the default administrator account:
```bash
python init_db.py
```

### 4. Start the Server
Launch the application by running:
```bash
python app.py
```

### 5. Access the System
Open your web browser and visit: http://127.0.0.1:5000

