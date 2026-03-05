"""
Basic report generator for recon pipeline MVP.
Generates a simple text report from pipeline results.
"""

import os
from datetime import datetime
import re
def generate_report(results, target, output_dir="reports"):
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