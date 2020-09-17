# gtk-github-notifications

> Read your GitHub notifications on your desktop. Supports Gtk-based desktop environments

### Install & Usage

 1. Get a personal access token with `notifications` scope and store it as an env variable `GITHUB_AUTH_TOKEN`
 2. Follow [install instructions]( https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-logo-ubuntu-debian-logo-debian) for `PyGObject`
 3. Run `./main.py`

### Notifications

This tool supports issue, pull request and release notifications at the moment. A click on the notification will take you to the corresponding issue / pull request or the releases page of the repo.

Support for commit comments and security alerts may be added in the future.

Seen notifications are currently not persisted over multiple program runs. If more than `3` unread notifications are retrieved by a single API call, a rollup notification linking to `/notifications` will be sent.
