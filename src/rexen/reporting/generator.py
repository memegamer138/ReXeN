
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
	counts = preprocessed.get("counts", {
		"subdomains": len(preprocessed.get("subdomains", [])),
		"discovered_urls": len(preprocessed.get("urls", [])),
		"out_of_scope_urls": len(preprocessed.get("out_of_scope_urls", [])),
		"probed_urls": len(preprocessed.get("live_url_records", [])) + len(preprocessed.get("failed_url_records", [])),
		"live_urls": len(preprocessed.get("live_urls", [])),
		"failed_urls": len(preprocessed.get("failed_url_records", [])),
	})
	validation_facts = {
		"counts": counts,
		"live_url_records": preprocessed.get("live_url_records", []),
		"failed_url_records": preprocessed.get("failed_url_records", []),
	}
	executive_summary = llm_generate_fn(f"""
	Write a concise, factual executive summary for an authorized reconnaissance report on {target}.
	Use only the observed data below. State whether live URL validation completed.
	Do not claim vulnerabilities, malicious intent, or security posture from discovery data alone.
	Use the backend-provided counts exactly. Do not recalculate or infer counts from raw URLs.
	The authoritative validation facts are below. A live URL is only one in live_url_records.
	A failed URL returned 4xx or 5xx and must not be described as live.

	Validation facts:
	{json.dumps(validation_facts, indent=2)}

	Recon data:
	{json.dumps(preprocessed, indent=2)}
	""")
	key_findings = llm_generate_fn(f"""
	List the key findings from this authorized reconnaissance of {target}.
	Separate observed discoveries from validated live services and hypotheses for manual testing.
	Do not treat a URL, filename, or encoded path as proof of a vulnerability.
	Exclude out-of-scope URLs from in-scope findings.
	Use the backend-provided counts exactly. Do not recalculate or infer counts from raw URLs.
	Use the validation facts below as the source of truth for statuses.

	Validation facts:
	{json.dumps(validation_facts, indent=2)}

	Recon data:
	{json.dumps(preprocessed, indent=2)}
	""")
	recommendations = llm_generate_fn(
		f"""
	You are assisting an authorized bug bounty hunter or penetration tester.
	Based only on the reconnaissance data below, recommend prioritized next investigation steps, not remediation.

	For each recommendation, you may use the following guidelines but do not restrict yourself to them:
	- identify the relevant URL, subdomain, or artifact
	- explain why it is interesting as an attack-surface lead
	- suggest safe manual validation or follow-up enumeration
	- identify relevant methods, parameters, authentication, or authorization checks when supported by the data
	- distinguish confirmed observations from hypotheses
	- distinguish confirmed observations from hypotheses
	- do not claim a vulnerability without evidence
	- treat unusual, encoded, or JavaScript-looking paths as collection artifacts or generic leads only
	- do not name XSS, SQL injection, XXE, traversal, authentication flaws, or impact unless the data contains direct supporting evidence
	- do not turn a path name into a vulnerability hypothesis
	- do not recommend manual testing of a URL as if it were live when its status is 4xx or 5xx
	- do not treat out-of-scope URLs as targets
	- respect authorized scope and rate limits
	- use the backend-provided counts exactly and do not recount raw URLs
	- use the backend-provided counts exactly and do not recount raw URLs
	- use only live_url_records for live assets
	- treat failed_url_records as unavailable/error responses, not live assets
	- do not recommend revalidating a URL solely because it returned 404

	Target: {target}

	Recon data:
	{json.dumps(preprocessed, indent=2)}
	"""
	)

	# Prepare context
	context = dict(preprocessed)
	context.update({
		"target": target,
		"generated": timestamp,
		"counts": counts,
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
	preprocessed = preprocess_results(results, target=target)

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