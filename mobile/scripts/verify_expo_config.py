"""Validate the resolved Expo config before generating the signed iOS project."""
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


def verify(config, env):
    ios = config.get('ios', {})
    bundle_id = env['APPLE_BUNDLE_ID']
    if not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', bundle_id):
        raise ValueError('APPLE_BUNDLE_ID must be an explicit reverse-DNS identifier')
    if not re.fullmatch(r'[A-Z0-9]{10}', env['APPLE_TEAM_ID']):
        raise ValueError('APPLE_TEAM_ID must contain 10 uppercase letters/digits')
    if ios.get('bundleIdentifier') != bundle_id:
        raise ValueError('Expo bundleIdentifier does not match APPLE_BUNDLE_ID')
    if ios.get('supportsTablet') is not True:
        raise ValueError('iPad support must remain enabled')
    if str(config.get('sdkVersion', '')).split('.')[0] != '57':
        raise ValueError('Expected Expo SDK 57')
    icon = config.get('icon')
    if not icon or not Path(icon).is_file():
        raise ValueError('Configured application icon does not exist')
    url = urlsplit(env['EXPO_PUBLIC_API_URL'])
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('EXPO_PUBLIC_API_URL must be a public HTTPS URL without credentials, query or fragment')
    if url.path.rstrip('/') != '/api':
        raise ValueError('EXPO_PUBLIC_API_URL must end in /api')


if __name__ == '__main__':
    try:
        verify(json.loads(Path(sys.argv[1]).read_text()), os.environ)
    except (ValueError, KeyError, OSError) as error:
        sys.exit(str(error))
    print('Expo SDK 57, bundle identifier, iPad, icon and API URL verified')
