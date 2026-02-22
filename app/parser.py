"""
RVTools Excel parser.
Legge i fogli vInfo e vHost dal file rvtools.xlsx
e calcola le statistiche per datacenter, host e tipo VM.
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class VMInfo:
    name: str
    power_state: str          # poweredOn / poweredOff / suspended
    host: str
    datacenter: str
    cluster: str
    num_cpu: int
    memory_mb: float          # vRAM in MB
    disk_used_gb: float       # Storage in use [GB]
    disk_provisioned_gb: float  # Storage provisioned [GB]
    num_vcpu: int             # vCPU (uguale a num_cpu per RVTools)
    os: str


@dataclass
class HostStats:
    name: str
    datacenter: str
    cluster: str
    num_cpu: int = 0          # CPU fisiche
    cpu_hz: float = 0         # Speed (GHz)
    memory_gb: float = 0      # RAM fisica GB
    vms_on: List[VMInfo] = field(default_factory=list)
    vms_off: List[VMInfo] = field(default_factory=list)


def _safe_float(val, default=0.0):
    try:
        return float(val) if pd.notna(val) else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    try:
        return int(float(val)) if pd.notna(val) else default
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=""):
    if pd.isna(val) if not isinstance(val, str) else False:
        return default
    return str(val).strip() if val is not None else default


def parse_rvtools(filepath: str) -> dict:
    """
    Legge il file RVTools xlsx e restituisce un dict con tutte le statistiche.
    """
    xl = pd.ExcelFile(filepath)
    sheet_names = xl.sheet_names

    # ---- Legge vInfo (VM inventory) ----
    # Prova nomi comuni del foglio
    vinfo_sheet = None
    for name in ["vInfo", "vinfo", "VMInfo"]:
        if name in sheet_names:
            vinfo_sheet = name
            break
    if vinfo_sheet is None:
        raise ValueError(f"Foglio vInfo non trovato. Fogli disponibili: {sheet_names}")

    df_vinfo = xl.parse(vinfo_sheet, header=0)
    df_vinfo.columns = [str(c).strip() for c in df_vinfo.columns]

    # ---- Mappa le colonne RVTools standard ----
    COL_MAP = {
        "VM": ["VM", "Name", "VM Name"],
        "Powerstate": ["Powerstate", "Power State", "State"],
        "Host": ["Host", "ESX Host", "ESXi Host"],
        "Datacenter": ["Datacenter", "DC"],
        "Cluster": ["Cluster"],
        "CPUs": ["CPUs", "CPU", "vCPUs", "Num CPUs"],
        "Memory": ["Memory", "Memory MB", "RAM MB", "Memory (MB)", "Memory MiB"],
        "Disk gb": ["Provisioned MiB", "Disk MiB", "Disk GB", "Total disk (GB)", "Provisioned MB", "Disk (GB)"],
        "In Use MB": ["In Use MiB", "In Use MB", "Used Space MB", "Used disk (MB)", "Disk usage (MB)"],
        "OS": ["OS according to the VMware Tools", "OS", "Guest OS", "OS according to the configuration file"],
    }

    # Match case-insensitive
    def find_col(df, candidates):
        lower_cols = {col.lower().strip(): col for col in df.columns}
        for c in candidates:
            if c.lower().strip() in lower_cols:
                return lower_cols[c.lower().strip()]
        return None

    col_name = find_col(df_vinfo, COL_MAP["VM"])
    col_power = find_col(df_vinfo, COL_MAP["Powerstate"])
    col_host = find_col(df_vinfo, COL_MAP["Host"])
    col_dc = find_col(df_vinfo, COL_MAP["Datacenter"])
    col_cluster = find_col(df_vinfo, COL_MAP["Cluster"])
    col_cpu = find_col(df_vinfo, COL_MAP["CPUs"])
    col_mem = find_col(df_vinfo, COL_MAP["Memory"])
    col_disk_prov = find_col(df_vinfo, COL_MAP["Disk gb"])
    col_disk_used = find_col(df_vinfo, COL_MAP["In Use MB"])
    col_os = find_col(df_vinfo, COL_MAP["OS"])

    vms: List[VMInfo] = []
    for _, row in df_vinfo.iterrows():
        name = _safe_str(row.get(col_name, "")) if col_name else ""
        if not name:
            continue
        power = _safe_str(row.get(col_power, "poweredOff")) if col_power else "poweredOff"
        host = _safe_str(row.get(col_host, "")) if col_host else ""
        dc = _safe_str(row.get(col_dc, "")) if col_dc else ""
        cluster = _safe_str(row.get(col_cluster, "")) if col_cluster else ""
        cpu = _safe_int(row.get(col_cpu, 0)) if col_cpu else 0
        mem_mb = _safe_float(row.get(col_mem, 0)) if col_mem else 0.0
        
        # Disk: converti MiB/MB in GB se necessario
        disk_prov_raw = _safe_float(row.get(col_disk_prov, 0)) if col_disk_prov else 0.0
        disk_used_raw = _safe_float(row.get(col_disk_used, 0)) if col_disk_used else 0.0
        
        # Heuristic: se il valore è > 10000 o la colonna contiene MiB/MB, dividi per 1024
        def to_gb(val, col_name):
            if not col_name: return val
            if "mib" in col_name.lower() or "mb" in col_name.lower() or val > 10000:
                return val / 1024
            return val

        disk_prov_gb = to_gb(disk_prov_raw, col_disk_prov)
        disk_used_gb = to_gb(disk_used_raw, col_disk_used)
        
        os_name = _safe_str(row.get(col_os, "")) if col_os else ""

        vms.append(VMInfo(
            name=name,
            power_state=power.lower(),
            host=host,
            datacenter=dc,
            cluster=cluster,
            num_cpu=cpu,
            memory_mb=mem_mb,
            disk_used_gb=round(disk_used_gb, 3),
            disk_provisioned_gb=round(disk_prov_gb, 3),
            num_vcpu=cpu,
            os=os_name,
        ))

    # ---- Legge vHost (host fisici) ----
    vhost_sheet = None
    for name in ["vHost", "vhost", "HostInfo"]:
        if name in sheet_names:
            vhost_sheet = name
            break

    host_stats: Dict[str, HostStats] = {}
    if vhost_sheet:
        df_vhost = xl.parse(vhost_sheet, header=0)
        df_vhost.columns = [str(c).strip() for c in df_vhost.columns]
        col_hname = find_col(df_vhost, ["Host", "Name"])
        col_hdc = find_col(df_vhost, ["Datacenter", "DC"])
        col_hcluster = find_col(df_vhost, ["Cluster"])
        col_hcpu = find_col(df_vhost, ["# CPU", "CPUs", "Num CPUs", "CPU"])
        col_hmem = find_col(df_vhost, ["# Memory", "Memory GB", "Memory MB", "RAM"])
        for _, row in df_vhost.iterrows():
            hname = _safe_str(row.get(col_hname, "")) if col_hname else ""
            if not hname:
                continue
            hdc = _safe_str(row.get(col_hdc, "")) if col_hdc else ""
            hcluster = _safe_str(row.get(col_hcluster, "")) if col_hcluster else ""
            hcpu = _safe_int(row.get(col_hcpu, 0)) if col_hcpu else 0
            hmem_raw = _safe_float(row.get(col_hmem, 0)) if col_hmem else 0.0
            hmem_gb = hmem_raw / 1024 if hmem_raw > 1000 else hmem_raw
            host_stats[hname] = HostStats(
                name=hname,
                datacenter=hdc,
                cluster=hcluster,
                num_cpu=hcpu,
                memory_gb=round(hmem_gb, 2),
            )

    # ---- Associa VM agli host ----
    for vm in vms:
        if vm.host not in host_stats:
            host_stats[vm.host] = HostStats(
                name=vm.host,
                datacenter=vm.datacenter,
                cluster=vm.cluster,
            )
        hs = host_stats[vm.host]
        if not hs.datacenter and vm.datacenter:
            hs.datacenter = vm.datacenter
        if vm.power_state == "poweredon":
            hs.vms_on.append(vm)
        else:
            hs.vms_off.append(vm)

    # ---- Calcola summary globale ----
    vms_on = [v for v in vms if v.power_state == "poweredon"]
    vms_off = [v for v in vms if v.power_state != "poweredon"]

    def vm_summary(vm_list):
        os_counts = {"windows": 0, "linux": 0, "other": 0}
        os_vms = {"windows": [], "linux": [], "other": []}
        for v in vm_list:
            os = (v.os or "").lower()
            if "windows" in os:
                os_counts["windows"] += 1
                os_vms["windows"].append(v)
            elif any(k in os for k in ["linux", "ubuntu", "debian", "centos", "red hat", "suse", "photon"]):
                os_counts["linux"] += 1
                os_vms["linux"].append(v)
            else:
                os_counts["other"] += 1
                os_vms["other"].append(v)

        return {
            "count": len(vm_list),
            "tot_vcpu": sum(v.num_vcpu for v in vm_list),
            "tot_vram_gb": round(sum(v.memory_mb for v in vm_list) / 1024, 3),
            "tot_disk_used_gb": round(sum(v.disk_used_gb for v in vm_list), 3),
            "tot_disk_prov_gb": round(sum(v.disk_provisioned_gb for v in vm_list), 3),
            "os_counts": os_counts,
            "os_vms": os_vms,
        }

    summary_on = vm_summary(vms_on)
    summary_off = vm_summary(vms_off)
    summary_total = {
        "count": summary_on["count"] + summary_off["count"],
        "tot_vcpu": summary_on["tot_vcpu"] + summary_off["tot_vcpu"],
        "tot_vram_gb": round(summary_on["tot_vram_gb"] + summary_off["tot_vram_gb"], 3),
        "tot_disk_used_gb": round(summary_on["tot_disk_used_gb"] + summary_off["tot_disk_used_gb"], 3),
        "tot_disk_prov_gb": round(summary_on["tot_disk_prov_gb"] + summary_off["tot_disk_prov_gb"], 3),
    }

    # ---- Raggruppa per datacenter ----
    datacenters: Dict[str, dict] = {}
    for vm in vms:
        dc = vm.datacenter or "N/D"
        if dc not in datacenters:
            datacenters[dc] = {"vms_on": [], "vms_off": []}
        if vm.power_state == "poweredon":
            datacenters[dc]["vms_on"].append(vm)
        else:
            datacenters[dc]["vms_off"].append(vm)

    dc_summaries = {}
    for dc, data in datacenters.items():
        dc_summaries[dc] = {
            "on": vm_summary(data["vms_on"]),
            "off": vm_summary(data["vms_off"]),
        }

    return {
        "vms_on": vms_on,
        "vms_off": vms_off,
        "summary_on": summary_on,
        "summary_off": summary_off,
        "summary_total": summary_total,
        "host_stats": host_stats,
        "datacenters": dc_summaries,
        "all_vms": vms,
        "sheet_names": sheet_names,
    }
