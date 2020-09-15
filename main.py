from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64
import json
import os
from random import randint
import subprocess
import threading
import time
import webbrowser

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify
from gi.repository import GLib


def read_auth_token():
  return os.getenv('GITHUB_AUTH_TOKEN')


def github_request(path, params = {}):
  url='https://api.github.com/{}?{}'.format(path, urlencode(params))
  headers = {
    'Authorization': 'Token {}'.format(read_auth_token()),
    'Accept': 'application/vnd.github.v3+json',
  }

  with urlopen(Request(url, headers=headers)) as res:
    data = res.read()
    encoding = res.info().get_content_charset('utf-8')
    return json.loads(data.decode(encoding))


def format_api_url_to_browser_url(url, type):
  browser_url = url.replace('https://api.github.com/repos', 'https://github.com')
  if type == 'PullRequest':
    return browser_url.replace('pulls', 'pull')
  elif type == 'Release':
    return browser_url.rsplit('/', 1)[0]
  else:
    return browser_url


class notification_daemon:
  def __init__(self):
    self.store = {}
    self.seen_ids = []

  def start(self):
    Notify.init('GitHub')
    while True:
      try:
        notifications = github_request('notifications', { 'per_page': 100 })
        self.process_notifications(notifications)
      except Exception as e:
        print(e)
      time.sleep(30)

  def process_notifications(self, all_notifications):
    def is_target(n):
      is_new = n['id'] not in self.seen_ids
      is_primary = n['subject']['type'] not in ['Commit', 'RepositoryVulnerabilityAlert']
      return is_new and is_primary

    notifications = [n for n in all_notifications if is_target(n)]
    count = len(notifications)
    if count < 3:
      for n in notifications:
        id = n['id']
        self.seen_ids.append(id)
        self.notify(
          id,
          '{} ({})'.format(n['repository']['full_name'], n['reason']),
          n['subject']
        )
    else:
      for n in notifications:
        self.seen_ids.append(n['id'])

      self.notify(
        int(time.time()),
        'GitHub Notifications',
        {
          'title': '{} new notifications'.format(count),
          'url': 'https://github.com/notifications',
          'type': 'Custom'
        }
      )

  def notify(self, id, title, subject):
    notification = Notify.Notification.new(title, subject['title'])
    notification.set_urgency(1)
    notification.set_timeout(0)
    notification.id = int(id)

    notification.add_action(
      'default',
      'Open GitHub',
      self.on_action,
      { 'subject': subject }
    )
    notification.connect('closed', self.on_dismiss)
    notification.show()
    self.store[id] = notification

  def on_dismiss(self, notification):
    self.store.pop(str(notification.id), None)

  def on_action(self, notification, name, n):
    self.on_dismiss(notification)
    subject = n['subject']
    url = format_api_url_to_browser_url(subject['url'], subject['type'])
    webbrowser.open(url)


def app_main():
  daemon = notification_daemon()
  daemon.start()


if __name__ == '__main__':
  if isinstance(read_auth_token(), str):
    thread = threading.Thread(target=app_main)
    thread.daemon = True
    thread.start()
    GLib.MainLoop().run()
  else:
    raise ValueError('`GITHUB_AUTH_TOKEN` is missing in env')
