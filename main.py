# 1. Import necessary libraries
import streamlit as st
import pandas as pd
import pymysql
from pymysql.cursors import DictCursor
import plotly.express as px
import numpy as np

# 2. Function to create database connection
def create_connection():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='12345',
            db='police_log',
            port=3306,
            cursorclass=DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"Database Connection Error: {e} 🚨")
        return None

# 3. Function to fetch query results from DB
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return pd.DataFrame(result)
        except Exception as e:
            st.error(f"Error Fetching Data: {e} 🚫")
            return pd.DataFrame()
        finally:
            connection.close()
    else:
        return pd.DataFrame()

# 4. Page config
st.set_page_config(page_title="SecureCheck Police Dashboard 🚨", layout='wide')
st.title("SecureCheck: Police Check Post Digital Leader 🚨")
st.markdown("Real-time monitoring and insights for law enforcement 👮")

# 5. Show full dataset
st.header("Police Logs Overview 📊")
query = 'SELECT * FROM traffic_stop'
data = fetch_data(query)

if not data.empty:
    st.dataframe(data, use_container_width=True)
else:
    st.warning("No data available 🚫")

# 6. Display key metrics
st.header("Key Metrics 📈")
if not data.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Police Stops 🚨", data.shape[0])
    with col2:
        arrests = data[data['stop_outcome'].astype(str).str.contains('arrest', case=False, na=False)].shape[0]
        st.metric("Total Arrests 👮", arrests)
    with col3:
        warnings = data[data['stop_outcome'].astype(str).str.contains('warning', case=False, na=False)].shape[0]
        st.metric("Total Warnings ⚠️", warnings)
    with col4:
        drug_related = data[data['drugs_related_stop'].astype(int) == 1].shape[0]
        st.metric("Drugs Related Stops 💊", drug_related)
else:
    st.warning("No data available for metrics 🚫")

# 7. Visual insights tabs
st.header("Visual Insights 📊")
tab1, tab2 = st.tabs(["Stops by Violation 🚨", "Driver Gender Distribution 👥"])

