"""
Automation Module
=================
Módulo de automações com n8n para o TikTrend Finder.
"""

from .n8n_orchestrator import (DEFAULT_AUTOMATIONS, AutomationConfig,
                               AutomationEvent, AutomationPriority,
                               AutomationResult, AutomationType, ChannelType,
                               N8nOrchestrator, get_orchestrator)
from .scheduler import (AutomationScheduler, ScheduledEvent, SchedulerStats,
                        ScheduleStatus, ScheduleType, get_scheduler,
                        start_scheduler, stop_scheduler)

__all__ = [
    # Orchestrator
    "N8nOrchestrator",
    "get_orchestrator",
    "AutomationType",
    "ChannelType",
    "AutomationPriority",
    "AutomationConfig",
    "AutomationEvent",
    "AutomationResult",
    "DEFAULT_AUTOMATIONS",
    # Scheduler
    "AutomationScheduler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    "ScheduledEvent",
    "SchedulerStats",
    "ScheduleStatus",
    "ScheduleType",
]

