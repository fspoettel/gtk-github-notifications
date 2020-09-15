from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64
import json
import os
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
        self.notify(notifications)
      except Exception as e:
        print(e)
      time.sleep(30)

  def dismiss(self, notification):
    self.store.pop(str(notification.id), None)

  def open_in_browser(self, notification, name, n):
    self.dismiss(notification)
    subject = n['subject']
    url = format_api_url_to_browser_url(subject['url'], subject['type'])
    webbrowser.open(url)

  def notify(self, all_notifications):
    def is_target(n):
      is_new = n['id'] not in self.seen_ids
      is_primary = n['subject']['type'] not in ['Commit', 'RepositoryVulnerabilityAlert']
      return is_new and is_primary

    notifications = [n for n in all_notifications if is_target(n)]

    for n in notifications:
      id = n['id']
      subject = n['subject']

      reason = n['reason']
      repo_name = n['repository']['full_name']

      notification = Notify.Notification.new(
        '{} ({})'.format(repo_name, reason),
        subject['title']
      )

      notification.set_urgency(0)
      notification.id = int(id)

      notification.add_action(
        'default',
        'Open GitHub',
        self.open_in_browser,
        { 'subject': subject }
      )

      notification.connect('closed', self.dismiss)
      notification.show()

      self.seen_ids.append(id)
      self.store[id] = notification

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
    raise ValueError('No GitHub auth token present')
