"""
Genera il report HTML dalle statistiche estratte dal parser RVTools.
"""

from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import json


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def build_report(data: dict, report_id: str, filename: str, custom: dict = None, custom_title: str = "", custom_date: str = "") -> str:
    """
    Genera l'HTML del report e lo restituisce come stringa.
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"])
    )

    def fmt_gb(val):
        if val is None:
            return "0"
        # Round to nearest integer and use dot for thousands
        s = f"{int(round(val)):,}"
        return s.replace(",", ".")

    def fmt_int(val):
        if val is None:
            return "0"
        s = f"{int(round(val)):,}"
        return s.replace(",", ".")

    env.filters["fmt_gb"] = fmt_gb
    env.filters["fmt_int"] = fmt_int

    template = env.get_template("report.html")

    # Raggruppa VM spente per datacenter + host
    vms_off_by_dc: dict = {}
    for vm in data["vms_off"]:
        dc = vm.datacenter or "N/D"
        host = vm.host or "N/D"
        vms_off_by_dc.setdefault(dc, {}).setdefault(host, []).append(vm)

    # Raggruppa VM accese per datacenter + host
    vms_on_by_dc: dict = {}
    for vm in data["vms_on"]:
        dc = vm.datacenter or "N/D"
        host = vm.host or "N/D"
        vms_on_by_dc.setdefault(dc, {}).setdefault(host, []).append(vm)

    rendered = template.render(
        report_id=report_id,
        filename=filename,
        summary_on=data["summary_on"],
        summary_off=data["summary_off"],
        summary_total=data["summary_total"],
        datacenters=data["datacenters"],
        host_stats=data["host_stats"],
        vms_on=data["vms_on"],
        vms_off=data["vms_off"],
        vms_off_by_dc=vms_off_by_dc,
        vms_on_by_dc=vms_on_by_dc,
        custom=custom or {},
        generation_date=custom_date or datetime.now().strftime("%d/%m/%Y %H:%M"),
        report_title=custom_title,
    )
    return rendered
