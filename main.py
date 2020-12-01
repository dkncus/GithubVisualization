from GithubVis import GithubVis
import seaborn as sns
import streamlit as st

def create_visualizations():
    try:
        loading_msg = st.subheader("Fetching diagnostics and commit history on this repository...")
        g = GithubVis(user, repo, load_from_csv=True, save_csv=False)
        commits_over_time = g.visualize_commits_over_time(show_authors=True)
        commits_over_time.figure.savefig("commits.png")
        changes_over_time = g.visualize_changes_over_time(show_authors=True)
        changes_over_time.figure.savefig("changes.png")
        subheader = user + '/' + repo
        st.subheader(subheader)
        st.image("commits.png", width=600)
        st.image("changes.png", width=600)
        st.dataframe(g.df)
    except:
        print("Github Repo ERROR")

# Set the theme, add necessary imports
sns.set_theme()

# Create Github Visualization object based on certain user & repo
st.header("Github Visualization")
user = st.text_input("Github User Name", "phadej")
repo = st.text_input("Repository Name", "github")
button = st.button('Show the data!')
if button:
    create_visualizations()