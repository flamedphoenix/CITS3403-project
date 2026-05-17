<div align="center">
    <h1>★ RateRace — Which Movie Rates Higher?</h1>
    <span style="font-size: 1.25em; font-weight: bold;">
        <p style="margin-bottom: 0;">Two films. One question.</p>
        <p style="margin-top: 0;">Guess which has the higher IMDb score and climb the ranks.</p>
    </span>
</div>

## Cits3403 Project   

Welcome to RateRace, a full-stack Flask based web game where users compare 10 movie pairs and attempt to guess the higher-rated film. The goal of the project is to provide an simple competitive movie-ranking game for a player of any entry level, that is both engaging and entertaining.     

## RateRace offers:
* Dynamic gameplay - 10 round games where both timer speed and answer correctness affect your score. Faster answers earn better points.
* Dynamic movie fetching - Movies are fetched from the `TMDB` API automatically when either the movie cache is low, or it has been at least 3 days since the last fetch, so the pool stays fresh and gradually grows.
* Gamemodes:
  * Standard Mode - Played with a set of 10 random movie pairs
  * Daily Mode — One shared set of movie pairs generated every day, the same for every player. A dropdown daily game history panel lets you view your score from previous days and play them again.
  * Challenge Mode (PVP) - A real-time head-to-head duel. Both players receive the same random movie pairs simultaneously, and the first to answer receives a point bonus.
* Global Leaderboard - Tracks highest score, best time, accuracy and rank of all players. A user must play a game to appear on the leaderboard. The leaderboard also offers:
  * A challenge button to request a duel against any currently online user, where the challengee receives a challenge pop-up without a page reload
  * A click on a player's name to view their personal profile page with more stats
* Score History - Daily scores and standard scores are stored separately and daily scores can be viewed through the game history panel


---
## Design and Architecture

The frontend is built with HTML, Tailwind CSS, and JavaScript. Pages are initially delivered through server-side rendering by Flask's `render_template()`, which uses Jinja templating for injecting user session data, leaderboard rows, daily history entries and score results    

After the initial load, game state data is fetched with AJAX through the Fetch API and `XMLHttpRequest`. DOM manipulation handles transitions between game rounds and game mode selection. Card title/poster elements, score, and other UI elements are updated to reflect the current state of the match and round.            

The Fetch API and SocketIO are used for real-time updates and game logic. On the backend, this application uses the Flask Python library with several extensions (as specified in `requirements.txt`) for API endpoints, field validation, session management/route protection (via `Flask-Login`), database management (via `Flask-SQLAlchemy`), and real-time event handlers.        

Challenge mode and single player modes differ in their architecture. While client-side rendering handles what the player sees in both, challenge mode round and match validation uses server-side logic with WebSockets to ensure fairness and synchronisation between players, while single player game logic is handled client-side.        

---

## Group Members
| UWA ID   | Name            | Github Username |
|----------|-----------------|-----------------|
| 24273259 | Kush Patel      | KushPatel-18    |
| 24252883 | Dean Kalweit    | flamedphoenix   |
| 23934799 | Roland Levinson | ggtroland       |

---
## Simple Launch Instructions        
### Set up Initial Project Files:          
Run ```git clone https://github.com/flamedphoenix/CITS3403-project``` in target directory to clone the repository, and then `cd CITS3403-project`  
Run ```python3 -m venv venv``` in root directory of project to set-up virtual environment (reccomended, not necessary)            
Activate the environment on:        
* Windows: ```venv\Scripts\activate```         
* Mac / Linux:   ```source venv/bin/activate```         
* Remember to activate it on new terminals you open for this application

Run ```pip install -r requirements.txt```  to install dependencies        
Before configuring environment, set up TMDB key

#### How to Set Up TMDB Key
Start by visiting https://www.themoviedb.org/signup, and input your credentials. Once signed up, follow the verification steps which should open you up to your profile page.
* Select your profile logo, select "settings" in the drop down, click API in the side panel and the click `Request API Key`
* You will be prompted by several prompts, including a form that you must fill out.
* Once completed and after approval, you should click `Access your API keys`, and there will be a header saying `API Key` under API with a key. That is your TMDB API key
* For the sake of this project and for the sake of marking, our API key for TMDB is: `8fedfc73fccc26d93432c78ffb09303f`. Under any other circumstance, we would not leave our key out in the open, the key will likely be deleted after the duration of this project.

#### How to set up `.env`
Create ```.env``` in project root to start configuring environment, and add `SECRET_KEY=` and `TMDB_API_KEY=` with your respective keys following the equals sign. The secret key can be anything, however should be long and random.
  
