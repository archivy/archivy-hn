from datetime import datetime
import sys

import click
import requests
from archivy import app
from archivy.data import create_dir, get_items
from archivy.models import DataObj
from bs4 import BeautifulSoup

BASE_URL = "https://news.ycombinator.com"
num_links_processed = 0
num_ask_hn = 0
num_links = 0


def build_comments(comment, tabs):
    cur = "\n\n" + "\t" * tabs + (
            f"- {comment['text']} by "
            f"[{comment['author']}]({BASE_URL}/user?id={comment['author']})"
          )

    for child in comment["children"]:
        cur += build_comments(child, tabs + 1)
    return cur

def finish():
    if not num_links_processed:
        print(
            "Could not retrieve any of the links. Check if you actually have any newly saved links."
        )
        sys.exit(1)
    else:
        print(f"Processed {num_links_processed} posts, "
              f"including {num_links} external links and {num_ask_hn} posts "
              f"directly posted on Hacker News (Ask HN: etc...)")


@click.command(help=f"Pull your upvoted or favorited posts from Hacker News and "
                    f"save their contents into your knowledge base")
@click.option("--post-type",
               default="upvoted",
               help="Whether to sync upvoted posts or favorited ones. One of 'upvoted' or 'favorites'")
@click.option("--save-comments",
              is_flag=True,
              help="Whether or not the hacker news comments should also be saved.")
@click.option("--username",
               required=True,
               help="Username on Hacker News")
@click.option('--hn-password', prompt=True, hide_input=True)
def hn_sync(save_comments, post_type, username, hn_password):
    global num_ask_hn, num_links, num_links_processed
    with app.app_context():
        session = requests.Session()

        print("\nLogging in...")

        r = session.post(f"{BASE_URL}/login", data={"acct": username, "pw": hn_password})

        if session.cookies.get("user", None) is None:
            print("Error logging in. Verify the credentials and try again.")
            sys.exit(1)
        print("Logged in successfully.\n")

        url = f"{BASE_URL}/{post_type}?id={username}&p="
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:75.0) Gecko/20100101 Firefox/75.0",
        }

        i = 1

        # create folders in archivy to store content
        create_dir("hacker_news")
        create_dir("hacker_news/" + post_type)

        # store titles of previous posts
        seen_posts = set([post["title"] for post in get_items(
                                                        path=f"hacker_news/{post_type}/",
                                                        structured=False)])
        while True:
            print(f"Getting results of page {i}")
            r = session.get(url + str(i), headers=headers)

            tree = BeautifulSoup(r.text, features="lxml")
            tree_subtext = tree.select(".subtext")
            # Number of links on the page
            n = len(tree_subtext)

            if not n:
                print(f"Processing page {i}. No links found.")
                break

            for j in range(n):
                tree_subtext_each = tree_subtext[j].find_all("a")

                # This is to take care of situations where flag link may not be
                # present in the subtext. So number of links could be either 3
                # or 4.
                num_subtext = len(tree_subtext_each)
                # get post id by parsing link to comments
                post_id = int(tree_subtext_each[num_subtext - 1]['href'].split("=")[1])

                # call algolia api
                res = requests.get(f"https://hn.algolia.com/api/v1/items/{post_id}").json()
                # might return a 404 if not indexed, so we check if we got a response by calling .get()
                if res.get("type") and res["type"] == "story":
                    if res["title"] in seen_posts:
                        # we have already seen this upvoted story
                        # this means that all stories that follow will also be seen
                        finish()
                        
                    bookmark = DataObj(path=f"hacker_news/{post_type}/",
                                       date=datetime.utcfromtimestamp(res["created_at_i"]),
                                       type="bookmark")
                    hn_link = f"{BASE_URL}/item?id={post_id}"
                    if res["url"]:
                        num_links += 1
                        bookmark.url = res["url"]
                        bookmark.process_bookmark_url()
                    else:
                        num_ask_hn += 1
                        bookmark.url = hn_link
                        bookmark.content = res["title"].replace("<p>", "").replace("</p>", "")

                    bookmark.title = res["title"]
                    bookmark.content = f"{res['points']} points on [Hacker News]({hn_link})\n\n{bookmark.content}"

                    # save comments if user requests it through option or if story is an ASK HN
                    if save_comments or not res["url"]:
                        bookmark.content += "\n\n## Comments from Hacker News"
                        for comment in res["children"]:
                            bookmark.content += "\n\n" + build_comments(comment, 0)
                    bookmark.insert()
                    num_links_processed += 1
                    print(f"Saving {res['title']}...")

            if n < 30:
                # no more links
                break

            i += 1
        finish()
