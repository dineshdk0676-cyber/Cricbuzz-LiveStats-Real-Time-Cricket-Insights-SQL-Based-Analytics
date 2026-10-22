"""The 25 documented SQL practice and analytics queries."""

QUERIES = {
    1: ("Indian players", """SELECT p.name, p.role, p.batting_style, p.bowling_style
        FROM players p JOIN teams t ON t.id=p.team_id WHERE t.country='India' ORDER BY p.name"""),
    2: ("Matches in last 30 days", """SELECT m.description, t1.name AS team1, t2.name AS team2,
        v.name AS venue, v.city, m.match_date FROM matches m
        JOIN teams t1 ON t1.id=m.team1_id JOIN teams t2 ON t2.id=m.team2_id
        JOIN venues v ON v.id=m.venue_id
        WHERE date(m.match_date) >= date('now','-30 days')
        ORDER BY m.match_date DESC"""),
    3: ("Top ODI run scorers", """SELECT p.name, SUM(b.runs) AS total_runs,
        ROUND(1.0*SUM(b.runs)/NULLIF(SUM(b.is_out),0),2) AS batting_average,
        SUM(CASE WHEN b.runs>=100 THEN 1 ELSE 0 END) AS centuries
        FROM batting_innings b JOIN players p ON p.id=b.player_id JOIN matches m ON m.id=b.match_id
        WHERE m.format='ODI' GROUP BY p.id ORDER BY total_runs DESC LIMIT 10"""),
    4: ("Large cricket venues", """SELECT name,city,country,capacity FROM venues
        WHERE capacity>50000 ORDER BY capacity DESC"""),
    5: ("Wins by team", """SELECT t.name,COUNT(m.id) AS total_wins FROM teams t
        LEFT JOIN matches m ON m.winner_team_id=t.id GROUP BY t.id ORDER BY total_wins DESC"""),
    6: ("Players by role", """SELECT role,COUNT(*) AS player_count FROM players
        GROUP BY role ORDER BY player_count DESC,role"""),
    7: ("Highest innings by format", """SELECT m.format,MAX(b.runs) AS highest_score
        FROM batting_innings b JOIN matches m ON m.id=b.match_id
        GROUP BY m.format ORDER BY m.format"""),
    8: ("Series started in 2024", """SELECT s.name,s.host_country,s.format,s.start_date,
        s.planned_matches FROM series s WHERE strftime('%Y',s.start_date)='2024'"""),
    9: ("All-rounders with 1,000 runs and 50 wickets", """WITH batting AS (
        SELECT b.player_id,m.format,SUM(b.runs) runs FROM batting_innings b
        JOIN matches m ON m.id=b.match_id GROUP BY b.player_id,m.format),
        bowling AS (SELECT bf.player_id,m.format,SUM(bf.wickets) wickets FROM bowling_figures bf
        JOIN matches m ON m.id=bf.match_id GROUP BY bf.player_id,m.format)
        SELECT p.name,bat.format,bat.runs total_runs,bowl.wickets total_wickets
        FROM players p JOIN batting bat ON bat.player_id=p.id
        JOIN bowling bowl ON bowl.player_id=p.id AND bowl.format=bat.format
        WHERE p.role='All-rounder' AND bat.runs>1000 AND bowl.wickets>50
        ORDER BY total_runs DESC"""),
    10: ("Last 20 completed matches", """SELECT m.description,t1.name team1,t2.name team2,
        winner.name winner,m.win_margin_runs,m.win_margin_wickets,v.name venue,m.match_date
        FROM matches m JOIN teams t1 ON t1.id=m.team1_id JOIN teams t2 ON t2.id=m.team2_id
        JOIN venues v ON v.id=m.venue_id LEFT JOIN teams winner ON winner.id=m.winner_team_id
        WHERE m.status='Completed' ORDER BY m.match_date DESC LIMIT 20"""),
    11: ("Player records across formats", """WITH formats AS (
        SELECT b.player_id,m.format,SUM(b.runs) runs,SUM(b.is_out) dismissals
        FROM batting_innings b JOIN matches m ON m.id=b.match_id
        GROUP BY b.player_id,m.format)
        SELECT p.name,
        SUM(CASE WHEN f.format='Test' THEN f.runs ELSE 0 END) test_runs,
        SUM(CASE WHEN f.format='ODI' THEN f.runs ELSE 0 END) odi_runs,
        SUM(CASE WHEN f.format='T20I' THEN f.runs ELSE 0 END) t20i_runs,
        ROUND(1.0*SUM(f.runs)/NULLIF(SUM(f.dismissals),0),2) overall_batting_average,
        COUNT(DISTINCT f.format) formats_played
        FROM formats f JOIN players p ON p.id=f.player_id GROUP BY p.id
        HAVING COUNT(DISTINCT f.format)>=2 ORDER BY p.name"""),
    12: ("Home vs away wins", """WITH appearances AS (
        SELECT m.id match_id,m.winner_team_id,m.match_date,v.country venue_country,
        m.team1_id team_id FROM matches m JOIN venues v ON v.id=m.venue_id
        WHERE v.country!='Unknown'
        UNION ALL SELECT m.id,m.winner_team_id,m.match_date,v.country,m.team2_id
        FROM matches m JOIN venues v ON v.id=m.venue_id WHERE v.country!='Unknown')
        SELECT t.name,CASE WHEN t.country=a.venue_country THEN 'Home' ELSE 'Away' END condition,
        SUM(CASE WHEN a.winner_team_id=a.team_id THEN 1 ELSE 0 END) wins
        FROM appearances a JOIN teams t ON t.id=a.team_id
        GROUP BY t.id,condition ORDER BY t.name,condition"""),
    13: ("100-run adjacent batter pairs", """WITH scores AS (
        SELECT b.match_id,b.innings_no,b.team_id,b.batting_position,b.player_id,b.runs,
        m.description FROM batting_innings b JOIN matches m ON m.id=b.match_id)
        SELECT p1.name batter1,p2.name batter2,a.runs+b.runs partnership_runs,
        a.innings_no,a.description FROM scores a JOIN scores b
        ON a.match_id=b.match_id AND a.innings_no=b.innings_no AND a.team_id=b.team_id
        AND b.batting_position=a.batting_position+1
        JOIN players p1 ON p1.id=a.player_id JOIN players p2 ON p2.id=b.player_id
        WHERE a.runs+b.runs>=100 ORDER BY partnership_runs DESC"""),
    14: ("Venue bowling analysis", """WITH by_match AS (
        SELECT bf.player_id,m.venue_id,m.id match_id,SUM(bf.balls_bowled) balls,
        SUM(bf.runs_conceded) runs,SUM(bf.wickets) wickets FROM bowling_figures bf
        JOIN matches m ON m.id=bf.match_id GROUP BY bf.player_id,m.venue_id,m.id
        HAVING SUM(bf.balls_bowled)>=24)
        SELECT p.name,v.name venue,ROUND(6.0*SUM(x.runs)/NULLIF(SUM(x.balls),0),2) economy,
        SUM(x.wickets) wickets,COUNT(*) matches FROM by_match x
        JOIN players p ON p.id=x.player_id JOIN venues v ON v.id=x.venue_id
        GROUP BY p.id,v.id HAVING COUNT(*)>=3 ORDER BY economy"""),
    15: ("Player performance in close matches", """WITH close_matches AS (
        SELECT * FROM matches WHERE (win_margin_runs BETWEEN 1 AND 49)
        OR (win_margin_wickets BETWEEN 1 AND 4))
        SELECT p.name,ROUND(AVG(b.runs),2) avg_runs,COUNT(DISTINCT m.id) close_matches,
        SUM(CASE WHEN m.winner_team_id=b.team_id THEN 1 ELSE 0 END) team_wins_when_batted
        FROM batting_innings b JOIN close_matches m ON m.id=b.match_id
        JOIN players p ON p.id=b.player_id GROUP BY p.id
        ORDER BY avg_runs DESC"""),
    16: ("Yearly batting trends since 2020", """SELECT p.name,strftime('%Y',m.match_date) year,
        ROUND(AVG(b.runs),2) avg_runs_per_match,
        ROUND(100.0*SUM(b.runs)/NULLIF(SUM(b.balls_faced),0),2) avg_strike_rate,
        COUNT(DISTINCT m.id) matches FROM batting_innings b
        JOIN matches m ON m.id=b.match_id JOIN players p ON p.id=b.player_id
        WHERE m.match_date>=date('2020-01-01') GROUP BY p.id,year
        HAVING COUNT(DISTINCT m.id)>=5 ORDER BY year DESC,avg_runs_per_match DESC"""),
    17: ("Toss-winning team match win rate", """SELECT toss_decision,
        COUNT(*) matches,ROUND(100.0*SUM(CASE WHEN winner_team_id=toss_winner_team_id THEN 1 ELSE 0 END)
        /NULLIF(COUNT(*),0),2) win_percentage FROM matches
        WHERE status='Completed' AND toss_winner_team_id IS NOT NULL
        GROUP BY toss_decision ORDER BY toss_decision"""),
    18: ("Economical limited-overs bowlers", """WITH player_matches AS (
        SELECT bf.player_id,m.id match_id,SUM(bf.balls_bowled) balls,
        SUM(bf.runs_conceded) runs,SUM(bf.wickets) wickets FROM bowling_figures bf
        JOIN matches m ON m.id=bf.match_id WHERE m.format IN ('ODI','T20I')
        GROUP BY bf.player_id,m.id)
        SELECT p.name,ROUND(6.0*SUM(x.runs)/NULLIF(SUM(x.balls),0),2) economy,
        SUM(x.wickets) wickets,COUNT(*) matches,ROUND(1.0*SUM(x.balls)/COUNT(*),1) balls_per_match
        FROM player_matches x JOIN players p ON p.id=x.player_id GROUP BY p.id
        HAVING COUNT(*)>=10 AND 1.0*SUM(x.balls)/COUNT(*)>=12 ORDER BY economy"""),
    19: ("Consistent batters since 2022", """SELECT p.name,ROUND(AVG(b.runs),2) average_runs,
        ROUND(SQRT(AVG(b.runs*b.runs)-AVG(b.runs)*AVG(b.runs)),2) stddev_runs,
        COUNT(*) innings FROM batting_innings b JOIN matches m ON m.id=b.match_id
        JOIN players p ON p.id=b.player_id WHERE m.match_date>=date('2022-01-01')
        AND b.balls_faced>=10 GROUP BY p.id HAVING COUNT(*)>=10 ORDER BY stddev_runs"""),
    20: ("Format matches and batting averages", """WITH format_stats AS (
        SELECT b.player_id,m.format,COUNT(DISTINCT m.id) matches,SUM(b.runs) runs,SUM(b.is_out) outs
        FROM batting_innings b JOIN matches m ON m.id=b.match_id
        GROUP BY b.player_id,m.format)
        SELECT p.name,
        SUM(CASE WHEN f.format='Test' THEN f.matches ELSE 0 END) test_matches,
        ROUND(1.0*SUM(CASE WHEN f.format='Test' THEN f.runs ELSE 0 END)/
        NULLIF(SUM(CASE WHEN f.format='Test' THEN f.outs ELSE 0 END),0),2) test_average,
        SUM(CASE WHEN f.format='ODI' THEN f.matches ELSE 0 END) odi_matches,
        ROUND(1.0*SUM(CASE WHEN f.format='ODI' THEN f.runs ELSE 0 END)/
        NULLIF(SUM(CASE WHEN f.format='ODI' THEN f.outs ELSE 0 END),0),2) odi_average,
        SUM(CASE WHEN f.format='T20I' THEN f.matches ELSE 0 END) t20_matches,
        ROUND(1.0*SUM(CASE WHEN f.format='T20I' THEN f.runs ELSE 0 END)/
        NULLIF(SUM(CASE WHEN f.format='T20I' THEN f.outs ELSE 0 END),0),2) t20_average,
        SUM(f.matches) total_matches FROM format_stats f JOIN players p ON p.id=f.player_id
        GROUP BY p.id HAVING SUM(f.matches)>=20 ORDER BY p.name"""),
    21: ("Weighted player performance rankings", """WITH bat AS (
        SELECT b.player_id,m.format,SUM(b.runs) runs,
        1.0*SUM(b.runs)/NULLIF(SUM(b.is_out),0) avg_runs,
        100.0*SUM(b.runs)/NULLIF(SUM(b.balls_faced),0) strike_rate
        FROM batting_innings b JOIN matches m ON m.id=b.match_id GROUP BY b.player_id,m.format),
        bowl AS (SELECT bf.player_id,m.format,SUM(bf.wickets) wickets,
        1.0*SUM(bf.runs_conceded)/NULLIF(SUM(bf.wickets),0) bowling_average,
        6.0*SUM(bf.runs_conceded)/NULLIF(SUM(bf.balls_bowled),0) economy
        FROM bowling_figures bf JOIN matches m ON m.id=bf.match_id GROUP BY bf.player_id,m.format),
        field AS (SELECT ff.player_id,m.format,SUM(ff.catches) catches,SUM(ff.stumpings) stumpings
        FROM fielding_figures ff JOIN matches m ON m.id=ff.match_id GROUP BY ff.player_id,m.format)
        , scored AS (SELECT p.name,bat.format,ROUND(COALESCE(bat.runs,0)*0.01+COALESCE(bat.avg_runs,0)*0.5+
        COALESCE(bat.strike_rate,0)*0.3+COALESCE(bowl.wickets,0)*2+
        COALESCE((50-bowl.bowling_average)*0.5,0)+COALESCE((6-bowl.economy)*2,0)+
        COALESCE(field.catches,0)*3+COALESCE(field.stumpings,0)*5,2) score
        FROM bat JOIN players p ON p.id=bat.player_id
        LEFT JOIN bowl ON bowl.player_id=bat.player_id AND bowl.format=bat.format
        LEFT JOIN field ON field.player_id=bat.player_id AND field.format=bat.format),
        ranked AS (SELECT *,RANK() OVER(PARTITION BY format ORDER BY score DESC) rank
        FROM scored)
        SELECT name,format,score,rank FROM ranked ORDER BY format,rank"""),
    22: ("Head-to-head by venue over three years", """WITH venue_results AS (
        SELECT m.team1_id,m.team2_id,m.venue_id,COUNT(*) matches,
        SUM(CASE WHEN m.winner_team_id=m.team1_id THEN 1 ELSE 0 END) team1_wins,
        SUM(CASE WHEN m.winner_team_id=m.team2_id THEN 1 ELSE 0 END) team2_wins,
        SUM(CASE WHEN ((m.toss_decision='bat' AND m.toss_winner_team_id=m.team1_id)
        OR (m.toss_decision='field' AND m.toss_winner_team_id=m.team2_id))
        AND m.winner_team_id=m.team1_id THEN 1
        WHEN ((m.toss_decision='bat' AND m.toss_winner_team_id=m.team2_id)
        OR (m.toss_decision='field' AND m.toss_winner_team_id=m.team1_id))
        AND m.winner_team_id=m.team2_id THEN 1 ELSE 0 END) batting_first_wins,
        SUM(CASE WHEN m.winner_team_id IS NOT NULL AND NOT
        (((m.toss_decision='bat' AND m.toss_winner_team_id=m.team1_id)
        OR (m.toss_decision='field' AND m.toss_winner_team_id=m.team2_id))
        AND m.winner_team_id=m.team1_id) AND NOT
        (((m.toss_decision='bat' AND m.toss_winner_team_id=m.team2_id)
        OR (m.toss_decision='field' AND m.toss_winner_team_id=m.team1_id))
        AND m.winner_team_id=m.team2_id) THEN 1 ELSE 0 END) bowling_first_wins
        FROM matches m WHERE m.match_date>=date('now','-3 years')
        GROUP BY m.team1_id,m.team2_id,m.venue_id),
        paired AS (SELECT *,SUM(matches) OVER(PARTITION BY team1_id,team2_id) pair_matches
        FROM venue_results)
        SELECT t1.name team,t2.name opponent,v.name venue,x.matches,
        x.team1_wins,x.team2_wins,x.batting_first_wins,x.bowling_first_wins,
        ROUND(100.0*x.team1_wins/NULLIF(x.matches,0),2) team1_win_pct
        FROM paired x JOIN teams t1 ON t1.id=x.team1_id JOIN teams t2 ON t2.id=x.team2_id
        JOIN venues v ON v.id=x.venue_id WHERE x.pair_matches>=5
        ORDER BY team,opponent,venue"""),
    23: ("Recent player form", """WITH recent AS (
        SELECT b.player_id,b.match_id,b.runs,b.balls_faced,m.match_date,
        ROW_NUMBER() OVER(PARTITION BY b.player_id ORDER BY m.match_date DESC,m.id DESC) rn
        FROM batting_innings b JOIN matches m ON m.id=b.match_id)
        SELECT p.name,ROUND(AVG(CASE WHEN r.rn<=5 THEN r.runs END),2) avg_last_5,
        ROUND(AVG(r.runs),2) avg_last_10,
        ROUND(100.0*SUM(r.runs)/NULLIF(SUM(r.balls_faced),0),2) strike_rate,
        SUM(CASE WHEN r.runs>=50 THEN 1 ELSE 0 END) scores_50_plus,
        ROUND(SQRT(AVG(r.runs*r.runs)-AVG(r.runs)*AVG(r.runs)),2) consistency_stddev,
        CASE WHEN AVG(r.runs)>=40 THEN 'Excellent Form'
             WHEN AVG(r.runs)>=25 THEN 'Good Form'
             WHEN AVG(r.runs)>=12 THEN 'Average Form' ELSE 'Poor Form' END form
        FROM recent r JOIN players p ON p.id=r.player_id WHERE r.rn<=10
        GROUP BY p.id HAVING COUNT(*)>=10 ORDER BY avg_last_5 DESC"""),
    24: ("Successful consecutive batting partnerships", """WITH pairs AS (
        SELECT a.match_id,a.innings_no,a.player_id player1,b.player_id player2,
        a.runs+b.runs runs FROM batting_innings a JOIN batting_innings b
        ON a.match_id=b.match_id AND a.innings_no=b.innings_no AND a.team_id=b.team_id
        AND b.batting_position=a.batting_position+1)
        SELECT p1.name batter1,p2.name batter2,ROUND(AVG(x.runs),2) avg_runs,
        SUM(CASE WHEN x.runs>50 THEN 1 ELSE 0 END) partnerships_over_50,
        MAX(x.runs) highest,ROUND(100.0*SUM(CASE WHEN x.runs>50 THEN 1 ELSE 0 END)/COUNT(*),2) success_pct,
        COUNT(*) partnerships FROM pairs x JOIN players p1 ON p1.id=x.player1
        JOIN players p2 ON p2.id=x.player2 GROUP BY x.player1,x.player2
        HAVING COUNT(*)>=5 ORDER BY success_pct DESC,avg_runs DESC"""),
    25: ("Quarterly performance trajectory", """WITH quarterly AS (
        SELECT b.player_id,strftime('%Y',m.match_date) year,
        ((CAST(strftime('%m',m.match_date) AS INTEGER)-1)/3)+1 quarter,
        ROUND(AVG(b.runs),2) avg_runs,
        ROUND(100.0*SUM(b.runs)/NULLIF(SUM(b.balls_faced),0),2) strike_rate,
        COUNT(DISTINCT m.id) matches FROM batting_innings b
        JOIN matches m ON m.id=b.match_id GROUP BY b.player_id,year,quarter
        HAVING COUNT(DISTINCT m.id)>=3),
        trend AS (SELECT *,LAG(avg_runs) OVER(PARTITION BY player_id ORDER BY year,quarter) previous_avg,
        COUNT(*) OVER(PARTITION BY player_id) quarter_count
        FROM quarterly)
        SELECT p.name,t.year,t.quarter,t.avg_runs,t.strike_rate,t.matches,
        CASE WHEN t.previous_avg IS NULL THEN 'First quarter'
             WHEN t.avg_runs>t.previous_avg*1.05 THEN 'Improving'
             WHEN t.avg_runs<t.previous_avg*0.95 THEN 'Declining' ELSE 'Stable' END quarter_trend,
        CASE WHEN t.quarter_count<6 THEN 'Insufficient history'
             WHEN AVG(t.avg_runs) OVER(PARTITION BY t.player_id ORDER BY t.year,t.quarter
                  ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) >
                  AVG(t.avg_runs) OVER(PARTITION BY t.player_id ORDER BY t.year,t.quarter
                  ROWS BETWEEN 5 PRECEDING AND 3 PRECEDING) THEN 'Career Ascending'
             WHEN AVG(t.avg_runs) OVER(PARTITION BY t.player_id ORDER BY t.year,t.quarter
                  ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) <
                  AVG(t.avg_runs) OVER(PARTITION BY t.player_id ORDER BY t.year,t.quarter
                  ROWS BETWEEN 5 PRECEDING AND 3 PRECEDING) THEN 'Career Declining'
             ELSE 'Career Stable' END career_phase
        FROM trend t JOIN players p ON p.id=t.player_id
        WHERE t.quarter_count>=6
        ORDER BY p.name,t.year,t.quarter"""),
}
