# src/api/services/crewai_service.py

from infraware.main import InfrawareFlow, InfrawareState
from infraware.crews.docs_crew.docs_crew import DocsCrew
import os

class CrewAIService:
    def __init__(self, output_base: str, templates_dir: str):
        self.output_base = output_base
        self.templates_dir = templates_dir

    def generate_yaml_and_diagram(self, job_id: str, prompt: str) -> dict:
        output_dir = os.path.join(self.output_base, job_id)

        state = InfrawareState(
            prompt=prompt,
            project_name=job_id,
            templates_dir=self.templates_dir,
            output_dir=output_dir,
            verbose=False
        )
        flow = InfrawareFlow(state)
        flow.prompt()
        flow.generate_yaml()
        if not flow.validate_yaml(): raise Exception(state.error)
        if not flow.validate_dependencies(): raise Exception(state.error)
        if not flow.generate_diagrams(): raise Exception(state.error)

        return {
            "yaml": state.plain_yaml,
            "diagram_dir": output_dir
        }

    def generate_iac_and_docs(self, job_id: str, yaml_str: str) -> dict:
        output_dir = os.path.join(self.output_base, job_id)

        state = InfrawareState(
            prompt="", plain_yaml=yaml_str,
            project_name=job_id,
            templates_dir=self.templates_dir,
            output_dir=output_dir,
        )
        flow = InfrawareFlow(state)
        flow.generate_iac()

        doc_result = DocsCrew().crew().kickoff(inputs={"yaml_content": yaml_str})
        docs_md = doc_result.output

        return {
            "terraform_dir": output_dir,
            "docs_content": docs_md
        }
