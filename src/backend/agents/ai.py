import json
from typing import List
from autogen_core import (
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
    LLMMessage,
)
from autogen_core.tools import Tool
from context.session_manager import SessionManager
from models.messages import Session


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
        sessionManager: SessionManager,
    ) -> None:
        super().__init__(description)
        self._system_message = system_message
        self._model_client = model_client
        self.tools = tools
        self.delegate_tools = delegate_tools
        self._tools_dict = dict([(tool.name, tool) for tool in tools])
        self._delegate_tools_dict = dict([(tool.name, tool) for tool in delegate_tools])
        self._agent_topic_type = agent_topic_type
        self._user_topic_type = user_topic_type
        self._session_manager = sessionManager

    @message_handler
    async def handle_task(self, message: Session, ctx: MessageContext) -> None:
        print(f"{'-' * 80}\nHandling Task by: {self.id.type}\n", flush=True)
        llm_result = await self._get_llm_response(
            message.get_context_as_llm_messages(), ctx.cancellation_token
        )
        message.add_message(
            AssistantMessage(content=llm_result.content, source=self.id.type)
        )
        print(f"\nLLM Result:\n{llm_result}\n", flush=True)

        # keep running until we get a non-function call response
        while llm_result.finish_reason == "function_calls":
            function_call = llm_result.content[0]

            if function_call.name in self._tools_dict:
                print(f"Function call: {function_call.name} with arguments: {function_call.arguments}", flush=True)
                tool_object = self._tools_dict.get(function_call.name)
                result = await tool_object.run_json(
                    json.loads(function_call.arguments), ctx.cancellation_token
                )
                tool_call_results = tool_object.return_value_as_string(result)
                tool_execution_result = FunctionExecutionResult(
                    call_id=function_call.id,
                    name=function_call.name,
                    content=tool_call_results,
                    is_error=False,
                )
                print(f"Tool call results: {tool_call_results}", flush=True)
                message.add_message(
                    FunctionExecutionResultMessage(content=[tool_execution_result])
                )
                llm_result = await self._get_llm_response(
                    message.get_context_as_llm_messages(), ctx.cancellation_token
                )
                message.add_message(
                    AssistantMessage(content=llm_result.content, source=self.id.type)
                )
                print(
                    f"LLM Result after function execution:\n{llm_result}\n", flush=True
                )

            elif function_call.name in self._delegate_tools_dict:
                print(f"Delegate tool call: {function_call.name}", flush=True)
                tool_object = self._delegate_tools_dict.get(function_call.name)
                result = await tool_object.run_json(
                    json.loads(function_call.arguments), ctx.cancellation_token
                )
                # Assuming the tool returns a string indicating the target topic
                tool_call_results = tool_object.return_value_as_string(result)
                tool_execution_result = FunctionExecutionResult(
                    call_id=function_call.id,
                    name=function_call.name,
                    content=f"Transferred to {tool_call_results}. Adopt persona immediately.",
                    is_error=False,
                )
                message.add_message(
                    FunctionExecutionResultMessage(content=[tool_execution_result])
                )
                await self.publish_message(
                    message, topic_id=TopicId(tool_call_results, source=self.id.key)
                )
                print(f"Delegated to: {tool_call_results}\n{'-' * 80}\n", flush=True)
                return  # Task fully delegated, we're done
            else:
                raise ValueError(f"Unknown tool: {function_call.name}")

        message.current_agent = self.id.type
        message.status = "completed"
        self._session_manager._update_session(message)
        print(f"Task completed by {self.id.type}", flush=True)

    async def _get_llm_response(self, messages: List[LLMMessage], cancellation_token):
        """Get response from LLM with appropriate context and tools."""
        result = await self._model_client.create(
            messages=[self._system_message] + messages,
            tools=self.tools + self.delegate_tools,
            cancellation_token=cancellation_token,
        )
        return result
