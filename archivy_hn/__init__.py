from datetime import datetime
from time import sleep
import sys

import click
import requests
from bs4 import BeautifulSoup
from html2text import html2text

from archivy import app
from archivy.data import create_dir, get_items
from archivy.models import DataObj
from archivy.click_web.web_click_types import PASSWORD_TYPE

BASE_URL = "https://news.ycombinator.com"
num_links_processed = 0
num_ask_hn = 0
num_links = 0


def build_comments(comment):
    cur = (
        f"<li>{comment['text']} by "
        f"<a href='{BASE_URL}/user?id={comment['author']}'>{comment['author']}</a><ul>"
    )

    for child in comment["children"]:
        cur += build_comments(child)
    cur += "</ul></li>"
    return cur


def finish():
    if not num_links_processed:
        print(
            "Could not retrieve any of the links. Check if you actually have any newly saved links."
        )
        sys.exit(1)
    else:
        print(
            f"Processed {num_links_processed} posts, "
            f"including {num_links} external links and {num_ask_hn} posts "
            f"directly posted on Hacker News (Ask HN: etc...)"
        )


@click.command(
    help=f"Pull your upvoted or favorited posts from Hacker News and "
    f"save their contents into your knowledge base"
)
@click.option(
    "--post-type",
    default="upvoted",
    help="Whether to sync upvoted posts or favorited ones. One of 'upvoted' or 'favorites'",
)
@click.option(
    "--save-comments",
    is_flag=True,
    help="Whether or not the hacker news comments should also be saved.",
)
@click.option("--username", required=True, help="Username on Hacker News")
@click.option("--hn-password", prompt=True, hide_input=True, type=PASSWORD_TYPE)
@click.option(
    "--force",
    is_flag=True,
    help="Set this option if something interrupted the syncing process and old posts haven't been seen, to indicate the plugin should search all of your posts, and continue even if it encounters newly upvoted posts that have already been saved.",
)
def hn_sync(save_comments, post_type, username, hn_password, force):
    global num_ask_hn, num_links, num_links_processed
    with app.app_context():
        session = requests.Session()

        print("\nLogging in...")

        r = session.post(
            f"{BASE_URL}/login", data={"acct": username, "pw": hn_password}
        )

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
        seen_posts = set(
            [
                post["url"]
                for post in get_items(
                    path=f"hacker_news/{post_type}/", structured=False
                )
            ]
        )
        while True:
            links_processed_prev = num_links_processed
            print(f"Getting results of page {i}")
            r = session.get(url + str(i), headers=headers)

            tree = BeautifulSoup(r.text, features="lxml")
            tree_subtext = tree.select(".subtext")
            post_links = tree.select(".titlelink")
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
                post_id = int(
                    tree_subtext_each[num_subtext - 1]["href"]
                    .split("=")[1]
                    .split("&")[0]
                )
                post_url = post_links[j]["href"]
                hn_link = f"{BASE_URL}/item?id={post_id}"

                if (post_url in seen_posts or hn_link in seen_posts) and not force:
                    # we have already seen this upvoted story
                    # this means that all stories that follow will also be seen
                    finish()
                if (post_url in seen_posts or hn_link in seen_posts) and force:
                    print(f"{post_url} already saved.")
                    continue
                # call algolia api
                try:
                    res = requests.get(
                        f"https://hn.algolia.com/api/v1/items/{post_id}"
                    ).json()
                except:
                    print(f"Could not save {post_url}.")
                    continue
                # might return a 404 if not indexed, so we check if we got a response by calling .get()
                if res.get("type") and res["type"] == "story":
                    bookmark = DataObj(
                        path=f"hacker_news/{post_type}/",
                        date=datetime.utcfromtimestamp(res["created_at_i"]),
                        type="bookmark",
                    )
                    if res["url"]:
                        num_links += 1
                        bookmark.url = post_url
                        bookmark.process_bookmark_url()
                    else:
                        num_ask_hn += 1
                        bookmark.url = hn_link
                        bookmark.content = (
                            res["title"].replace("<p>", "").replace("</p>", "")
                        )

                    bookmark.title = res["title"]
                    bookmark.content = f"{res['points']} points on [Hacker News]({hn_link})\n\n{bookmark.content}"

                    # save comments if user requests it through option or if story is an ASK HN
                    if save_comments or not res["url"]:
                        bookmark.content += "\n\n## Comments from Hacker News"
                        for comment in res["children"]:
                            comments = "<ul>" + build_comments(comment) + "</ul>"
                            bookmark.content += "\n\n" + html2text(
                                comments, bodywidth=0
                            ).replace("\n\n", "\n")
                    bookmark.insert()
                    num_links_processed += 1
                    print(f"Saving {res['title']}...")

            if n < 30:
                # no more links
                break
            elif links_processed_prev == num_links_processed:
                sleep(
                    1
                )  # throttling if no new links have been saved (when we're running force.)

            i += 1
        finish()
