import sqlite3
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from helper import ask_llm

class Review(TypedDict):
    review_ID: int
    review_text: str
    date: str 
    sentiment: str
    reply: str


    

def classify_sentiment(review: Review) -> Review:
    review_text = review["review_text"]
    prompt = f"Classify the sentiment of this review, using one word positive, neutral, or negative:\n\n{review_text}"

    llm_response = ask_llm(prompt, 0.7).lower()

    if 'positive' in llm_response:
        review["sentiment"] = 'positive'
    elif 'negative' in llm_response:
        review['sentiment'] = "negative"
    elif 'neutral' in llm_response:
        review['sentiment'] = "neutral"
    else:
        print("Invalid response from LLM!")
        print("Trying again...")
        classify_sentiment(review)

    return review

def generate_reply(review: Review) -> Review:
    prompt = f"""
    You are a polite restaurant assistant. The review is {review['sentiment']}:
    "{review['review_text']}"
    Write a short, kind, context-aware reply.
    """

    llm_response = ask_llm(prompt)
    review["reply"] = llm_response
    return review

def save_review(review: Review) -> Review:
    conn = sqlite3.connect("agent_db.db")
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reply (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_ID INTEGER,
        review_text TEXT,
        sentiment TEXT,
        reply TEXT,
        date DATETIME,
        Foreign key (review_ID) references review(ID)
    );
    """)
    conn.commit()

    cursor.execute("INSERT INTO reply (review_ID, review_text, sentiment, reply, date) VALUES (?, ?, ?, ?, ?)",
                   (review['review_ID'], review['review_text'], review['sentiment'], review['reply'], review['date']))
    conn.commit()

    return review


def Customer_Feedback_Response_Agent():
    builder = StateGraph(Review)
    builder.add_node("classify_sentiment", classify_sentiment)
    builder.add_node("generate_reply", generate_reply)
    builder.add_node("save_review", save_review)

    builder.set_entry_point("classify_sentiment")
    builder.add_edge("classify_sentiment", "generate_reply")
    builder.add_edge("generate_reply", "save_review")

    graph = builder.compile()

    return graph