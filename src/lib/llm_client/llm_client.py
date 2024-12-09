import abc
import json
import logging
from typing import Dict, List

from src.types.schema import LlmMessage


class LlMClient(abc.ABC):

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._memory: List[LlmMessage] = []

    def send_message_expecting_json_response(
        self, message: str, num_attempts: int = 10, **kwargs
    ) -> Dict:
        response = self.send_message(message, **kwargs)

        # Clean the response from any non-json characters
        response = response.removeprefix('```json').removesuffix('```').removeprefix('```').strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self._logger.error(f"Could not parse response as json: {response}")
            # Remove the last two messages from memory since they are invalid
            self._memory = self._memory[:-2]
            if num_attempts > 0:
                self._logger.info(f"Retrying {num_attempts} more times")
                return self.send_message_expecting_json_response(
                    message=message, num_attempts=num_attempts - 1, **kwargs
                )
            raise

    def reset_memory(self):
        self._memory = []
        self._logger.info("Memory reset successfully")

    def send_message(
        self,
        message: str,
        role: str = "user",
        add_to_memory_without_response: bool = False,
        **kwargs,
    ) -> str:
        user_message = LlmMessage(role=role, content=message)

        if add_to_memory_without_response:
            self._memory.append(user_message)
            return ""

        response = self._send_message_implementation_specific_logic(
            message=user_message, **kwargs
        )

        self._memory.extend([user_message, response])

        return response.content

    @abc.abstractmethod
    def _send_message_implementation_specific_logic(
        self, message: LlmMessage, **kwargs
    ) -> LlmMessage:
        pass
