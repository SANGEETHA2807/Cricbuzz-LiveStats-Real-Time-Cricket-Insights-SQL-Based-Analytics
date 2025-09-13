import streamlit as st
import requests
import pandas as pd
import sqlite3
import datetime
from datetime import datetime, timedelta

# 🔑 API Credentials
API_KEY = "997354f96emsh13978d66fe8ee01p1b5c7djsn614af4f1bef5"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}

# ------------------------------
# 📌 Page 1: Live Scores 👈
# ------------------------------
def live_scores():
    st.header("🏏 Live, Upcoming & Recent Matches")

    # Tabs for match types
    tab1, tab2, tab3 = st.tabs(["🔴 Live", "⏳ Upcoming", "✅ Recent"])

    with tab1:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        show_matches(url)

    with tab2:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/upcoming"
        show_matches(url)

    with tab3:
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/recent"
        show_matches(url)


def show_matches(url):
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    matches = []
    match_map = {}  # Store matchId -> match info
    for type_match in data.get("typeMatches", []):
        for series in type_match.get("seriesMatches", []):
            series_data = series.get("seriesAdWrapper", {})
            for match in series_data.get("matches", []):
                info = match.get("matchInfo", {})
                team1 = info.get("team1", {}).get("teamName", "")
                team2 = info.get("team2", {}).get("teamName", "")
                match_id = info.get("matchId")
                status = info.get("status")

                display = f"{team1} vs {team2} - {status}"
                matches.append(display)
                match_map[display] = match_id  # Store matchId

    if matches:
        selected = st.selectbox("Select Match", matches)
        if selected:
            match_id = match_map[selected]
            st.write(f"Selected Match ID: {match_id}")
            st.success(f"Showing Scorecard for: {selected}")

            # Fetch Scorecard API
            score_url = f"https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/{match_id}/scard"
            resp = requests.get(score_url, headers=HEADERS)
            scard = resp.json()

            # 🏏 Display tables for both teams
            for inning in scard.get("scorecard", []):
                st.subheader(f"{inning.get('batteamname')} - {inning.get('score')} ({inning.get('overs')} overs)")
                
                # Batsmen Table
                batsmen = []
                for b in inning.get("batsman", []):
                    batsmen.append({
                        "Name": b.get("name"),
                        "Runs": b.get("runs"),
                        "Balls": b.get("balls"),
                        "4s": b.get("fours"),
                        "6s": b.get("sixes"),
                        "SR": b.get("strikeRate"),
                    })
                if batsmen:
                    st.write("**Batting:**")
                    st.dataframe(pd.DataFrame(batsmen)) #using panda or data frame to display

                # Bowlers Table
                bowlers = []
                for bow in inning.get("bowler", []):
                    bowlers.append({
                        "Name": bow.get("name"),
                        "Overs": bow.get("overs"),
                        "Runs": bow.get("runs"),
                        "Wickets": bow.get("wickets"),
                        "Econ": bow.get("economy"),
                    })
                if bowlers:
                    st.write("**Bowling:**")
                    st.dataframe(pd.DataFrame(bowlers))

                st.markdown("---")


# ------------------------------
# 📌 Page 2: Player Stats
# ------------------------------
def player_stats():
    st.header("👤 Player Stats")
    
    with st.expander("About the Players Page"):
        # ✅ This is where you put the description text
        st.info("""
        Search any player by full or partial name. 
        Select a player from the list to see:
        - Profile (default)
        - Batting career stats
        - Bowling career stats
        """)



    # Show trending players as example (optional)
    trending_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/trending"
    trending_res = requests.get(trending_url, headers=HEADERS).json()
    trending_players = [p["name"] for p in trending_res.get("player", [])][:3]  # top 3 
    st.write(f"Trending Players: {', '.join(trending_players)}")

    # Search player
    player_name = st.text_input("Search Player")
    if st.button("Search") and player_name:
        # Search API
        search_url = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
        response = requests.get(search_url, headers=HEADERS, params={"plrN": player_name})
        data = response.json()

        players_list = []
        for p in data.get("player", []):
            players_list.append({"id": p["id"], "name": p["name"], "team": p["teamName"]})

        if players_list:
            df = pd.DataFrame(players_list)
            st.dataframe(df)
            selected_player = st.selectbox("Choose Player", df["name"])
            
            if selected_player:
                player_id = df[df["name"] == selected_player]["id"].values[0]

                # Player profile API
                url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}"
                res = requests.get(url, headers=HEADERS).json()

                # Tabs: Profile, Batting, Bowling
                tab1, tab2, tab3 = st.tabs(["Profile", "Batting Stats", "Bowling Stats"])

                with tab1:
                    st.subheader(res.get("name", "Unknown Player"))
                    st.write(f"**Role:** {res.get('role')}")
                    # st.write(f"**Bio:** {res.get('bio')[:200]}")
                    bio_text = res.get('bio', '').replace('<br>', ' ').replace('<br></br>', ' ')
                    st.write(f"**Bio:** {bio_text[:200]}")
                    st.write(f"**DOB:** {res.get('DoB')}")
                    st.write(f"**Birth Place:** {res.get('birthPlace')}")
                    st.write(f"**Height:** {res.get('height')}")
                    st.write(f"[🔗 Full Profile on Cricbuzz](https://www.cricbuzz.com/profiles/{player_id})")

                with tab2:
                    batting_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/batting"
                    bat_res = requests.get(batting_url, headers=HEADERS).json()
                    bat_headers = bat_res.get("headers", [])
                    bat_rows = bat_res.get("values", [])
                    if bat_rows:
                        bat_data = pd.DataFrame([r.get("values") for r in bat_rows], columns=bat_headers)
                        st.dataframe(bat_data)
                    else:
                        st.write("No batting data available.")

                with tab3:
                    bowling_url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/bowling"
                    bowl_res = requests.get(bowling_url, headers=HEADERS).json()
                    bowl_headers = bowl_res.get("headers", [])
                    bowl_rows = bowl_res.get("values", [])
                    if bowl_rows:
                        bowl_data = pd.DataFrame([r.get("values") for r in bowl_rows], columns=bowl_headers)
                        st.dataframe(bowl_data)
                    else:
                        st.write("No bowling data available.")

