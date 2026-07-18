"""Protocol interfaces for constructing Agent-visible task inputs."""

from sci_modeling_bench.protocol.agent_input import (
    AgentFieldRole,
    AgentInputBundle,
    AgentInputContext,
    AgentInputField,
    AgentInputManifest,
    AgentInputView,
    AgentViewRole,
    agent_input_field,
    agent_input_manifest,
    agent_table_view,
)
from sci_modeling_bench.protocol.protocol import (
    Protocol,
    ProtocolDataT,
    ProtocolOutputT,
)

__all__ = [
    "AgentFieldRole",
    "AgentInputBundle",
    "AgentInputContext",
    "AgentInputField",
    "AgentInputManifest",
    "AgentInputView",
    "AgentViewRole",
    "Protocol",
    "ProtocolDataT",
    "ProtocolOutputT",
    "agent_input_field",
    "agent_input_manifest",
    "agent_table_view",
]
