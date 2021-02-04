archivy-hn allows users to sync the posts they've upvoted on [hacker news](https://news.ycombinator.com) to their [Archivy](https://archivy.github.io) knowledge base.

It is an official extension developed by [archivy](https://github.com/archivy/).

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

## Install in Docker
To install this plugin inside the official Docker image for Archivy, do the following:
1) `docker exec -u 0 archivy apk add libxml2-dev` to install the `libxml2-dev` dependency.
2) `docker exec -u 0 archivy apk add libxslt-dev` to install the `libxslt-dev` dependency.
3) `docker exec archivy pip install archivy_hn` to install the plugin.

## Usage in Docker
To execute commands within the container, use the `docker exec -it archivy archivy hn-sync [OPTIONS]` format. 
For example: `docker exec -it archivy hn-sync --username example --hn-password password --save-comments`.

### Contributing

You can open any issues or feature requests [here](https://github.com/archivy/archivy_hn/issues).

You can also talk to me directly on the [Archivy discord server](https://discord.gg/uQsqyxB)
