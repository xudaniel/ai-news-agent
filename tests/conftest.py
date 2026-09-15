"""Upstream regression suite explicitly exercises the supported legacy profile.
Chinese fork defaults are checked in a clean subprocess in test_top5.py.
"""
import os

os.environ["DIGEST_FORMAT"] = "headlines"
os.environ["DIGEST_TIMEZONE"] = "America/New_York"
os.environ["DIGEST_ISSUE_TITLE_PREFIX"] = "AI Headlines"
