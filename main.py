import base64
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import subprocess
import time

def read_auth_token():
  return os.getenv('GITHUB_AUTH_TOKEN')

def send_message(title, message):
  subprocess.Popen(['notify-send', title, message])
  return

def make_github_request(path, params = {}):
  req = Request(
    'https://api.github.com/{}?{}'.format(path, urlencode(params)),
    headers={
      'Authorization': 'Token {}'.format(read_auth_token()),
      'Accept': 'application/vnd.github.v3+json',
    },
  )

  with urlopen(req) as res:
    data = res.read()
    encoding = res.info().get_content_charset('utf-8')
    return json.loads(data.decode(encoding))

class github_notify_daemon:
  def __init__(self):
    self.seen = []
    self.reason_denylist = ['security_alert']

  def notify(self, notifications):
    new_notifications = list(filter(
      lambda n: n['id'] not in self.seen and n['reason'] not in self.reason_denylist,
      notifications
    ))

    if len(new_notifications) != 0:
      for n in new_notifications:
        self.seen.append(n['id'])
        title = 'GitHub: {}'.format(n['repository']['full_name'])
        send_message(title, n['subject']['title'])

  def get_notifications(self):
    res = make_github_request('notifications', {
      'all': 'false',
      'page': 1,
      'per_page': 100
    })
    return res

  def start(self):
    while True:
      try:
        notifications = self.get_notifications()
        self.notify(notifications)
      except KeyboardInterrupt:
        os._exit(0)
      except Exception as e:
        print(e)
      time.sleep(60)

def main():
  token = read_auth_token()
  if isinstance(token, str):
    daemon = github_notify_daemon()
    daemon.start()
  else:
    raise ValueError('No GitHub auth token present')

if __name__ == '__main__':
  main()
