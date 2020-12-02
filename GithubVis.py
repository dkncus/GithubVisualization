from github import Github                   # For authentication to the Github API
import pandas as pd                         # For creating and managing dataframes
import seaborn as sns                       # For visualizing the organized data
from datetime import datetime, timedelta    # For organizing dataframe data
import os                                   # For fetching API key
import threading                            # For fetching data from github API concurrently
import time                                 # For sleeping the system

class GithubVis:
    # Initialization Method
    def __init__(self, user, repo, load_from_csv=True, save_csv=False):
        '''
        key = os.environ.get('GITHUB_API_KEY')
        print("API KEY:", key)
        '''

        print("IN TESTING")
        key_file = open('./access_key/key.txt')
        key = key_file.readline().rstrip('\n')
        print("API KEY:", key)

        # Authenticate to Github API
        print("Authenticating to Github API with key -", key, '...')
        self.g = None
        try:
            self.g = Github(key)
            print("Authentication Success!\n")
        except:
            print("Authentication Failed.\n")
            quit()

        # Get repo from certain user
        self.user = user
        self.name = repo
        self.repo_loc = self.user + '/' + self.name
        self.repo = self.g.get_repo(self.repo_loc)

        # Create Pandas Dataframe
        self.data_head = {'SHA':[], 'ETAG':[], 'Author':[], 'Username':[], 'Additions':[], 'Deletions':[], 'Total':[], 'Date':[]}

        if load_from_csv:
            self.df = pd.read_csv("commit_data.csv")
        else:
            self.df = pd.DataFrame(self.data_head)
            self.fetch_data()

    # Fetch the data from a given Username and Repository
    def fetch_data(self, save_csv=False):
        # Get every commit from that repo
        commits = self.repo.get_commits()

        threads = []
        for commit in commits:
            thread = threading.Thread(target = self.threaded_insert, args = (commit,))
            threads.append(thread)

        print("Starting", len(threads), "Threads")

        batch_size = 20
        batch = 0
        threads_remaining = len(threads)
        while threads_remaining > 0:
            start = (batch_size + 1) * batch
            end = (batch_size + 1) * batch + batch_size

            print("Starting Batch", batch, ", Threads[", start, ',', end, ']')
            #Start a batch of threads
            # 0 - [0:20]
            # 1 - [21:41]
            # 2 - [42:62]
            # 3 - [63:83]
            for thread in threads[start:end]:
                thread.start()

            # Await all the threads completion
            while not self.check_threads_complete(threads[start:end]):
                time.sleep(0.01)

            # Join all the threads in the list
            for thread in threads[start:end]:
                thread.join()

            # Increment the Current Batch
            batch += 1

            # Decrement number of Threads
            threads_remaining -= batch_size

        # Sort Dataframe by Commit Date
        if save_csv:
            print("SAVING CSV FILE")
            self.df.to_csv('commit_data.csv', index=False)

    def check_threads_complete(self, threads):
        for thread in threads:
            if thread.is_alive():
                print("Threads still alive!")
                return False
        print("Threads are dead.")
        return True

    def threaded_insert(self, commit):
        data = commit.raw_data

        # Error handle a null user
        try:
            name = data['commit']['author']['name']
            username = data['author']['login']
        except:
            name = ''
            username = ''

        # Create commit data row
        row = {
            'SHA': data['sha'],
            'ETAG': None,
            'Author': name,
            'Username': username,
            'Additions': data['stats']['additions'],
            'Deletions': data['stats']['deletions'],
            'Total': data['stats']['total'],
            'Date': commit.stats.last_modified
        }

        # Append the created row to the dataframe
        self.df = self.df.append(row, ignore_index=True)

        return 0

    # Gets a unique dict of developers with keys to their names
    def get_developers_data(self):
        dev_users = self.df['Username'].drop_duplicates()

        devs_dict = {}

        for i, user in enumerate(dev_users):
            user_stats = self.df.loc[self.df['Username'] == user]
            author_names = user_stats['Author']
            name = ''
            for n in author_names:
                name = n
            if user_stats.shape[0] != 0:
                devs_dict[i] = {'Username': user, 'Name': name, 'Commits': user_stats.shape[0], 'Changes': user_stats['Total'].sum()}

        return devs_dict

    # Visualize developers that have the most commits
    def visualize_authors(self):
        # Get the data from the developers
        devs = g.get_developers_data()

        # Set the dataframe
        data = pd.DataFrame.from_dict(devs, orient='index', columns=["Username", "Name", "Commits", "Changes"])
        users_changes = data.sort_values(by=['Changes'], ascending=False)
        users_commits = data.sort_values(by=['Commits'], ascending=False)

        plot = sns.barplot(data=users_commits[0:5], x='Name', y='Commits', palette='Blues_d')
        for item in plot.get_xticklabels():
            item.set_rotation(30)

        return plot

    # Shows the total number of commits to the repository over the lifetime of the project.
    def visualize_commits_over_time(self, show_authors = False, num_authors=5):
        # Create list of all days where a commit happened
        commit_dates = []

        # For each row of the dataframe
        for index, row in self.df.iterrows():
            # Create a parsed datetime object and place into "commit_dates"
            date_time = datetime.strptime(row['Date'], "%a, %d %b %Y %H:%M:%S GMT")
            date = datetime(date_time.year, date_time.month, date_time.day)
            commit_dates.append(date)

        # Create dict of number of commits for every given day
        commit_dates_with_amount = {}
        for date in commit_dates:
            if date in commit_dates_with_amount.keys():
                commit_dates_with_amount[date] += 1
            else:
                commit_dates_with_amount[date] = 1

        # Get a list of all days between the start and end of the cycle
        sdate = commit_dates[-1]  # start date
        d = datetime.now()
        edate = datetime(d.year, d.month, d.day)# end date

        days_between = []
        delta = edate - sdate  # as timedelta
        for i in range(delta.days + 1):
            day = sdate + timedelta(days=i)
            days_between.append(day)

        # For each day in Days_between, get a running total of the commits that occurred
        total_commits = 0
        running_commits = []
        for day in days_between:
            if day in commit_dates_with_amount.keys():
                total_commits += commit_dates_with_amount[day]
            running_commits.append(total_commits)

        # If the show_authors toggle is on
        authors_commit_counts = {}
        if show_authors:
            # Get the top num_authors that have worked on the project
            authors = pd.DataFrame.from_dict(
                self.get_developers_data(),
                orient='index',
                columns=["Username", "Name", "Commits", "Changes"]
            )
            authors = authors.sort_values(by=['Commits'], ascending=False)
            authors = authors[0:num_authors]

            # For each author in the dataframe
            for index, author in authors.iterrows():
                author_username = author["Username"]

                authors_commit_dates = []
                # For each row of the dataframe
                for index, row in self.df.iterrows():
                    if row['Username'] == author_username:
                        # Create a parsed datetime object and place into "commit_dates"
                        date_time = datetime.strptime(row['Date'], "%a, %d %b %Y %H:%M:%S GMT")
                        date = datetime(date_time.year, date_time.month, date_time.day)
                        authors_commit_dates.append(date)

                # Tally the number of commits for each date
                author_dates_with_amount = {}

                for date in authors_commit_dates:
                    if date in author_dates_with_amount.keys():
                        author_dates_with_amount[date] += 1
                    else:
                        author_dates_with_amount[date] = 1

                # For each day in Days_between, get a running total of the commits that occurred
                author_total_commits = 0
                author_running_commits = []
                for day in days_between:
                    if day in author_dates_with_amount.keys():
                        author_total_commits += author_dates_with_amount[day]
                    author_running_commits.append(author_total_commits)

                # Insert the key into the dictionary
                authors_commit_counts[author_username] = author_running_commits

        # Zip the 2 lists (running_commits) and (days_between) and place in DataFrame
        if show_authors:
            vis_data = pd.DataFrame(list(zip(days_between, running_commits)), columns=['Date', 'Commit Count'])
            for item in authors_commit_counts:
                vis_data[item] = authors_commit_counts[item]
        else:
            vis_data = pd.DataFrame(list(zip(days_between, running_commits)), columns=['Date', 'Commit Count'])

        plot = sns.lineplot(data=vis_data, palette='mako')
        plot.set(xlabel="Days Since Initial Commit", ylabel="Number of Commits", title="Repository Commits over Time")
        return plot

    # Show the changes made to the repository over time
    def visualize_changes_over_time(self, show_authors=False, num_authors=5):
        # Create list of all days where a commit happened
        change_dates = {}
        sdate = None

        # For each row of the dataframe
        for index, row in self.df.iterrows():
            # Create a parsed datetime object and place into "commit_dates"
            date_time = datetime.strptime(row['Date'], "%a, %d %b %Y %H:%M:%S GMT")
            date = datetime(date_time.year, date_time.month, date_time.day)
            if date in change_dates.keys():
                change_dates[date] += row['Total']
            else:
                change_dates[date] = row['Total']
            if index == self.df.shape[0] - 1:
                sdate = date

        # Create dict of number of commits for every given day
        change_dates_with_amount = {}
        for date in change_dates:
            if date in change_dates_with_amount.keys():
                change_dates_with_amount[date] += change_dates[date]
            else:
                change_dates_with_amount[date] = change_dates[date]

        # Get a list of all days between the start and end of the cycle
        d = datetime.now()
        edate = datetime(d.year, d.month, d.day)  # end date

        days_between = []
        delta = edate - sdate  # as timedelta
        for i in range(delta.days + 1):
            day = sdate + timedelta(days=i)
            days_between.append(day)

        # For each day in Days_between, get a running total of the commits that occurred
        total_changes = 0
        running_commits = []
        for day in days_between:
            if day in change_dates_with_amount.keys():
                total_changes += change_dates_with_amount[day]
            running_commits.append(total_changes)

        authors_change_counts = {}
        if show_authors:
            # Get the top num_authors that have worked on the project
            authors = pd.DataFrame.from_dict(
                self.get_developers_data(),
                orient='index',
                columns=["Username", "Name", "Commits", "Changes"]
            )
            authors = authors.sort_values(by=['Changes'], ascending=False)

            if authors.shape[0] > num_authors:
                authors = authors[0:num_authors]


            # For each author in the dataframe
            for index, author in authors.iterrows():
                author_username = author["Username"]

                authors_commit_dates = []
                # For each row of the dataframe
                for index, row in self.df.iterrows():

                        # Create a parsed datetime object and place into "commit_dates"
                        date_time = datetime.strptime(row['Date'], "%a, %d %b %Y %H:%M:%S GMT")
                        date = datetime(date_time.year, date_time.month, date_time.day)
                        authors_commit_dates.append(date)

                author_change_dates = {}

                # For each row of the dataframe
                for index, row in self.df.iterrows():
                    if row['Username'] == author_username:
                        # Create a parsed datetime object and place into "commit_dates"
                        date_time = datetime.strptime(row['Date'], "%a, %d %b %Y %H:%M:%S GMT")
                        date = datetime(date_time.year, date_time.month, date_time.day)
                        if date in author_change_dates.keys():
                            author_change_dates[date] += row['Total']
                        else:
                            author_change_dates[date] = row['Total']

                # Create dict of number of commits for every given day
                author_dates_with_amount = {}
                for date in author_change_dates:
                    if date in author_dates_with_amount.keys():
                        author_dates_with_amount[date] += author_change_dates[date]
                    else:
                        author_dates_with_amount[date] = change_dates[date]

                # For each day in Days_between, get a running total of the commits that occurred
                author_total_commits = 0
                author_running_commits = []
                for day in days_between:
                    if day in author_dates_with_amount.keys():
                        author_total_commits += author_dates_with_amount[day]
                    author_running_commits.append(author_total_commits)

                # Insert the key into the dictionary
                authors_change_counts[author_username] = author_running_commits

        # Zip the 2 lists (running_commits) and (days_between) and place in DataFrame
        if show_authors:
            vis_data = pd.DataFrame(list(zip(days_between, running_commits)), columns=['Date', 'Change Count'])
            print(vis_data)
            for item in authors_change_counts:
                vis_data[item] = authors_change_counts[item]
        else:
            vis_data = pd.DataFrame(list(zip(days_between, running_commits)), columns=['Date', 'Commit Count'])

        print(vis_data)
        plot = sns.lineplot(data=vis_data, palette='mako')
        plot.set(xlabel="Days Since Initial Commit", ylabel="Number of Commits", title="Repository Changes over Time")
        return plot

    # Get the languages that the repository is programmed in
    def get_languages(self):
        pass

if __name__ == '__main__':
    # Set the theme, add necessary imports
    import matplotlib.pyplot as plt
    sns.set_theme()

    # Create Visualization Tool
    g = GithubVis('phadej', 'github', load_from_csv=False, save_csv=True)
    commits_over_time = g.visualize_commits_over_time(show_authors=True)
    commits_over_time.figure.savefig("commits.png")
    plt.show()
    changes_over_time = g.visualize_changes_over_time(show_authors=True)
    changes_over_time.figure.savefig("changes.png")
    plt.show()

    # Show the most significant percentage of codebase in the project
    # Show the percentage of languages used in the project

    # MORE COMPLEX - Show file tree structure over time