# ------------------------------
# 📌 Page 3 : SQL Questions:
# ------------------------------
from datetime import datetime, timedelta
import psycopg2

def SQL_Questions():
    # ----------------------------
    # 1️⃣ Database connection (PostgreSQL)
    # ----------------------------
    try:
        conn = psycopg2.connect(
            user="postgres",
            password="hello01!MSL",   
            host="localhost",
            port="5433",                
            dbname="cricbuzz"           
        )
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return

    questions = {
        1: {
            "text": "Find all players who represent India. Display their full name, playing role, batting style, and bowling style.",
            "sql": """SELECT 
                        full_name,
                        role AS playing_role,
                        batting_style,
                        bowling_style
                    FROM PlayersQuestion1 ;"""
        },
        2: {
            "text": "Show all cricket matches that were played in the last 30 days. Include the match description, both team names, venue name with city, and the match date. Sort by most recent matches first.",
            "sql": """SELECT 
                        m.series_name || ' - ' || m.team1 || ' vs ' || m.team2 AS match_description,
                        m.team1,
                        m.team2,
                        m.venuename || ', ' || m.city AS venue,
                        TO_TIMESTAMP(CAST(m.start_time AS BIGINT) / 1000)::DATE AS match_date
                    FROM Matches m
                    WHERE TO_TIMESTAMP(CAST(m.start_time AS BIGINT) / 1000)::DATE >= CURRENT_DATE - INTERVAL '30 days'
                    AND TO_TIMESTAMP(CAST(m.start_time AS BIGINT) / 1000)::DATE <= CURRENT_DATE
                    ORDER BY match_date DESC;"""
        },
        3: {
            "text": "List the top 10 highest run scorers in ODI cricket. Show player name, total runs scored, batting average, and number of centuries. Display the highest run scorer first.",
            "sql": """SELECT 
                        player_name,
                        runs,
                        average,
                        innings
                    FROM MostRuns
                    ORDER BY runs DESC
                    LIMIT 10;"""
        },
        4: {
            "text": "Display all cricket venues that have a seating capacity of more than 50,000 spectators. Show venue name, city, country, and capacity. Order by largest capacity first.",
            "sql": """SELECT 
                        ground AS venue_name,
                        city,
                        country,
                        CAST(capacity AS INTEGER) AS capacity
                    FROM Venues
                    WHERE CAST(capacity AS INTEGER) > 50000
                    ORDER BY CAST(capacity AS INTEGER) DESC;"""
        },
        5: {
            "text": "Calculate how many matches each team has won. Show team name and total number of wins. Display teams with most wins first.",
            "sql": """SELECT 
                        t.team_name,
                        COUNT(m.match_id) AS total_wins
                    FROM Teams t
                    LEFT JOIN Matches m 
                    ON m.winner_team_id = t.team_id

                    GROUP BY t.team_name
                    ORDER BY total_wins DESC;"""
        },
        6: {
            "text": "Count how many players belong to each playing role (like Batsman, Bowler, All-rounder, Wicket-keeper). Show the role and count of players for each role.",
            "sql": """SELECT 
                        role AS player_role,
                        COUNT(player_id) AS total_players
                    FROM Players
                    GROUP BY role
                    ORDER BY total_players DESC;"""
        },
        7: {
            "text": "Find the highest individual batting score achieved in each cricket format (Test, ODI, T20I). Display the format and the highest score for that format.",
            "sql": """SELECT 
                        m.format,
                        MAX(b.runs) AS highest_score
                    FROM BattingScore b
                    JOIN Matches m ON b.match_id = m.match_id
                    GROUP BY m.format;"""
        },
        8: {
            "text": "Show all cricket series that started in the year 2024. Include series name, host country, match type, start date, and total number of matches planned.",
            "sql": """SELECT 
                        series_name,
                        host_country,
                        match_type,
                        start_date,
                        total_matches
                    FROM Series
                    WHERE (start_date) = '2024';"""
        },
        9: {
            "text": "Find all-rounder players who have scored more than 1000 runs AND taken more than 50 wickets in their career. Display player name, total runs, total wickets, and the cricket format.",
            "sql": """WITH WicketsPerPlayer AS (
                        SELECT player_id, SUM(wickets) AS total_wickets
                        FROM BowlingScore
                        GROUP BY player_id
                    )
                    SELECT 
                        p.full_name AS player_name,
                        mr.runs AS total_runs,
                        w.total_wickets,
                        'Career' AS format
                    FROM Players p
                    JOIN MostRuns mr ON p.player_id = mr.player_id
                    JOIN WicketsPerPlayer w ON p.player_id = w.player_id
                    WHERE p.role = 'All-rounder'
                        AND mr.runs > 1000
                        AND w.total_wickets > 50
                    ORDER BY mr.runs DESC;"""
        },
        10: {
            "text": "Get details of the last 20 completed matches. Show match description, both team names, winning team, victory margin, victory type (runs/wickets), and venue name. Display most recent matches first.",
            "sql": """SELECT 
                        m.series_name AS match_description,
                        m.team1 AS team1_name,
                        m.team2 AS team2_name,
                        t.team_name AS winning_team,
                        m.victory_margin,
                        m.victory_type,
                        m.venuename AS venue_name
                    FROM Matches m
                    LEFT JOIN Teams t ON m.winner_team_id = t.team_id
                    LIMIT 20;"""
        },
        11: {
            "text": "Compare each player's performance across different cricket formats. For players who have played at least 2 different formats, show their total runs in Test cricket, ODI cricket, and T20I cricket, along with their overall batting average across all formats.",
            "sql": """SELECT 
                        player_name,
                        runs AS total_runs,
                        average AS batting_average,
                        'Career' AS format
                    FROM MostRuns
                    ORDER BY runs DESC
                    LIMIT 10;"""
        },
        12: {
            "text": "Analyze each international team's performance when playing at home versus playing away. Count wins for each team in both home and away conditions.",
            "sql": """SELECT
                        t.team_name,
                        SUM(CASE WHEN t.country = v.country THEN 1 ELSE 0 END) AS home_wins,
                        SUM(CASE WHEN t.country != v.country THEN 1 ELSE 0 END) AS away_wins
                    FROM Matches m
                    JOIN Teams t ON m.winner_team_id = t.team_id
                    JOIN Venues v ON m.venue_id = v.venue_id
                    GROUP BY t.team_name;"""
        },
        13: {
            "text": "Identify batting partnerships where two consecutive batsmen scored a combined total of 100 or more runs in the same innings. Show both player names, their combined partnership runs, and which innings it occurred in.",
            "sql": """SELECT
                        batsman1_id,
                        batsman2_id,
                        runs AS partnership_runs,
                        innings_id,
                        match_id
                    FROM Partnerships
                    WHERE runs >= 100
                    ORDER BY runs DESC;"""
        },
        14: {
            "text": "Examine bowling performance at different venues. For bowlers who have played at least 3 matches at the same venue, calculate their average economy rate, total wickets taken, and number of matches played at each venue. Focus on bowlers who bowled at least 4 overs in each match.",
            "sql": """SELECT
                            b.player_id,
                            p.full_name AS bowler_name,
                            t.team_name,
                            v.venue_id,
                            v.ground AS venue_name,
                            COUNT(*) AS matches_played,
                            SUM(b.wickets) AS total_wickets,
                            AVG(b.economy) AS avg_economy
                        FROM BowlingScore b
                        JOIN Matches m ON b.match_id = m.match_id
                        JOIN Venues v ON m.venue_id = v.venue_id
                        JOIN Players p ON b.player_id = p.player_id
                        JOIN Teams t ON b.team_id = t.team_id
                        WHERE b.overs >= 4
                        GROUP BY b.player_id, p.full_name, t.team_name, v.venue_id, v.ground
                        HAVING COUNT(*) >= 3
                        ORDER BY total_wickets DESC, avg_economy ASC;"""
        },
        15: {
            "text": "Identify players who perform exceptionally well in close matches. Calculate each player's average runs scored, total close matches played, and how many of those close matches their team won when they batted.",
            "sql": """WITH CloseMatches AS (
                            SELECT *
                            FROM Matches
                            WHERE (victory_type = 'runs' AND CAST(victory_margin AS INTEGER) < 50)
                            OR (victory_type = 'wickets' AND CAST(victory_margin AS INTEGER) < 5)
                        )
                        SELECT
                            bs.player_id,
                            p.full_name AS player_name,
                            COUNT(*) AS close_matches_played,
                            AVG(bs.runs) AS avg_runs,
                            SUM(CASE WHEN cm.winner_team_id = bs.team_id THEN 1 ELSE 0 END) AS wins_while_batting
                        FROM BattingScore bs
                        JOIN CloseMatches cm ON bs.match_id = cm.match_id
                        JOIN Players p ON bs.player_id = p.player_id
                        GROUP BY bs.player_id, p.full_name
                        HAVING COUNT(*) >= 1
                        ORDER BY avg_runs DESC, wins_while_batting DESC;
                        """
        },
        16: {
            "text": "Track how players' batting performance changes over different years. For matches since 2020, show each player's average runs per match and average strike rate for each year. Only include players who played at least 5 matches in that year.",
            "sql": """WITH MatchesSince2020 AS (
                        SELECT 
                            match_id, 
                            TO_CHAR(TO_TIMESTAMP(CAST(start_time AS BIGINT) / 1000), 'YYYY') AS year
                        FROM Matches
                        WHERE CAST(TO_CHAR(TO_TIMESTAMP(CAST(start_time AS BIGINT) / 1000), 'YYYY') AS INTEGER) >= 2020
                    )
                    SELECT
                        bs.player_id,
                        p.full_name AS player_name,
                        m.year,
                        COUNT(*) AS matches_played,
                        AVG(bs.runs) AS avg_runs_per_match,
                        AVG(bs.strike_rate) AS avg_strike_rate
                    FROM BattingScore bs
                    JOIN MatchesSince2020 m ON bs.match_id = m.match_id
                    JOIN Players p ON bs.player_id = p.player_id
                    GROUP BY bs.player_id, m.year, p.full_name
                    HAVING COUNT(*) >= 5
                    ORDER BY player_name, m.year;
                    """
        },
        17: {
            "text": "Investigate whether winning the toss gives teams an advantage in winning matches. Calculate what percentage of matches are won by the team that wins the toss, broken down by their toss decision.",
            "sql": """SELECT
                        m.toss_decision,
                        COUNT(*) AS total_matches_with_toss_decision,
                        SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) AS matches_won_after_toss,
                        ROUND(100.0 * SUM(CASE WHEN m.toss_winner_id = m.winner_team_id THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_percentage_after_toss
                    FROM Matches m
                    WHERE m.toss_winner_id IS NOT NULL
                        AND m.winner_team_id IS NOT NULL
                    GROUP BY m.toss_decision
                    ORDER BY win_percentage_after_toss DESC;"""
        },
        18: {
            "text": "Find the most economical bowlers in limited-overs cricket (ODI and T20 formats). Calculate each bowler's overall economy rate and total wickets taken.",
            "sql": """SELECT
                            b.player_id,
                            p.full_name AS player_name,
                            COUNT(DISTINCT b.match_id) AS matches_played,
                            SUM(CAST(b.overs AS NUMERIC)) AS total_overs,
                            SUM(b.runs) AS total_runs_conceded,
                            SUM(b.wickets) AS total_wickets,
                            ROUND(SUM(b.runs)::NUMERIC / SUM(CAST(b.overs AS NUMERIC)), 2) AS economy_rate
                        FROM BowlingScore b
                        JOIN Players p ON b.player_id = p.player_id
                        JOIN Matches m ON b.match_id = m.match_id
                        WHERE m.format IN ('ODI', 'T20')
                            AND CAST(b.overs AS NUMERIC) >= 2
                        GROUP BY b.player_id, p.full_name
                        HAVING COUNT(DISTINCT b.match_id) >= 10
                            AND SUM(CAST(b.overs AS NUMERIC)) / COUNT(DISTINCT b.match_id) >= 2
                        ORDER BY economy_rate ASC, total_wickets DESC;"""
        },
        19: {
            "text": "Determine which batsmen are most consistent in their scoring. Calculate the average runs scored and the standard deviation of runs for each player. Only include players who have faced at least 10 balls per innings and played since 2022.",
            "sql": """SELECT
                            b.player_id,
                            p.full_name AS player_name,
                            COUNT(b.match_id) AS innings_played,
                            ROUND(AVG(b.runs)::NUMERIC, 2) AS avg_runs,
                            ROUND(STDDEV(b.runs)::NUMERIC, 2) AS runs_stddev
                        FROM BattingScore b
                        JOIN Players p ON b.player_id = p.player_id
                        JOIN Matches m ON b.match_id = m.match_id
                        WHERE b.balls >= 10
                            AND EXTRACT(YEAR FROM TO_TIMESTAMP(m.start_time::BIGINT / 1000)) >= 2022
                        GROUP BY b.player_id, p.full_name
                        HAVING COUNT(b.match_id) > 0
                        ORDER BY runs_stddev ASC, avg_runs DESC;"""
        },
        20: {
            "text": "Analyze how many matches each player has played in different cricket formats and their batting average in each format.",
            "sql": """SELECT
                        p.player_id,
                        p.full_name AS player_name,
                        SUM(CASE WHEN mf.format = 'Test' THEN 1 ELSE 0 END) AS test_matches,
                        ROUND(CASE WHEN SUM(CASE WHEN mf.format = 'Test' THEN 1 ELSE 0 END) > 0
                                    THEN SUM(CASE WHEN mf.format = 'Test' THEN b.runs ELSE 0 END) * 1.0 /
                                        SUM(CASE WHEN mf.format = 'Test' THEN 1 ELSE 0 END)
                                    ELSE 0 END, 2) AS test_avg,
                        SUM(CASE WHEN mf.format = 'ODI' THEN 1 ELSE 0 END) AS odi_matches,
                        ROUND(CASE WHEN SUM(CASE WHEN mf.format = 'ODI' THEN 1 ELSE 0 END) > 0
                                    THEN SUM(CASE WHEN mf.format = 'ODI' THEN b.runs ELSE 0 END) * 1.0 /
                                        SUM(CASE WHEN mf.format = 'ODI' THEN 1 ELSE 0 END)
                                    ELSE 0 END, 2) AS odi_avg,
                        SUM(CASE WHEN mf.format = 'T20' THEN 1 ELSE 0 END) AS t20_matches,
                        ROUND(CASE WHEN SUM(CASE WHEN mf.format = 'T20' THEN 1 ELSE 0 END) > 0
                                    THEN SUM(CASE WHEN mf.format = 'T20' THEN b.runs ELSE 0 END) * 1.0 /
                                        SUM(CASE WHEN mf.format = 'T20' THEN 1 ELSE 0 END)
                                    ELSE 0 END, 2) AS t20_avg,
                        SUM(1) AS total_matches
                    FROM Players p
                    LEFT JOIN BattingScore b ON p.player_id = b.player_id
                    LEFT JOIN MatchFormatYear mf ON b.match_id = mf.match_id
                    GROUP BY p.player_id, p.full_name
                    HAVING SUM(1) >= 20
                    ORDER BY total_matches DESC;"""
        },
        21: {
            "text": "Create a comprehensive performance ranking system for players combining batting, bowling, and fielding into a single weighted score.",
            "sql": """SELECT
                            p.player_id,
                            p.full_name AS player_name,
                            SUM(b.runs) AS total_runs,
                            ROUND(AVG(b.runs)::NUMERIC, 2) AS batting_average,
                            ROUND(AVG(b.strike_rate)::NUMERIC, 2) AS strike_rate,
                            SUM(bs.wickets) AS total_wickets,
                            ROUND(
                                CASE WHEN SUM(bs.wickets) > 0 
                                    THEN SUM(bs.runs)::NUMERIC / SUM(bs.wickets)::NUMERIC
                                    ELSE 0
                                END, 2
                            ) AS bowling_average,
                            ROUND(
                                CASE WHEN SUM(bs.overs) > 0 
                                    THEN SUM(bs.runs)::NUMERIC / SUM(bs.overs)::NUMERIC
                                    ELSE 0
                                END, 2
                            ) AS economy_rate,
                            SUM(fs.catches) AS total_catches,
                            SUM(fs.stumpings) AS total_stumpings,
                            ROUND(
                                (
                                    (SUM(b.runs)::NUMERIC * 0.01::NUMERIC)
                                    + (AVG(b.runs)::NUMERIC * 0.5::NUMERIC)
                                    + (AVG(b.strike_rate)::NUMERIC * 0.3::NUMERIC)
                                    + (SUM(bs.wickets)::NUMERIC * 2::NUMERIC)
                                    + ((50::NUMERIC - 
                                        (CASE WHEN SUM(bs.wickets) > 0 
                                            THEN SUM(bs.runs)::NUMERIC / SUM(bs.wickets)::NUMERIC
                                            ELSE 0::NUMERIC
                                        END)
                                    ) * 0.5::NUMERIC)
                                    + ((6::NUMERIC - 
                                        (CASE WHEN SUM(bs.overs) > 0 
                                            THEN SUM(bs.runs)::NUMERIC / SUM(bs.overs)::NUMERIC
                                            ELSE 0::NUMERIC
                                        END)
                                    ) * 2::NUMERIC)
                                    + (SUM(fs.catches)::NUMERIC * 1::NUMERIC)
                                    + (SUM(fs.stumpings)::NUMERIC * 1::NUMERIC)
                                ), 2
                            ) AS performance_score
                        FROM Players p
                        LEFT JOIN BattingScore b ON p.player_id = b.player_id
                        LEFT JOIN BowlingScore bs ON p.player_id = bs.player_id
                        LEFT JOIN FieldingStats fs ON p.player_id = fs.player_id
                        GROUP BY p.player_id, p.full_name
                        ORDER BY performance_score DESC;"""
        },
        22: {
            "text": "Build a head-to-head match prediction analysis between teams. Calculate wins, average victory margins, and overall win percentages for teams with at least 5 matches against each other in the last 3 years.",
            "sql": """WITH recent_matches AS (
                        SELECT *
                        FROM Matches
                        WHERE TO_TIMESTAMP(start_time::BIGINT / 1000) >= CURRENT_DATE - INTERVAL '3 years'
                    ),
                    team_pairs AS (
                        SELECT 
                            LEAST(team1id, team2id) AS team_a_id, 
                            GREATEST(team1id, team2id) AS team_b_id, 
                            COUNT(*) AS total_matches
                        FROM recent_matches
                        GROUP BY LEAST(team1id, team2id), GREATEST(team1id, team2id)
                        HAVING COUNT(*) >= 5
                    )
                    SELECT
                        t.team_name AS team_a,
                        t2.team_name AS team_b,
                        tp.total_matches,
                        SUM(CASE WHEN m.winner_team_id = tp.team_a_id THEN 1 ELSE 0 END) AS team_a_wins,
                        SUM(CASE WHEN m.winner_team_id = tp.team_b_id THEN 1 ELSE 0 END) AS team_b_wins,
                        AVG(CASE WHEN m.victory_type = 'runs' THEN m.victory_margin::FLOAT END) AS avg_victory_margin_runs,
                        AVG(CASE WHEN m.victory_type = 'wickets' THEN m.victory_margin::FLOAT END) AS avg_victory_margin_wickets
                    FROM team_pairs tp
                    JOIN Matches m 
                        ON (m.team1id = tp.team_a_id AND m.team2id = tp.team_b_id) 
                        OR (m.team1id = tp.team_b_id AND m.team2id = tp.team_a_id)
                    JOIN Teams t ON tp.team_a_id = t.team_id
                    JOIN Teams t2 ON tp.team_b_id = t2.team_id
                    GROUP BY tp.team_a_id, tp.team_b_id, tp.total_matches, t.team_name, t2.team_name;"""
        },
        23: {
            "text": "Evaluate the impact of player form on match outcomes. For each player, determine the correlation between their runs in the last 5 matches and their team's win in the next match.",
            "sql": """WITH last_5_matches AS (
                        SELECT 
                            player_id, 
                            match_id, 
                            runs,
                            LEAD(match_id) OVER (PARTITION BY player_id ORDER BY match_id) AS next_match_id
                        FROM BattingScore
                    )
                    SELECT
                        l5.player_id,
                        p.full_name AS player_name,
                        CORR(l5.runs, CASE WHEN m_next.winner_team_id = bs.team_id THEN 1 ELSE 0 END) AS performance_correlation
                    FROM last_5_matches l5
                    JOIN Players p ON l5.player_id = p.player_id
                    JOIN BattingScore bs ON l5.player_id = bs.player_id AND l5.next_match_id = bs.match_id
                    JOIN Matches m_next ON l5.next_match_id = m_next.match_id
                    GROUP BY l5.player_id, p.full_name;"""
        },
        24: {
            "text": "Assess team consistency across formats. Calculate each team's win percentage in Test, ODI, and T20I formats over the last 5 years.",
            "sql": """SELECT 
                            t.team_name,
                            mf.format,
                            COUNT(*) AS total_matches,
                            SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS matches_won,
                            ROUND(
                                100.0 * SUM(CASE WHEN m.winner_team_id = t.team_id THEN 1 ELSE 0 END) / COUNT(*), 
                                2
                            ) AS win_percentage
                        FROM Teams t
                        JOIN Matches m ON t.team_id IN (m.team1id, m.team2id)
                        JOIN MatchFormatYear mf ON m.match_id = mf.match_id
                        WHERE EXTRACT(YEAR FROM TO_TIMESTAMP((m.start_time::bigint) / 1000)) >= EXTRACT(YEAR FROM CURRENT_DATE) - 5
                        GROUP BY t.team_name, mf.format
                        ORDER BY t.team_name, mf.format;"""
        },
        25: {
            "text": "Predict potential top performers for upcoming matches. Rank players based on their past 1-year performance metrics including batting average, strike rate, wickets taken, economy rate, and fielding contributions.",
            "sql": """WITH past_year AS (
                                SELECT *
                                FROM Matches
                                WHERE TO_TIMESTAMP(start_time::bigint / 1000) >= CURRENT_DATE - INTERVAL '1 year'
                            )
                            SELECT
                                p.player_id,
                                p.full_name AS player_name,
                                SUM(b.runs) AS total_runs,
                                AVG(b.runs) AS batting_average,
                                AVG(b.strike_rate) AS strike_rate,
                                SUM(bs.wickets) AS total_wickets,
                                ROUND((SUM(bs.runs) / NULLIF(SUM(bs.overs),0))::numeric, 2) AS economy_rate,
                                SUM(fs.catches + fs.stumpings) AS fielding_contribution,
                                ROUND(
                                    (
                                        AVG(b.runs)*0.4 
                                        + AVG(b.strike_rate)*0.2 
                                        + SUM(bs.wickets)*0.25 
                                        + (SUM(bs.runs) / NULLIF(SUM(bs.overs),0))*0.1 
                                        + SUM(fs.catches + fs.stumpings)*0.05
                                    )::numeric, 2
                                ) AS predicted_score
                            FROM Players p
                            LEFT JOIN BattingScore b ON p.player_id = b.player_id
                            LEFT JOIN BowlingScore bs ON p.player_id = bs.player_id
                            LEFT JOIN FieldingStats fs ON p.player_id = fs.player_id
                            LEFT JOIN past_year m ON b.match_id = m.match_id OR bs.match_id = m.match_id OR fs.match_id = m.match_id
                            GROUP BY p.player_id, p.full_name
                            ORDER BY predicted_score DESC;"""
        }
    }


    # ----------------------------
    # 3️⃣ Sidebar: Select Question
    # ----------------------------
    st.sidebar.title("Select SQL Question")
    question_id = st.sidebar.selectbox("Choose a question", list(questions.keys()))

    # ----------------------------
    # 4️⃣ Display Selected Question
    # ----------------------------
    st.title(f"Question {question_id}")
    st.write(questions[question_id]["text"])

    # ----------------------------
    # 5️⃣ Optionally Show SQL Code
    # ----------------------------
    show_code = st.checkbox("View SQL code for this question?")
    if show_code:
        st.code(questions[question_id]["sql"], language="sql")

    # ----------------------------
    # 6️⃣ Execute SQL and Show Results
    # ----------------------------
    try:
        df = pd.read_sql_query(questions[question_id]["sql"], conn)
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error executing SQL: {e}")

    # ----------------------------
    # 7️⃣ About Page (Default)
    # ----------------------------
    with st.expander("About this App"):
        st.info("""
        This Streamlit app allows users to explore cricket data using SQL queries.
        - Select a question from the sidebar
        - View the SQL query (optional)
        - See the results directly from the SQLite database
        Data is fetched from Cricbuzz APIs and stored in local SQLite tables.
        """)

    # ----------------------------
    # 8️⃣ Close DB connection on exit
    # ----------------------------
    conn.close()


