from datetime import datetime, timedelta
from getpass import getpass
import re
import sys

import click
import requests
from archivy import app
from archivy.models import DataObj
from archivy.data import create_dir
from bs4 import BeautifulSoup

BASE_URL = "https://news.ycombinator.com"


def post_age_to_date(post_age):
    if "ago" in post_age:
        # get precise date from hn format:
        # 4 days ago - 2 years ago - 5 seconds ago -> datetime object
        date = datetime.now()
        units = int(post_age.split()[0])
        # timedelta does not support month
        if "month" in post_age:
            post_age = post_age.replace("month", "day") 
            units *= 30
        attrs = ["day", "hour", "minute", "second"]
        for i in attrs:
            if i in post_age:
                # plural parameter
                date = date - timedelta(**{f"{i}s": units})
        return date
    else:
        return datetime.strptime(post_age, "on %b %d, %Y")

def extract_comments(hn_url):
    r = requests.get(hn_url)
    parsed = BeautifulSoup(r.text)
    
    comments.process_bookmark_url()
    return comments.content

@click.command()
@click.option("--save_comments", is_flag=True, help="Whether or not the hacker news comments should also be saved.")
def hn_sync(save_comments):
    with app.app_context():
        session = requests.Session()
        print("Enter your HN account details:")
        username = input("Username: ")
        password = getpass()

        print("\nLogging in...")

        r = session.post(f"{BASE_URL}/login", data={"acct": username, "pw": password})

        if session.cookies.get("user", None) is None:
            print("Error logging in. Verify the credentials and try again.")
            sys.exit(1)
        print("Logged in successfully.\n")

        url = f"{BASE_URL}/upvoted?id={username}&p="
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:75.0) Gecko/20100101 Firefox/75.0",
        }

        links_processed = 0
        i = 1

        create_dir("hacker_news")
        while True:
            print(f"Getting results of page {i}")
            r = session.get(url + str(i), headers=headers)

            tree = BeautifulSoup(r.text)

            # Part that contains the title and url for the stories
            tree_title = tree.select(".title")
            # Part that contains metadata such as author, no. of comments, etc.
            tree_subtext = tree.select(".subtext")

            tree_score = tree.select(".subtext span.score")

            # Number of links on the page
            n = len(tree_score)

            if not n:
                print(f"Processing page {i}. No links found.")
                break

            for j in range(n):
                tree_subtext_each = tree_subtext[j].find_all("a")
                tree_title_each = tree_title[2 * j + 1].find_all("a")

                # This is to take care of situations where flag link may not be
                # present in the subtext. So number of links could be either 3
                # or 4.
                num_subtext = len(tree_subtext_each)
                discussion = f"{BASE_URL}/{tree_subtext_each[num_subtext - 1]['href']}"
                data = {
                    "title": tree_title_each[0].get_text(),
                    "url": tree_title_each[0]["href"],
                    "points": int(tree_score[j].get_text().split()[0]),
                    "date": post_age_to_date(tree_subtext_each[1].get_text()),
                    "hn_link": discussion
                }

                bookmark = DataObj(url=data["url"], path='hacker_news/', date=data["date"], type="bookmark")
                bookmark.process_bookmark_url()
                bookmark.title = data["title"]
                bookmark.content = f"{data['points']} points on [Hacker News]({data['hn_link']})\n\n{bookmark.content}"


                if save_comments:
                   cur_content = None
                   comments_page = 1
                   # check for more button to see if there is another page of comments
                   while comments_page == 1 or "[More]" in cur_content:
                       cur_content = extract_comments(f"{data['hn_link']}&p={comments_page}")
                       bookmark.content += "\n\n" + cur_content
                       comments_page += 1

                bookmark.insert()

                print(f"Saving {data['title']}...")


                links_processed += 1

            if n < 30:
                break

            i += 1

        if not links_processed:
            print(
                "Could not retrieve any of the links. Check if you actually have any saved links."
            )
            sys.exit(1)
        else:
            print(f"Processed {links_processed} links")
