import logging
import os
from typing import Dict, Optional, List

from src.lib.llm_client import llm_client_factory
from src.services.repository_reader_service import RepositoryReaderService
from src.types.enums import CodedFileAction
from src.types.schema import CodedFileResponse


class CodingService:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._llm_client = llm_client_factory()
        self._repo_reader_service = RepositoryReaderService()

    @property
    def repo_reader_service(self):
        return self._repo_reader_service

    def code_feature(
        self, task: str, local_repo_path: Optional[str] = None
    ) -> List[CodedFileResponse]:
        self._logger.info(f"Asking the llm to code the feature: {task}")

        # Based on the feature request, ask the llm to code the feature.
        # The llm should return a list of files and their updated content.
        files = self._llm_client.send_message_expecting_json_response(
            f"""
            You are a senior software engineer at a tech company.
            Based on the code I showed you previously, please implement the following feature: {task}.

            Your response must be a valid JSON object with the following format:

            [
            {{ "file_path": "file_path_1", "content (optional)": "content_1", action: "CREATE" | "UPDATE" | "DELETE" }},
            {{ "file_path": "file_path_2", "content (optional)": "content_1", action: "CREATE" | "UPDATE" | "DELETE" }},
            ]

            Additional Requirements:
            Always create an EXPLANATION.md file in the root directory of the repository that explains the changes made.
            The code that I showed you is the most important - you must take it into account when implementing the feature.
            If a file already exists, update the file with the new content and do not create a new file.
            Make sure to look for files if they are similar to those that you are creating or updating.
            Only return the JSON object. No additional text or explanation.
            The content for each file must be JSON-serializable.
            Ensure your response reflects all necessary changes across multiple files.
            I will feed your response directly to a JSON parser, so it must strictly adhere to the JSON format.
            """
        )

        files = [CodedFileResponse.model_validate(file) for file in files]

        if local_repo_path:
            for file in files:
                file.file_path = os.path.join(
                    local_repo_path,
                    file.file_path.replace(local_repo_path, "").lstrip("/"),
                )

        return files

    def write_code(self, coded_files: List[CodedFileResponse], local_repo_path: str):
        if len(local_repo_path) < 20:
            raise ValueError("local_repo_path is too short")

        self._logger.info("Writing the code to the local repository")
        for coded_file in coded_files:
            self._handle_coded_feature_file_response(coded_file=coded_file)

        self._logger.info("All files written successfully")

    def _handle_coded_feature_file_response(self, coded_file: CodedFileResponse):
        return {
            CodedFileAction.CREATE: lambda: self._create_file(
                file_abs_path=coded_file.file_path, content=coded_file.content
            ),
            CodedFileAction.UPDATE: lambda: self._update_file(
                file_abs_path=coded_file.file_path, content=coded_file.content
            ),
            CodedFileAction.DELETE: lambda: self._delete_file(
                file_abs_path=coded_file.file_path
            ),
        }[coded_file.action]()

    def _create_file(self, file_abs_path: str, content: str):
        self._logger.info(f"Creating file: {file_abs_path}")

        # Ensure that the parent directory exists
        os.makedirs(os.path.dirname(file_abs_path), exist_ok=True)

        with open(file_abs_path, "w") as f:
            f.write(content)

        self._logger.debug(f"File created: {file_abs_path}")

    def _update_file(self, file_abs_path: str, content: str):
        self._logger.info(f"Updating file: {file_abs_path}")

        with open(file_abs_path, "w") as f:
            f.write(content)

        self._logger.debug(f"File updated: {file_abs_path}")

    def _delete_file(self, file_abs_path: str):
        self._logger.info(f"Deleting file: {file_abs_path}")
        os.remove(file_abs_path)
        self._logger.debug(f"File deleted: {file_abs_path}")

    def learn_code(self, file_abs_path_to_content: Dict[str, str]):
        self._logger.info("Teaching the llm the code")

        for file_abs_path, content in file_abs_path_to_content.items():
            self._llm_client.send_message(
                f"""
                #########################
                # {file_abs_path}
                {content}
                #########################
                """,
                add_to_memory_without_response=True,
            )

        self._logger.info("Taught the llm the code")

    def perform_code_review(self):
        prompt = """
        AI Agent Code Review Prompt
        
        You are tasked with reviewing an input code file to identify potential bugs, issues, and areas for improvement. Your output should be a structured JSON list where each entry includes the following properties:
        
        explanation: A concise description of the issue, including why it might cause problems or be suboptimal, or how can it be improved.
        fix_suggestion: A clear suggestion for how to fix the issue, including a brief explanation of why the fix works.
        Your analysis should include syntax errors, logical bugs, performance issues, potential security vulnerabilities, and non-compliance with coding best practices.
        
        Input: A code file in Python (or specify another language if needed).
        Output: A JSON list in the format specified above.
        
        Additional Instructions:
        
        Ensure that your explanations and suggestions are detailed enough to guide a developer in addressing the issues.
        Do not include unrelated or unnecessary details in the JSON output.
        Try to review the architecture, design, and implementation of the code comprehensively.
        Do not only focus on syntax errors; consider all aspects of code quality and robustness.
        Be VERY critical but also constructive in your feedback. 
        If no issues are found in a specific function, exclude it from the output.
        Here is an example of the expected JSON structure:
        
        [
          {
            "explanation": "The function does not handle non-numeric input, which could cause a runtime error.",
            "suggestion": "Add input validation to check if 'a' and 'b' are numbers before performing the addition."
          },
          {
            "explanation": "Division by zero is not handled, leading to a potential ZeroDivisionError.",
            "suggestion": "Include a check to ensure 'b' is not zero before performing the division."
          }
        ]
        
        Only return the JSON object. No additional text or explanation AT ALL COSTS.
        I will feed your response directly to a JSON parser, so it must strictly adhere to the JSON format.
        If bugs were not found, do not include any entries in the 'issues' list.
        """
        return self._llm_client.send_message_expecting_json_response(prompt)