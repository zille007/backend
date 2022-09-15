import unittest


if __name__ == '__main__':
    loader = unittest.TestLoader()
    tests = loader.discover("./Tests", pattern="*.py")
    testRunner = unittest.TextTestRunner()
    testRunner.run(tests)