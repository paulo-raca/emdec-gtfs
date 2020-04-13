from datetime import date
from .csvmodel import CsvModel

@CsvModel('feed_info.txt')
class FeedInfo:
    feed_publisher_name: str
    feed_publisher_url: str
    feed_lang: str
    feed_start_date: date
    feed_end_date: date
    feed_version: str

