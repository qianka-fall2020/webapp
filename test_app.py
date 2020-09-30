import unittest

from helper import password_validator


class TestPasswrod(unittest.TestCase):
	def test_pass(self):
		self.assertEqual(password_validator("1234sssss"), True)
		self.assertEqual(password_validator("1234ssss"), False)
		self.assertEqual(password_validator("12345678"), False)
		self.assertEqual(password_validator("123456789"), False)
		self.assertEqual(password_validator("sssssssss"), False)
		self.assertEqual(password_validator("ssssssss"), False)

if __name__ == '__main__':
    unittest.main()