# Copyright (c) 2023 - 2024, HaiyangLi <quantocean.li at gmail dot com>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ...data_models import AnthropicEndpointResponseBody
from .content_models import ContentBlock
from .usage_models import Usage


class AnthropicMessageResponseBody(AnthropicEndpointResponseBody):
    id: str = Field(description="Unique object identifier")

    type: Literal[
        "message",
        "message_start",
        "content_block_start",
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop",
    ] = Field(description="Type of the response")

    role: Literal["assistant"] | None = Field(
        default=None,
        description="Conversational role of the generated message. Always 'assistant' for non-stream responses",
    )

    content: list[ContentBlock] | None = Field(
        default=None,
        description="Content generated by the model",
    )

    model: str | None = Field(
        default=None,
        description="The model that handled the request",
    )

    stop_reason: (
        Literal["end_turn", "max_tokens", "stop_sequence", "tool_use"] | None
    ) = Field(
        default=None,
        description="""The reason that we stopped. May be:
        "end_turn": the model reached a natural stopping point
        "max_tokens": exceeded the requested max_tokens or model's maximum
        "stop_sequence": one of the provided custom stop_sequences was generated
        "tool_use": the model invoked one or more tools""",
    )

    stop_sequence: str | None = Field(
        default=None,
        description="Which custom stop sequence was generated, if any",
    )

    usage: Usage | None = Field(
        default=None,
        description="""Billing and rate-limit usage. Anthropic's API bills and
        rate-limits by token counts, as tokens represent the underlying cost to our systems.""",
    )

    # Stream-specific fields
    message: "AnthropicMessageResponseBody | None" = Field(
        default=None,
        description="Initial message object in stream response",
    )

    content_block: dict | None = Field(
        default=None,
        description="Content block information in stream response",
    )

    delta: dict | None = Field(
        default=None,
        description="Delta update in stream response",
    )

    message_id: str | None = Field(
        default=None,
        description="Message ID reference in stream response",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def validate_stream_fields(self):
        # For stream responses, some fields are optional
        if self.type != "message":
            return self

        # For regular message responses, validate required fields
        if not self.role:
            raise ValueError("role is required for message responses")
        if self.content is None:
            raise ValueError("content is required for message responses")
        if not self.model:
            raise ValueError("model is required for message responses")

        return self
