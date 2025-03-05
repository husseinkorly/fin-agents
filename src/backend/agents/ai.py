import json
from typing import List

from autogen_core import (
    FunctionCall,
    MessageContext,
    RoutedAgent,
    TopicId,
    message_handler,
)
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    SystemMessage,
)
from autogen_core.tools import Tool
from models.messages import AgentResponse, UserRequest
from rich.console import Console
from rich.theme import Theme

# Create a console with a theme that defines "agent" as yellow
console = Console(theme=Theme({"agent": "yellow"}))


class AIAgent(RoutedAgent):
    def __init__(
        self,
        description: str,
        system_message: SystemMessage,
        model_client: ChatCompletionClient,
        tools: List[Tool],
        delegate_tools: List[Tool],
        agent_topic_type: str,
        user_topic_type: str,
    ) -> None:
        super().__init__(description)
        self._system_message = system_message
        self._model_client = model_client
        self._tools = dict([(tool.name, tool) for tool in tools])
        self._tool_schema = [tool.schema for tool in tools]
        self._delegate_tools = dict([(tool.name, tool) for tool in delegate_tools])
        self._delegate_tool_schema = [tool.schema for tool in delegate_tools]
        self._agent_topic_type = agent_topic_type
        self._user_topic_type = user_topic_type

    @message_handler
    async def handle_task(self, message: UserRequest, ctx: MessageContext) -> None:
        """Handle incoming task requests by either processing tools directly or delegating to other agents."""
        # Initial LLM call with user context
        llm_result = await self._get_llm_response(message, ctx.cancellation_token)

        # Process function calls if present
        while self._has_function_calls(llm_result.content):
            tool_call_results = []
            delegate_targets = []

            # Process each function call
            for call in llm_result.content:
                arguments = json.loads(call.arguments)

                if call.name in self._tools:
                    # Handle direct tool execution
                    result = await self._execute_tool(
                        call, arguments, ctx.cancellation_token
                    )
                    tool_call_results.append(result)
                elif call.name in self._delegate_tools:
                    # Handle delegation to other agents
                    delegate_task = await self._prepare_delegation(
                        call, arguments, message, ctx.cancellation_token
                    )
                    delegate_targets.append(delegate_task)
                else:
                    raise ValueError(f"Unknown tool: {call.name}")

            # Handle delegation if needed
            if delegate_targets:
                await self._delegate_to_agents(delegate_targets)
                if not tool_call_results:
                    return  # Task fully delegated, we're done

            # If we have tool results, continue the conversation
            if tool_call_results:
                message = self._update_message_context(
                    message, llm_result, tool_call_results
                )
                llm_result = await self._get_llm_response(
                    message, ctx.cancellation_token
                )

        # Task completed - send final response to user
        await self._publish_final_response(message, llm_result)

    # Helper methods
    async def _get_llm_response(self, message: UserRequest, cancellation_token):
        """Get response from LLM with appropriate context and tools."""
        result = await self._model_client.create(
            messages=[self._system_message] + message.context,
            tools=self._tool_schema + self._delegate_tool_schema,
            cancellation_token=cancellation_token,
        )
        console.print(f"[agent]{'-' * 80}\n{self.id.type}:\n{result.content}[/agent]")
        return result

    def _has_function_calls(self, content):
        """Check if content contains function calls."""
        return isinstance(content, list) and all(
            isinstance(m, FunctionCall) for m in content
        )

    async def _execute_tool(self, call, arguments, cancellation_token):
        """Execute a tool and format its result."""
        try:
            tool = self._tools[call.name]
            result = await tool.run_json(arguments, cancellation_token)
            result_as_str = tool.return_value_as_string(result)
            return FunctionExecutionResult(
                call_id=call.id, content=result_as_str, is_error=False
            )
        except Exception as e:
            print(f"Error executing tool {call.name}: {str(e)}")
            return FunctionExecutionResult(
                call_id=call.id, content=f"Error: {str(e)}", is_error=True
            )

    async def _prepare_delegation(self, call, arguments, message, cancellation_token):
        """Prepare task delegation to another agent."""
        tool = self._delegate_tools[call.name]
        result = await tool.run_json(arguments, cancellation_token)
        topic_type = tool.return_value_as_string(result)

        delegate_messages = list(message.context) + [
            AssistantMessage(content=[call], source=self.id.type),
            FunctionExecutionResultMessage(
                content=[
                    FunctionExecutionResult(
                        call_id=call.id,
                        content=f"Transferred to {topic_type}. Adopt persona immediately.",
                        is_error=False,
                    )
                ]
            ),
        ]
        return (topic_type, UserRequest(context=delegate_messages))

    async def _delegate_to_agents(self, delegate_targets):
        """Delegate tasks to other agents."""
        for topic_type, task in delegate_targets:
            print(
                f"{'-' * 80}\n{self.id.type}:\nDelegating to {topic_type}", flush=True
            )
            await self.publish_message(
                task, topic_id=TopicId(topic_type, source=self.id.key)
            )

    def _update_message_context(self, message, llm_result, tool_call_results):
        """Update message context with latest LLM response and tool results."""
        print(f"{'-' * 80}\n{self.id.type}:\n{tool_call_results}", flush=True)
        message.context.extend(
            [
                AssistantMessage(content=llm_result.content, source=self.id.type),
                FunctionExecutionResultMessage(content=tool_call_results),
            ]
        )
        return message

    async def _publish_final_response(self, message, llm_result):
        """Publish the final response back to the user."""
        try:
            assert isinstance(llm_result.content, str)
            message.context.append(
                AssistantMessage(content=llm_result.content, source=self.id.type)
            )
            await self.publish_message(
                AgentResponse(
                    context=message.context,
                    reply_to_topic=self._agent_topic_type,
                ),
                topic_id=TopicId(self._user_topic_type, source=self.id.key),
            )
        except Exception as e:
            print(f"Error publishing final response: {str(e)}")
