from GithubVis import GithubVis
import seaborn as sns
import streamlit as st

def create_visualizations():
    try:
        st.subheader("Fetching diagnostics and commit history on this repository...")
        g = GithubVis(user, repo, load_from_csv=False, save_csv=False)
        print("Data Collected. Building visualization...")

        commits_over_time = g.visualize_commits_over_time(show_authors=True)
        commits_over_time.figure.savefig("commits.png")
        changes_over_time = g.visualize_changes_over_time(show_authors=True)
        changes_over_time.figure.savefig("changes.png")

        print("Figures Saved.")

        subheader = user + '/' + repo
        st.header(subheader)
        st.subheader("Commits over Time")
        st.image("commits.png", width=800)
        st.subheader("Total Codebase Changes over Time")
        st.image("changes.png", width=800)
        st.subheader("Data from all commits")
        st.dataframe(g.df)
    except Exception as e:
        print(e)
        st.error("Error Connecting to GitHub API.")

# Set the theme, add necessary imports
sns.set_theme()

# Create Github Visualization object based on certain user & repo
st.header("Github Visualization")
user = st.text_input("Github User Name", "paulirish")
repo = st.text_input("Repository Name", "git-open")
button = st.button('Show the data!')
if button:
    create_visualizations()