# ------------------------------
# 📌 Page 4: Crud Operations
# ------------------------------

def crud_operations():
    # Connect to database (or create if it doesn't exist)
    conn = sqlite3.connect('players.db')
    c = conn.cursor()

    # Create table if not exists
    c.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        runs INTEGER
    )
    ''')
    conn.commit()

    st.title("Player Management (CRUD Operations)")

    operation = st.selectbox("Choose Operation", ["Read", "Create", "Update", "Delete"])

# Helper function to display current table
    def show_table():
        c.execute("SELECT * FROM players")
        data = c.fetchall()
        if data:
            st.subheader("Current Player Records")
            st.table(data)
        else:
            st.info("No records found.")

    if operation == "Read":
        show_table()

    # --- CREATE ---
    elif operation == "Create":
        st.subheader("Add New Player")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        runs = st.number_input("Runs", min_value=0, step=1)

        if st.button("Add Player"):
            if first_name and last_name:
                c.execute("INSERT INTO players (first_name, last_name, runs) VALUES (?, ?, ?)",
                          (first_name, last_name, runs))
                conn.commit()
                st.success(f"Player {first_name} {last_name} added successfully!")
                show_table()
            else:
                st.error("Please enter both first and last name.")
     # --- UPDATE ---
    elif operation == "Update":
        c.execute("SELECT first_name, last_name, runs FROM players")
        players = c.fetchall()
        if players:
        # Create dropdown with tuples (first_name, last_name)
           player_selection = st.selectbox(
            "Select Player to Update",
            players,  # directly use tuples
            format_func=lambda x: f"{x[0]} {x[1]}" if x[1] else x[0]  # show nicely
        )
        selected_first_name, selected_last_name, selected_runs = player_selection

        new_first_name = st.text_input("New First Name", selected_first_name)
        new_last_name = st.text_input("New Last Name", selected_last_name)
        new_runs = st.number_input("New Runs", min_value=0, step=1, value=selected_runs)

        if st.button("Update Player"):
            c.execute("""
                UPDATE players
                SET first_name=?, last_name=?, runs=?
                WHERE first_name=? AND last_name=?
            """, (new_first_name, new_last_name, new_runs,
                  selected_first_name, selected_last_name))
            conn.commit()
            st.success(f"Player {selected_first_name} {selected_last_name} updated successfully!")
            show_table()
        else:
            st.info("No players to update.")

# --- DELETE ---
    elif operation == "Delete":
         c.execute("SELECT first_name, last_name FROM players")
         players = c.fetchall()
         if players:
            player_selection = st.selectbox(
            "Select Player to Delete",
            players,
            format_func=lambda x: f"{x[0]} {x[1]}" if x[1] else x[0]
        )
         selected_first_name, selected_last_name = player_selection

         if st.button("Delete Player"):
            c.execute("""
                DELETE FROM players
                WHERE first_name=? AND last_name=?
            """, (selected_first_name, selected_last_name))
            conn.commit()
            st.success(f"Player {selected_first_name} {selected_last_name} deleted successfully!")
            show_table()
         else:
             st.info("No players to delete.")

    conn.close()

# ------------------------------
# 📌 Sidebar Navigation
# ------------------------------
st.sidebar.title("🏏 Cricket Dashboard")
page = st.sidebar.radio("Navigate", ["Home", "Live Scores", "Player Stats","SQL Questions","Crud Operations"])

if page == "Home":
    st.title("🏏 Cricbuzz LiveStats")
    st.subheader("Real-Time Cricket Insights & SQL-Based Analytics")
    st.markdown("### 📝 About This Project")
    st.info("""
    This is my first project where I created a **cricket analytics website** using Streamlit and the Cricbuzz API.  

    Features include:  
    - Explore **live, recent, and upcoming matches** (similar to Cricbuzz)  
    - **Search for players** to see detailed profiles  
    - Run **SQL queries** related to cricket data  
    - **CRUD page:** A game page where you can add, delete, and update records as many times as you like
    """)
    st.markdown("### 📌 Skills & Domain")
    col1, col2 = st.columns(2)

    with col1:
        st.success("💡 Skills Learned")
        st.write("""
        - REST API Integration  
        - JSON Analytics  
        - Python Programming  
        - SQL & Pandas  
        - Streamlit Web App Development
        """)

    with col2:
        st.success("🏷️ Domain")
        st.write("""
        - Sports Analytics """)


    st.subheader("Link To Project Documentation 📁 ")

    st.link_button(" Open Project Document 📂 ", "https://docs.google.com/document/d/1LpjVvTTespcAdsF9gWe2KGQORHTBoBh95MH4hpVGvus/edit?tab=t.0")

elif page == "Live Scores":
    live_scores()

elif page == "Player Stats":
    player_stats()
elif page == "SQL Questions":
    SQL_Questions()
elif page == "Crud Operations":
    crud_operations()

# import pandas as pd

# import requests

# url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"

# headers = {
# 	"x-rapidapi-key": "7ee193bd09mshd975546ea0e50bcp1756fbjsnb79a9ed72db8",
# 	"x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
# }

# response = requests.get(url, headers=headers)

# data = (response.json())


# matches = []

# match_map = {}  # Store matchId -> match info
# for type_match in data.get("typeMatches", []):
#     for series in type_match.get("seriesMatches", []):
#         series_data = series.get("seriesAdWrapper", {})
#         for match in series_data.get("matches", []):
#             info = match.get("matchInfo", {})
#             team1 = info.get("team1", {}).get("teamName", "")
#             team2 = info.get("team2", {}).get("teamName", "")
#             match_id = info.get("matchId")
#             status = info.get("status")
#             matches.append({
#                 'Series': series_data,
#                 'Team1': team1,
#                 'Team2': team2,
#                 'Status': status
#             })

# df = pd.DataFrame(matches)
# import streamlit as st
# st.dataframe(df)
