archivy_hn is an official extension for [Archivy](https://archivy.github.io).

It allows users to sync the posts they've upvoted on [hacker news](https://news.ycombinator.com) to their archivy knowledge base.

![demo](https://github.com/archivy/archivy_hn/blob/main/demo.gif)

## Install

You need to have [`archivy`](https://archivy.github.io) already installed.

Run `pip install archivy_hn` (or pip3 if you're on ubuntu).

## Usage

Refer below to see the commands and options you can run:

```
Usage: archivy hn-sync [OPTIONS]

  Pull your upvoted or favorited posts from Hacker News and save their
  contents into your knowledge base

Options:
  --post-type TEXT    Whether to sync upvoted posts or favorited ones. One of
                      'upvoted' or 'favorites'

  --save-comments     Whether or not the hacker news comments should also be
                      saved.

  --username TEXT     Username on Hacker News  [required]
  --hn-password TEXT
  --help              Show this message and exit.
```


### Contributing

You can open any issues or feature requests [here](https://github.com/archivy/archivy_hn/issues).

You can also talk to me directly on the [Archivy discord server](https://discord.gg/uQsqyxB)
