"""
aiconnex_zip_compiler.plugins - Extensible Multi-Stage Plugin Pipeline Package
"""

from .base import (
    BasePlugin,
    BaseDiscoveryPlugin,
    BaseParserPlugin,
    BaseAssemblerPlugin,
    BaseFeatureHarvesterPlugin,
    BaseSchemaNormalizerPlugin,
    MatchResult,
)
from .context import PipelineContext, PluginSnapshot, FileInventoryItem
from .registry import PluginRegistry, register_plugin, AmbiguousPluginMatchError, UnsupportedLayoutError

__all__ = [
    "BasePlugin",
    "BaseDiscoveryPlugin",
    "BaseParserPlugin",
    "BaseAssemblerPlugin",
    "BaseFeatureHarvesterPlugin",
    "BaseSchemaNormalizerPlugin",
    "MatchResult",
    "PipelineContext",
    "PluginSnapshot",
    "FileInventoryItem",
    "PluginRegistry",
    "register_plugin",
    "AmbiguousPluginMatchError",
    "UnsupportedLayoutError",
]
