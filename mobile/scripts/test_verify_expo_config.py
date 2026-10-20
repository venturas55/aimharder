import copy
import json
import unittest
from pathlib import Path

from verify_expo_config import verify


class VerifyExpoConfigTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path('app.json').read_text())['expo']
        self.config['sdkVersion'] = '57.0.0'
        self.config['ios']['bundleIdentifier'] = 'es.example.aimharder'
        self.env = {'APPLE_BUNDLE_ID': 'es.example.aimharder', 'APPLE_TEAM_ID': 'AB12345678',
                    'EXPO_PUBLIC_API_URL': 'https://example.com/api'}

    def test_valid_config(self):
        verify(self.config, self.env)

    def test_wrong_bundle_or_missing_tablet_support(self):
        for key, value in [('bundleIdentifier', 'es.example.other'), ('supportsTablet', False)]:
            config = copy.deepcopy(self.config)
            config['ios'][key] = value
            with self.assertRaises(ValueError):
                verify(config, self.env)

    def test_invalid_api_urls(self):
        for url in ['http://example.com/api', 'https://example.com', 'https://user:pass@example.com/api']:
            with self.assertRaises(ValueError):
                verify(self.config, {**self.env, 'EXPO_PUBLIC_API_URL': url})

    def test_wrong_sdk_or_missing_icon(self):
        for key, value in [('sdkVersion', '58.0.0'), ('icon', './missing.png')]:
            with self.assertRaises(ValueError):
                verify({**self.config, key: value}, self.env)


if __name__ == '__main__':
    unittest.main()
