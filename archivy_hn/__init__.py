from datetime import datetime
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

def build_comments(comment, tabs):
    cur = "\n\n" + "\t" * tabs + f"- {comment['text']} by [{comment['author']}](https://news.ycombinator.com/user?id={comment['author']})"

    for child in comment["children"]:
        cur += build_comments(child, tabs + 1)
    return cur

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

                # This is to take care of situations where flag link may not be
                # present in the subtext. So number of links could be either 3
                # or 4.
                num_subtext = len(tree_subtext_each)
                post_id = int(tree_subtext_each[num_subtext - 1]['href'].split("=")[1])

                # call algolia api
                res = requests.get(f"https://hn.algolia.com/api/v1/items/{post_id}").json()
                if res["type"] == "story":
                    bookmark = DataObj(path='hacker_news/', date=datetime.utcfromtimestamp(res["created_at_i"]), type="bookmark")
                    hn_link = f"https://news.ycombinator/item?id={post_id}"
                    if res["url"]:
                        bookmark.url = res["url"] 
                        bookmark.process_bookmark_url()
                    else:
                        bookmark.url = hn_link
                        bookmark.content = res["title"].replace("<p>", "").replace("</p>", "")
                        
                    bookmark.title = res["title"]
                    bookmark.content = f"{res['points']} points on [Hacker News]({hn_link})\n\n{bookmark.content}"


                    if save_comments:
                        for comment in res["children"]:
                            bookmark.content += "\n\n" + build_comments(comment, 0)
                    bookmark.insert()

                print(f"Saving {res['title']}...")


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
