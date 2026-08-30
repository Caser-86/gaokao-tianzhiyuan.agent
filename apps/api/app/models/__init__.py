"""Package for application data models."""

from .access_control import RuntimeSetting, UserEntitlement
from .catalog import (
    FeaturedMajor,
    FeaturedRotationRule,
    FeaturedSchool,
    Major,
    MajorRankingReference,
    School,
    SchoolMajorRelation,
    SchoolRankingReference,
    SearchEntry,
)
from .chat import ChatMessage, ChatSession
from .content import SchoolContentVersion, VersionStatus
from .ingestion import MediaAnalysisEvent, ReviewQueue, WeChatMessageReceipt

__all__ = [
    "ChatMessage",
    "ChatSession",
    "FeaturedMajor",
    "FeaturedRotationRule",
    "FeaturedSchool",
    "Major",
    "MajorRankingReference",
    "MediaAnalysisEvent",
    "ReviewQueue",
    "RuntimeSetting",
    "School",
    "SchoolContentVersion",
    "SchoolMajorRelation",
    "SchoolRankingReference",
    "SearchEntry",
    "UserEntitlement",
    "VersionStatus",
    "WeChatMessageReceipt",
]
