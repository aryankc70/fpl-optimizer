CREATE OR REPLACE VIEW player_rolling_form AS
SELECT
    s.id AS stat_id,
    s.player_id,
    s.season,
    s.gameweek_id,
    s.total_points,
    s.minutes,
    s.value,

    AVG(s.total_points) OVER w3 AS avg_points_last_3,
    AVG(s.minutes)      OVER w3 AS avg_minutes_last_3,
    AVG(s.expected_goals)   OVER w3 AS avg_xg_last_3,
    AVG(s.expected_assists) OVER w3 AS avg_xa_last_3,

    AVG(s.total_points) OVER w5 AS avg_points_last_5,
    STDDEV(s.total_points) OVER w5 AS std_points_last_5,

    COUNT(*) OVER w5 AS games_in_window_5
FROM player_gameweek_stats s
WINDOW
    w3 AS (
        PARTITION BY s.player_id
        ORDER BY s.season, s.gameweek_id
        ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
    ),
    w5 AS (
        PARTITION BY s.player_id
        ORDER BY s.season, s.gameweek_id
        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
    );