import html
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ElementTree

# Needs to be defined
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
telegram_thread_id = os.getenv('TELEGRAM_THREAD_ID')
github_event_before = os.getenv('GITHUB_EVENT_BEFORE', '')

# Already defined
github_repository = os.getenv('GITHUB_REPOSITORY')
github_sha = os.getenv('GITHUB_SHA')

MAX_LISTED = 10
MAX_TEXT_LENGTH = 100


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, check=True, text=True).stdout.strip()


def parse_strings(xml):
    root = ElementTree.fromstring(xml)
    return {element.get('name'): ''.join(element.itertext()) for element in root.iter('string')}


def base_revision():
    # A force push replaces the previous head, and the checkout doesn't have it.
    if github_event_before.strip('0'):
        exists = subprocess.run(['git', 'cat-file', '-e', f'{github_event_before}^{{commit}}'], capture_output=True)
        if exists.returncode == 0:
            return github_event_before
    return git('rev-parse', f'{github_sha}~1')


def strings_at(revision):
    result = subprocess.run(['git', 'show', f'{revision}:values/strings.xml'], capture_output=True)
    return parse_strings(result.stdout) if result.returncode == 0 else {}


def strings_to_translate(before, after):
    return [(name, text) for name, text in after.items() if before.get(name) != text]


def display(text):
    text = text.replace("\\'", "'").replace('\\"', '"')
    return text if len(text) <= MAX_TEXT_LENGTH else text[:MAX_TEXT_LENGTH - 3] + '...'


def message(strings, compare_url, repository_url):
    count = len(strings)
    lines = [f"<b>{count} {'string' if count == 1 else 'strings'} to translate</b>", '']
    lines += [f'- <code>{html.escape(name, quote=False)}</code> {html.escape(display(text), quote=False)}' for name, text in strings[:MAX_LISTED]]
    if count > MAX_LISTED:
        lines.append(f'And {count - MAX_LISTED} more')
    lines += ['', f'<a href="{compare_url}">See the changes</a> | <a href="{repository_url}">How to translate</a>']
    return '\n'.join(lines)


def main():
    repository_url = f'https://github.com/{github_repository}'
    before = base_revision()

    strings =strings_to_translate(strings_at(before), strings_at(github_sha))
    if not strings:
        print('No new or changed strings, not notifying')
        return

    data = {
        'chat_id': telegram_chat_id,
        'parse_mode': 'HTML',
        'text': message(strings, f'{repository_url}/compare/{before}...{github_sha}', repository_url),
        'disable_web_page_preview': 'true',
        'disable_notification': 'true',
    }
    if telegram_thread_id:
        data['message_thread_id'] = telegram_thread_id
    request = urllib.request.Request(
        f'https://api.telegram.org/bot{telegram_token}/sendMessage',
        data=urllib.parse.urlencode(data).encode(),
    )
    try:
        with urllib.request.urlopen(request) as response:
            print(response.read().decode())
    except urllib.error.HTTPError as error:
        print(error.read().decode())
        raise


if __name__ == '__main__':
    main()
