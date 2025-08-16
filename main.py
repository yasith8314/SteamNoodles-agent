from feedback_agent import Customer_Feedback_Response_Agent, Review
from plot_agent import Sentiment_Visualization_Agent, PlotState
import sqlite3

def test_1():
    print("========== Test 01 ===========")
    print("Generate a reply for given reviews in the database, clasify them")
    print("and store them in the database.\n")

    graph = Customer_Feedback_Response_Agent()

    conn = sqlite3.connect("agent_db.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.ID, r.date, r.review_text
        FROM review r
        LEFT JOIN reply rp ON r.id = rp.review_ID
        WHERE rp.review_ID IS NULL;
    """)

    for id, date, review_text in cursor.fetchall():
        review = Review(review_ID=id, date=date, review_text=review_text)
        review = graph.invoke(review)

        print(f"ID: {id}\nReview: {review_text}")
        print(f"Sentiment: {review["sentiment"]}\nGenerated Reply:\n{review["reply"]}\n")


def test_2():
    graph = Sentiment_Visualization_Agent()

    plot1 = PlotState(date_range_prompt="last 2 weeks", graph_type="bar graph")
    plot2 = PlotState(date_range_prompt="from July 10th to August 1st", graph_type="line graph")

    graph.invoke(plot1)
    #graph.invoke(plot2)


if __name__ == "__main__":
    #test_1()
    test_2()
