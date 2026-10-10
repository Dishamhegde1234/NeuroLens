"""Educator dashboard (Streamlit) that reads the same database as the Flask app.

    pip install -r requirements-streamlit.txt
    streamlit run streamlit_app.py

Shows one student's topic risk, and which topics are weakest across the class.
Run it on a trusted network only: it has no login of its own.
"""
import pandas as pd
import streamlit as st

from neurolens import create_app, db


@st.cache_resource
def get_app():
    return create_app()


app = get_app()
svc = app.extensions["neurolens"]

st.set_page_config(page_title="NeuroLens · Educator view", page_icon="🧠", layout="wide")
st.title("🧠 NeuroLens: educator view")
st.caption("Spot weak topics early, for one student or the whole class.")


def topic_table(dash: dict) -> pd.DataFrame:
    rows = []
    for level in dash["levels"]:
        for t in level["topics"]:
            rows.append({
                "Level": level["name"], "Topic": t["name"], "Risk %": round(t["risk"] * 100),
                "Tier": {"hi": "High", "mid": "Medium", "lo": "Low"}[t["tier"]],
                "Attempts": t["n"], "Confidence": f"{round(t['confidence'] * 100)}%",
            })
    return pd.DataFrame(rows)


with app.app_context():
    students = db.get_db().execute(
        "SELECT id, name, email, is_demo FROM users ORDER BY is_demo, id DESC"
    ).fetchall()
    if not students:
        st.info("No students yet. Sign up in the Flask app first.")
        st.stop()

    labels = {s["id"]: f"{s['name']} ({'demo' if s['is_demo'] else s['email']})" for s in students}
    tab_student, tab_class = st.tabs(["Student", "Class overview"])

    with tab_student:
        uid = st.selectbox("Student", list(labels), format_func=labels.get)
        dash = svc.dashboard(db.get_user(uid))
        s, h = dash["stats"], dash["habits"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy", f"{s['accuracy']}%")
        c2.metric("Attempts", s["attempts"])
        c3.metric("Attendance", f"{h['attendance']}%")
        c4.metric("Study hours", f"{h['hours']:.1f} h")
        df = topic_table(dash)
        st.subheader("Highest-risk topics")
        top = df[df["Attempts"] > 0].sort_values("Risk %", ascending=False).head(10)
        if top.empty:
            st.write("No attempts yet, so every topic is on the neutral baseline.")
        else:
            st.bar_chart(top.set_index("Topic")["Risk %"])
        st.subheader("All topics")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_class:
        frames = []
        for stu in students:
            if stu["is_demo"]:
                continue
            d = topic_table(svc.dashboard(db.get_user(stu["id"])))
            frames.append(d[d["Attempts"] > 0])
        if not frames or all(f.empty for f in frames):
            st.write("No practice data from real students yet.")
        else:
            all_df = pd.concat(frames)
            class_view = (all_df.groupby(["Level", "Topic"], as_index=False)
                          .agg(**{"Average risk %": ("Risk %", "mean"), "Students": ("Risk %", "size")})
                          .sort_values("Average risk %", ascending=False))
            class_view["Average risk %"] = class_view["Average risk %"].round(1)
            st.subheader("Topics the class struggles with most")
            st.bar_chart(class_view.head(10).set_index("Topic")["Average risk %"])
            st.dataframe(class_view, use_container_width=True, hide_index=True)