### Tailwind CSS (in its own terminal):  
If not installed already, Install [NodeJS](https://nodejs.org/en/download) and set it up beforehand for the sake of Tailwind.         
Next in `client/` directory, for initial set up:    
Run ```npm install```            
For running tailwind in general, in a new terminal (always run from `client/`):                
Run ```npm run watch:css```              
  
### Initialise and Launch in it's own terminal -- Whenever you want to run the Application:  
Run `python3 run.py` in root directory of project - already configured to apply database migrations        

Visit http://127.0.0.1:5020 to start playing!        

### Database Management / Updates        
If models are updated in `models.py`, then in project root directory,               
Run ```flask --app run db migrate -m "change description"```            
Run ```flask --app run db upgrade``` (or run `run.py` again)            
If models need to be downgraded:            
Run ```flask --app run db downgrade```            

---

### Running the Tests
**UnitTests for Game, API, Models, and User Auth**:     
In a separate terminal run:            
```
python3 -m unittest tests/test_models_auth.py
python3 -m unittest tests/test_game_api.py
```
        
**System Tests**    
Run either:            
```python3 -m unittest tests/test_selenium.py``` if you want to see the test windows              
or                
```HEADLESS=1 python3 -m unittest tests/test_selenium.py``` if you don't want browser window                  

---

## How to Play / Navigate the Website

### Landing on the Website — [Home/Index Page](#index-page)

To begin playing, sign up or log in. Click **Sign Up** in the navbar or the **"Sign Up Free"** button on the landing page.        
Once logged in, click **Play Now** to go to the Game page. You must play at least one game to appear on the leaderboard.        

### Game Start Screen — *Game Start Screen with Daily Game History Panel*

Three buttons are shown: **Start Game**, **Daily Challenge**, and a dropdown arrow for the daily history panel.

- The dropdown shows a history of past daily games. Entries are greyed out if already played that day, and show a score if played on the day it was the daily. Today's entry is highlighted in gold.
- Clicking any entry starts that day's daily game with the appropriate UI label.
- Clicking **Daily Challenge** or today's gold entry starts today's daily game.

### Playing a Game — *Standard Game Screen* and *Daily Challenge*

You are shown two movie cards. Click the one you think has the higher IMDb rating. A timer counts down for each round so answer before it expires. At the end you'll see a score summary and can play again or view the leaderboard.

### Leaderboard — *[Leaderboard Page and Challenge Page](#leaderboard-pages)* and *[User Profile Page](#user-profile)*

- Click a player's **name** to view their profile page.
- Click the **Challenge** button to send an online user a challenge request.
- The recipient sees a popup to accept or decline with no page reload.
- On accept, a challenge game starts immediately.

### Challenge Game — *Challenge Game*

Similar to other game modes, but:

- The player who answers first receives bonus points.
- Both players' scores are visible during rounds.
- The end screen shows both players' results albeit fewer stats than the single player game-modes.

---

## Web Page Previews
### Standard Game Pages

| Standard Game Screen   | Game Start Screen with Daily Game History Panel       |
|------------------------|--------------------------|
| <img width="1470" height="767" alt="Game-Standard" src="https://github.com/user-attachments/assets/bf12edfd-1111-4ac2-814a-9c4a216b9b0c" />        | <img width="1469" height="767" alt="Daily-history-panel-game" src="https://github.com/user-attachments/assets/de6a41d7-2aac-41ad-9e8f-6368c3a425c5" />|

### Leaderboard Pages
| Leaderboard Page and Challenge Page  | Challenge Game |
|-------------------------------|---------------------------------|
| <img width="1463" height="753" alt="Leaderboard-and-Challenge" src="https://github.com/user-attachments/assets/ff72a56f-d935-4a04-91d2-41ebc986edc9" />         | <img width="1456" height="756" alt="Challenge-Game" src="https://github.com/user-attachments/assets/4d051200-cb2d-4575-9b4f-14eabc3877ad" />       |

### Daily Challenge
|           Daily Challenge                                                                                                                   |
|---------------------------------------------------------------------------------------------------------------------------------------------|
|<img width="1466" height="766" alt="Daily-Challenge" src="https://github.com/user-attachments/assets/75e331d9-8b5d-4758-8c0e-b68b72124dda" />|

<details>
<summary><h3><strong>Click to See User Profile Page</strong></h3></summary>
    
![User Profile Page](https://github.com/user-attachments/assets/7962836c-394e-42b0-9222-4006b05a338a)
</details>
<details>
<summary><h3><strong>Click to See Home / Index Page</strong></h3></summary>
    
![Index page](https://github.com/user-attachments/assets/c4c4705c-3c5e-496e-94fd-18ac0e72e811)
</details>

---

<div align="center">
★   RateRace — CITS3403 Project — 2026   ★
</div>