with tab1:
    if not data.empty and "violation" in data.columns:
        violation_counts = data["violation"].value_counts().reset_index()
        violation_counts.columns = ['violation', 'count']
        fig = px.bar(violation_counts, x='violation', y='count', title="Stops by Violation Type 🚨")
        fig.update_layout(xaxis_title="Violation", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for Violation Chart. 🚫")

with tab2:
    if not data.empty and 'driver_gender' in data.columns:
        gender_counts = data['driver_gender'].value_counts().reset_index()
        gender_counts.columns = ['gender', 'count']
        fig = px.pie(gender_counts, names='gender', values='count', title='Driver Gender Distribution 👥')
        fig.update_layout(legend_title="Gender")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for Driver Gender chart. 🚫")

# 8. Advanced Insights
st.header("Advanced Insights 🔍")

query_map = {
    # Basic Queries
    "1. Top 10 vehicle numbers involved in drug-related stops 🚨": """
        SELECT vehicle_number, COUNT(*) AS stop_count 
        FROM traffic_stop 
        WHERE drugs_related_stop = 1 
        GROUP BY vehicle_number 
        ORDER BY stop_count DESC 
        LIMIT 10;
    """,

    "2. Top 10 vehicles most frequently searched 🔍": """
        SELECT vehicle_number, COUNT(*) AS search_count 
        FROM traffic_stop 
        WHERE search_conducted = 1 
        GROUP BY vehicle_number 
        ORDER BY search_count DESC 
        LIMIT 10;
    """,

    # Demographic-Based Analysis
    "3. Driver age group with the highest arrest rate 👮": """
        SELECT 
            CASE 
                WHEN driver_age < 18 THEN '<18'
                WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
                WHEN driver_age BETWEEN 36 AND 50 THEN '36-50'
                ELSE '51+'
            END AS age_group,
            COUNT(*) AS arrest_count
        FROM traffic_stop
        WHERE is_arrested = 1 AND driver_age IS NOT NULL
        GROUP BY age_group
        ORDER BY arrest_count DESC;
    """,

    "4. Gender distribution of drivers stopped by country 🌎": """
        SELECT 
            country_name, 
            driver_gender, 
            COUNT(*) AS stop_count
        FROM traffic_stop
        WHERE driver_gender IS NOT NULL AND country_name IS NOT NULL
        GROUP BY country_name, driver_gender
        ORDER BY country_name, stop_count DESC;
    """,

    "5. Race and gender combination with the highest search rate 🔎": """
        SELECT 
            driver_race, 
            driver_gender,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS total_searches
        FROM traffic_stop
        GROUP BY driver_race, driver_gender
        ORDER BY total_searches DESC;
    """,

    # Time-Based Analysis
    "6. Time of day with the most traffic stops (by hour) ⏰": """
        SELECT 
            HOUR(stop_time) AS stop_hour,
            COUNT(*) AS stop_count
        FROM traffic_stop
        GROUP BY stop_hour
        ORDER BY stop_count DESC;
    """,

    "7. Are stops at night more likely to lead to arrests? 🌃": """
        SELECT
            CASE 
                WHEN HOUR(stop_time) >= 20 OR HOUR(stop_time) < 5 THEN 'Night'
                ELSE 'Day'
            END AS time_period,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrest_count,
            ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate_percent
        FROM traffic_stop
        GROUP BY time_period;
    """,

    # Violation-Based Analysis
    "8. Violations most associated with searches or arrests 🚨": """
        SELECT 
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests
        FROM traffic_stop
        GROUP BY violation
        ORDER BY searches DESC, arrests DESC;
    """,

    "9. Most common violations among younger drivers (<25) 👥": """
        SELECT 
            violation,
            COUNT(*) AS total_stops
        FROM traffic_stop
        WHERE driver_age < 25
        GROUP BY violation
        ORDER BY total_stops DESC;
    """,

    "10. Violations rarely resulting in search or arrest (low rates) 📉": """
        SELECT 
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
            ROUND(100.0 * SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS search_rate_percent,
            ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate_percent
        FROM traffic_stop
        GROUP BY violation
        ORDER BY search_rate_percent ASC, arrest_rate_percent ASC;
    """,

    # Location-Based Analysis
    "11. Countries with highest rate of drug-related stops 🌐": """
        SELECT 
            country_name,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) AS drug_stops,
            ROUND(100.0 * SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS drug_stop_rate_percent
        FROM traffic_stop
        GROUP BY country_name
        ORDER BY drug_stop_rate_percent DESC;
    """,

    "12. Arrest rate by country and violation 🚔": """
        SELECT 
            country_name,
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
            ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate_percent
        FROM traffic_stop
        GROUP BY country_name, violation
        ORDER BY arrest_rate_percent DESC;
    """,

    "13. Countries with the most stops where a search was conducted 🔍": """
        SELECT 
            country_name,
            COUNT(*) AS total_search_stops
        FROM traffic_stop
        WHERE search_conducted = 1
        GROUP BY country_name
        ORDER BY total_search_stops DESC;
    """,

    # Complex Analysis
    "14. Yearly breakdown of stops and arrests by country (with cumulative sums) 📆": """
        WITH yearly_data AS (
            SELECT 
                country_name,
                YEAR(stop_date) AS stop_year,
                COUNT(*) AS total_stops,
                SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests
            FROM traffic_stop
            GROUP BY country_name, YEAR(stop_date)
        )
        SELECT
            country_name,
            stop_year,
            total_stops,
            total_arrests,
            SUM(total_stops) OVER (PARTITION BY country_name ORDER BY stop_year) AS cumulative_stops,
            SUM(total_arrests) OVER (PARTITION BY country_name ORDER BY stop_year) AS cumulative_arrests
        FROM yearly_data
        ORDER BY country_name, stop_year;
    """,

    "15. Driver violation trends by age group and race 📈": """
        SELECT
            CASE
                WHEN driver_age < 18 THEN '<18'
                WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
                WHEN driver_age BETWEEN 36 AND 50 THEN '36-50'
                ELSE '51+'
            END AS age_group,
            driver_race,
            violation,
            COUNT(*) AS violation_count
        FROM traffic_stop
        GROUP BY age_group, driver_race, violation
        ORDER BY age_group, driver_race, violation_count DESC;
    """,

    "16. Number of stops by year, month, and hour of the day ⏰": """
        SELECT
            YEAR(stop_date) AS stop_year,
            MONTH(stop_date) AS stop_month,
            HOUR(stop_time) AS stop_hour,
            COUNT(*) AS total_stops
        FROM traffic_stop
        GROUP BY stop_year, stop_month, stop_hour
        ORDER BY stop_year, stop_month, stop_hour;
    """,

    "17. Violations with highest search and arrest rates, ranked by arrest rate 📊": """
        SELECT
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
            ROUND(100.0 * SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS search_rate_percent,
            ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate_percent,
            RANK() OVER (ORDER BY ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) DESC) AS arrest_rank
        FROM traffic_stop
        GROUP BY violation
        ORDER BY arrest_rank;
    """,

    "18. Driver demographics by country (age group, gender, race) 🌎": """
        SELECT
            country_name,
            CASE
                WHEN driver_age < 18 THEN '<18'
                WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                WHEN driver_age BETWEEN 26 AND 35 THEN '26-35'
                WHEN driver_age BETWEEN 36 AND 50 THEN '36-50'
                ELSE '51+'
            END AS age_group,
            driver_gender,
            driver_race,
            COUNT(*) AS driver_count
        FROM traffic_stop
        GROUP BY country_name, age_group, driver_gender, driver_race
        ORDER BY country_name, age_group, driver_gender, driver_race;
    """,

    "19. Top 5 violations with the highest arrest rates 🚨": """
        SELECT
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS total_arrests,
            ROUND(100.0 * SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate_percent
        FROM traffic_stop
        GROUP BY violation
        ORDER BY arrest_rate_percent DESC
        LIMIT 5;
    """
}

selected_query = st.selectbox("Select a Query to Run 🚀", list(query_map.keys()))

if st.button("Run Query 🚀"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("No data available for the selected query. 🚫")

st.markdown("---")
st.markdown("Built with ❤️ for Law Enforcement by SecureCheck 💻")

# 9. Custom Natural Language Filter (UI only)
st.header("Custom Natural Language Filter 🤖")
st.markdown("Fill in the details below to get a natural language prediction of the stop outcome based on existing data.")
stop_duration_options = data["stop_duration"].dropna().unique().tolist() if not data.empty else ["0-15 Min", "16-30 Min", "30+ Min"]

# 10. Add new log and predict outcome
st.header("Add New Police Log & Predict Outcome and Violation 📝")
with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date 📆")
    stop_time = st.time_input("Stop Time ⏰")
    country_name = st.text_input("Country Name 🌎")
    driver_gender = st.selectbox("Driver Gender 👥", ["male", "female"])
    driver_age = st.number_input("Driver Age 👴", min_value=16, max_value=100, value=27)
    driver_race = st.text_input("Driver Race 👥")
    search_conducted = st.selectbox("Was a Search Conducted? 🔍", ["0", "1"])
    drugs_related_stop = st.selectbox("Was it Drug Related? 💊", ["0", "1"])
    stop_duration = st.selectbox("Stop Duration ⏱️", stop_duration_options)
    vechicle_number = st.text_input("Vehicle Number 🚗")
    timestamp = pd.Timestamp.now()

    submitted = st.form_submit_button("Predict Stop Outcome & Violation 🤔")

    if submitted:
        filtered_data = data[
            (data['driver_gender'] == driver_gender) &
            (np.abs(data['driver_age'] - driver_age) <= 2) &
            (data['search_conducted'] == int(search_conducted)) &
            (data['stop_duration'] == stop_duration) &
            (data['drugs_related_stop'] == int(drugs_related_stop))
        ]

        if not filtered_data.empty:
            predicted_outcome = filtered_data['stop_outcome'].mode()[0]
            predicted_violation = filtered_data['violation'].mode()[0]
        else:
            predicted_outcome = "warning"
            predicted_violation = "speeding"

        search_text = "A search was conducted 🔍" if int(search_conducted) else "NO search was conducted 🚫"
        drug_text = "was drug-related 💊" if "was drug-related" else "was not drug related 🚫"

        st.markdown(f"""
        **Predicted Summary**
        
        - **Predicted Violation**: {predicted_violation} 🚨  
        - **Predicted Stop Outcome**: {predicted_outcome} 👮  
        A {driver_age}-year-old {driver_gender} driver in {country_name} was stopped at {stop_time.strftime('%I:%M %p')} on {stop_date}.  
        {search_text}, and the stop {drug_text}.  
        Stop Duration: **{stop_duration}** ⏱️  
        Vehicle Number: **{vechicle_number}** 🚗
        """)
