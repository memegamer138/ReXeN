
from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime
import json
import re

from rexen.reporting.preprocessor import preprocess_results

def render_template_report(preprocessed, target, results, output_dir=None, template_path=None, llm_generate_fn=None):
	"""
	Render a recon report using a Jinja2 template, with LLM-generated narrative sections.
	Args:
		preprocessed (dict): Preprocessed tool outputs.
		target (str): The scan target.
		results (dict): Raw tool outputs (for raw_output section).
		output_dir (str): Directory to save the report.
		template_path (str): Path to the Jinja2 template file.
		llm_generate_fn (callable): Function to call the LLM for narrative sections.
	Returns:
		str: Path to the generated report file.
	"""

	# Set default output_dir to src/rexen/reports if not provided
	if output_dir is None:
		output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../reports'))
	os.makedirs(output_dir, exist_ok=True)
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	# Extract domain for filename
	import re as _re
	domain_match = _re.search(r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", target)
	if domain_match:
		domain = domain_match.group(1).replace('.', '_')
	else:
		domain = target.replace('/', '_').replace(':', '_').replace('.', '_')
	report_path = os.path.join(output_dir, f"{domain}_{timestamp}.txt")

	# Set up Jinja2 environment
	if template_path is None:
		template_path = os.path.join(os.path.dirname(__file__), '../../templates/report_template.j2')
	env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
	template = env.get_template(os.path.basename(template_path))

	# LLM-generated narrative sections
	if llm_generate_fn is None:
		raise ValueError("llm_generate_fn must be provided to generate narrative sections with the LLM.")
	executive_summary = llm_generate_fn(f"Write an executive summary for a recon report on {target} based on this data:\n{json.dumps(preprocessed, indent=2)}")
	key_findings = llm_generate_fn(f"List the key findings for a recon report on {target} based on this data:\n{json.dumps(preprocessed, indent=2)}")
	recommendations = llm_generate_fn(f"Write recommendations for next steps or remediation for {target} based on this data:\n{json.dumps(preprocessed, indent=2)}")

	# Prepare context
	context = dict(preprocessed)
	context.update({
		"target": target,
		"generated": timestamp,
		"executive_summary": executive_summary,
		"key_findings": key_findings,
		"recommendations": recommendations,
		"raw_output": json.dumps(results, indent=2),
	})
	# Render template
	report_text = template.render(**context)
	with open(report_path, "w", encoding="utf-8") as f:
		f.write(report_text)
	return report_path


def generate_report(results, target, output_dir="reports", llm_generate_fn=None):
	"""
	Generate a professional recon report using the LLM, with preprocessed results.
	Args:
		results (dict): Raw tool outputs from the pipeline.
		target (str): The scan target (e.g., domain).
		output_dir (str): Directory to save the report.
		llm_generate_fn (callable): Function to call the LLM, signature: (prompt:str) -> str
	Returns:
		str: Path to the generated report file.
	"""
	os.makedirs(output_dir, exist_ok=True)
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	safe_target = target.replace("/", "_").replace(":", "_").replace(".", "_")
	report_path = os.path.join(output_dir, f"llm_report_{safe_target}_{timestamp}.txt")

	# Preprocess results
	preprocessed = preprocess_results(results)

	# Prepare LLM prompt
	prompt = (
		"Generate a professional recon report for the following target. "
		"Summarize key findings, highlight interesting endpoints, and provide recommendations.\n"
		f"Target: {target}\n"
		f"Scan Data: {json.dumps(preprocessed, indent=2)}"
	)

	# Call LLM (user must provide llm_generate_fn)
	if llm_generate_fn is None:
		raise ValueError("llm_generate_fn must be provided to generate the report with the LLM.")
	report_text = llm_generate_fn(prompt)

	with open(report_path, "w", encoding="utf-8") as f:
		f.write(report_text)
		f.write("\n\n---\nRaw Tool Output (for debugging):\n")
		f.write(json.dumps(results, indent=2))
	return report_path

# ---------------------------------- Fallback report generation if LLM fails or is not available ----------------------------------

def generate_report_fallback(results, target, output_dir="reports"):
	"""
	Generate a simple text report from pipeline results.
	Args:
		results (dict): Tool outputs from the pipeline.
		target (str): The scan target (e.g., domain).
		output_dir (str): Directory to save the report.
	Returns:
		str: Path to the generated report file.
	"""
	os.makedirs(output_dir, exist_ok=True)
	now = datetime.now()
	timestamp = now.strftime("%Y%m%d_%H%M%S")
	# Sanitize target for filename: remove/replace invalid characters
	safe_target = re.sub(r'[^A-Za-z0-9_.-]', '_', target)
	report_path = os.path.join(output_dir, f"report_{safe_target}_{timestamp}.txt")
	with open(report_path, "w", encoding="utf-8") as f:
		f.write(f"Recon Report for: {target}\n")
		f.write(f"Generated: {now}\n\n")
		for tool, output in results.items():
			f.write(f"=== {tool.upper()} ===\n")
			f.write(f"{output}\n\n")
	return report_path