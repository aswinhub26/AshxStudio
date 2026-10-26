import unittest
from app import app, clean_url, is_safe_url

class AshxStudioTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_health_endpoints(self):
        """Verify /api/health and /healthz endpoints return HTTP 200 and valid schema."""
        for path in ['/api/health', '/healthz']:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get('status'), 'healthy')
            self.assertEqual(data.get('service'), 'AshxStudio')
            self.assertIn('version', data)
            self.assertIsInstance(data.get('platforms'), list)
            self.assertIn('YouTube', data['platforms'])
            self.assertIn('Instagram', data['platforms'])
            self.assertIn('TikTok', data['platforms'])
            self.assertIn('X/Twitter', data['platforms'])

    def test_url_sanitization(self):
        """Verify fast regex normalization converts shorts & youtu.be to canonical watch URLs."""
        # Shorts normalization
        shorts_url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        self.assertEqual(clean_url(shorts_url), "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # youtu.be normalization
        shortened_url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(clean_url(shortened_url), "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Whitespace stripping
        padded_url = "  https://www.instagram.com/reel/C-123456/   "
        self.assertEqual(clean_url(padded_url), "https://www.instagram.com/reel/C-123456/")

    def test_ssrf_protection(self):
        """Verify is_safe_url blocks private, loopback, link-local and non-HTTP protocols."""
        self.assertTrue(is_safe_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(is_safe_url("https://google.com"))

        # Blocked targets
        self.assertFalse(is_safe_url("http://localhost:5000"))
        self.assertFalse(is_safe_url("http://127.0.0.1:8080"))
        self.assertFalse(is_safe_url("http://169.254.169.254/latest/meta-data/"))
        self.assertFalse(is_safe_url("file:///etc/passwd"))
        self.assertFalse(is_safe_url("ftp://server/file.mp4"))
        self.assertFalse(is_safe_url(""))
        self.assertFalse(is_safe_url("a" * 3000))

    def test_extract_missing_url(self):
        """Verify /api/extract rejects empty requests."""
        res = self.client.post('/api/extract', json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get('success'))
        self.assertIn('error', data)

    def test_download_missing_url(self):
        """Verify /api/download rejects empty url parameters."""
        res = self.client.get('/api/download')
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.get_json())

    def test_download_ssrf_blocked(self):
        """Verify /api/download rejects SSRF attacks."""
        res = self.client.get('/api/download?url=http://127.0.0.1:5000/api/health')
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.get_json())

    def test_static_routes(self):
        """Verify PWA manifest and service worker routes."""
        res_sw = self.client.get('/sw.js')
        self.assertEqual(res_sw.status_code, 200)
        self.assertIn('javascript', res_sw.content_type)

        res_manifest = self.client.get('/manifest.json')
        self.assertEqual(res_manifest.status_code, 200)

if __name__ == '__main__':
    unittest.main()
