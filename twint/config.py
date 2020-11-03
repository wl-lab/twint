from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    Search: Optional[str] = None
    Geo: str = ""
    Near: str = None
    Lang: Optional[str] = None
    Year: Optional[int] = None
    Since: Optional[str] = None
    Until: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    Verified: bool = False
    To: str = None
    All = None
    Profile: bool = False
    TwitterSearch: bool = False
    RetriesCount: int = 10
    Images: bool = False
    Videos: bool = False
    Media: bool = False
    Replies: bool = False
    Query: str = None
    CustomQuery: str = ""
    PopularTweets: bool = False
    NativeRetweets: bool = False
    MinLikes: int = 0
    MinRetweets: int = 0
    MinReplies: int = 0
    Links: Optional[str] = None
    Source: Optional[str] = None
    MembersList: Optional[str] = None
    FilterRetweets: bool = False
    BackoffExponent: float = 3.0
    MinWaitTime: int = 0
    BearerToken: str = None
    GuestToken: str = None
    TweetsPortionSize: int = 100
