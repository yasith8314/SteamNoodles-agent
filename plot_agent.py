import sqlite3
from datetime import datetime
from langgraph.graph import StateGraph, START, END
import matplotlib.pyplot as plt
import re
import random

from helper import ask_llm

class PlotState(dict):
    date_range_prompt: str
    graph_type: str
    start_date: str
    end_date: str
    filtered_data: dict
    plot_path: str

def get_date_range(state: PlotState) -> PlotState:
    date_range_prompt = state["date_range_prompt"]
    prompt = f"""
        You are a date parser assistant. 
        Given a date range input (e.g., "last 7 days", "June 1 to June 15"), 
        convert it to a JSON object with start_date and end_date in YYYY-MM-DD format. 
        Use August 11, 2025, as the current date for relative ranges. If the input is a single day, 
        set both dates to it. For invalid inputs, return "Invalid date range". 
        Output ONLY in this exact format, with no extra text: YYYY-MM-DD YYYY-MM-DD where first date is start date and latter is end date.
        User input: {date_range_prompt}
    """

    llm_response = ask_llm(prompt)
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", llm_response)

    if not dates or "Invalid date range" in llm_response:
        print("Invalid date range prompt!")
        return END
    
    d1 = datetime.strptime(dates[0], "%Y-%m-%d").date()
    d2 = datetime.strptime(dates[1], "%Y-%m-%d").date()

    if d1 > d2:
        state["start_date"] = dates[1]
        state["end_date"] = dates[0]
    else:
        state["start_date"] = dates[0]
        state["end_date"] = dates[1]

    return state

def filter_data(state: PlotState) -> PlotState:
    try:
        with sqlite3.connect("agent_db.db") as conn:
            cursor = conn.cursor()
            filtered_data = dict()

            cursor.execute("""
                SELECT date,
                SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
                SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count,
                SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) AS neutral_count
                FROM reply
                WHERE date BETWEEN ? AND ?
                GROUP BY date;
            """, (state['start_date'], state['end_date']))

            for date, positive, negative, neutral in cursor.fetchall():
                filtered_data[date] = {"positive":positive, "negative":negative, "neutral":neutral}

            state['filtered_data'] = filtered_data

    except sqlite3.Error as e:
        raise sqlite3.Error(f"Database error: {e}")

    return state


def choose_graph_type(state: PlotState) -> PlotState:
    graph_type = state['graph_type'].lower()

    if graph_type == "bar graph":
        return "bar_graph_ploter"
    elif graph_type == "line graph":
        return "line_graph_ploter"
    else:
        print("Invalid or Unsupported graph type!")
        return END

    

def bar_graph_ploter(state: PlotState) -> PlotState:
    data = state["filtered_data"]

    if not data:
        print("No data to plot.")
        return state

    dates = sorted(data.keys())
    positive_counts = [data[d]["positive"] for d in dates]
    negative_counts = [data[d]["negative"] for d in dates]
    neutral_counts = [data[d]["neutral"] for d in dates]

    # Plot
    plt.style.use("ggplot")
    plt.figure(figsize=(12, 7))
    bar_width = 0.25
    x = range(len(dates))

    plt.bar([i - bar_width for i in x], positive_counts, width=bar_width, label="Positive", color="green")
    plt.bar(x, negative_counts, width=bar_width, label="Negative", color="red")
    plt.bar([i + bar_width for i in x], neutral_counts, width=bar_width, label="Neutral", color="blue")

    plt.xticks(x, dates, rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Number of Reviews")
    plt.title(f"Sentiment Counts ({state['start_date']} to {state['end_date']}) - Bar Graph")
    plt.legend()

    # Save plot
    plot_path = f"./graphs/sentiment_bar_graph from {state['start_date']} to {state['end_date']}.png"
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    state["plot_path"] = plot_path
    print(f"Bar graph saved at {plot_path}")

    return state

def line_graph_ploter(state: PlotState) -> PlotState:
    data = state["filtered_data"]

    if not data:
        print("No data to plot.")
        return state

    # Extract sorted dates and counts
    dates = sorted(data.keys())
    positive_counts = [data[d]["positive"] for d in dates]
    negative_counts = [data[d]["negative"] for d in dates]
    neutral_counts = [data[d]["neutral"] for d in dates]

    # Plot
    plt.style.use("ggplot")
    plt.figure(figsize=(12, 7))

    plt.plot(dates, positive_counts, marker="o", linestyle="-", color="green", label="Positive")
    plt.plot(dates, negative_counts, marker="o", linestyle="-", color="red", label="Negative")
    plt.plot(dates, neutral_counts, marker="o", linestyle="-", color="blue", label="Neutral")

    plt.xticks(rotation=45)
    plt.xlabel("Date")
    plt.ylabel("Number of Reviews")
    plt.title(f"Sentiment Counts ({state['start_date']} to {state['end_date']}) - Line Graph")
    plt.legend()

    # Save plot
    plot_path = f"./graphs/sentiment_line_graph from {state['start_date']} to {state['end_date']}.png"
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    state["plot_path"] = plot_path
    print(f"Line graph saved at {plot_path}")

    return state



def Sentiment_Visualization_Agent():
    builder = StateGraph(PlotState)
    builder.add_node("get_date_range", get_date_range)
    builder.add_node("filter_data", filter_data)
    builder.add_node("bar_graph_ploter", bar_graph_ploter)
    builder.add_node("line_graph_ploter", line_graph_ploter)

    builder.add_edge(START, "get_date_range")
    builder.add_edge("get_date_range", "filter_data")
    builder.add_conditional_edges(
        "filter_data",
        choose_graph_type,
        {
            "bar_graph_ploter": "bar_graph_ploter",
            "line_graph_ploter": "line_graph_ploter"
        }
    )
    builder.add_edge("bar_graph_ploter", END)
    builder.add_edge("line_graph_ploter", END)

    graph = builder.compile()

    return graph
