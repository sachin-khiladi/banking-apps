#!/usr/bin/env python3
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

REPORTS_DIR = Path("agents-communication/reports")
LIVE_FILE = REPORTS_DIR / "live-rg-bankapi-dev.normalized.json"
TF_FILE = REPORTS_DIR / "tf-dev-managed-resources.normalized.json"
RG_FILE = REPORTS_DIR / "live-rg-bankapi-dev.group.json"
OUT_JSON = REPORTS_DIR / "terraform-parity-report.json"
OUT_MD = REPORTS_DIR / "terraform-parity-report.md"

TF_TO_ARM_TYPE = {
    "azurerm_storage_account": "microsoft.storage/storageaccounts",
    "azurerm_log_analytics_workspace": "microsoft.operationalinsights/workspaces",
    "azurerm_application_insights": "microsoft.insights/components",
    "azurerm_key_vault": "microsoft.keyvault/vaults",
    "azurerm_user_assigned_identity": "microsoft.managedidentity/userassignedidentities",
    "azurerm_app_configuration": "microsoft.appconfiguration/configurationstores",
    "azurerm_container_registry": "microsoft.containerregistry/registries",
    "azurerm_container_app_environment": "microsoft.app/managedenvironments",
    "azurerm_container_app": "microsoft.app/containerapps",
    "azurerm_cosmosdb_account": "microsoft.documentdb/databaseaccounts",
    "azurerm_resource_group": "microsoft.resources/resourcegroups",
}

NON_COMPARABLE_TF_TYPES = {
    "azurerm_role_assignment",
    "azurerm_cosmosdb_sql_role_assignment",
    "azurerm_key_vault_secret",
    "azurerm_app_configuration_key",
    "azurerm_cosmosdb_sql_database",
    "azurerm_cosmosdb_sql_container",
}

LIKELY_PLATFORM_GENERATED_LIVE_TYPES = {
    "microsoft.alertsmanagement/smartdetectoralertrules",
}


@dataclass(frozen=True)
class ResourceKey:
    type: str
    name: str


def _load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text())


def _normalize_type_name(type_value: str, name_value: str) -> ResourceKey:
    return ResourceKey(type=(type_value or "").lower(), name=(name_value or "").lower())


def build_parity_report() -> Dict:
    live_resources = _load_json(LIVE_FILE)
    tf_resources = _load_json(TF_FILE)
    live_group = _load_json(RG_FILE)

    live_comparable: Dict[ResourceKey, Dict] = {}
    live_platform_generated: List[Dict] = []

    for item in live_resources:
        key = _normalize_type_name(item.get("type", ""), item.get("name", ""))
        if key.type in LIKELY_PLATFORM_GENERATED_LIVE_TYPES:
            live_platform_generated.append(item)
            continue
        live_comparable[key] = item

    tf_comparable: Dict[ResourceKey, Dict] = {}
    tf_non_comparable: List[Dict] = []

    for item in tf_resources:
        tf_type = item.get("type", "")
        if tf_type in NON_COMPARABLE_TF_TYPES:
            tf_non_comparable.append(item)
            continue

        arm_type = TF_TO_ARM_TYPE.get(tf_type)
        if arm_type is None:
            tf_non_comparable.append(item)
            continue

        key = _normalize_type_name(arm_type, item.get("name", ""))
        tf_comparable[key] = {
            "tf_type": tf_type,
            "arm_type": arm_type,
            "name": item.get("name"),
            "address": item.get("address"),
            "id": item.get("id"),
            "resource_group_name": item.get("resource_group_name"),
            "location": item.get("location"),
        }

    rg_name = (live_group.get("name") or "").lower()
    if rg_name:
        rg_key = ResourceKey(type="microsoft.resources/resourcegroups", name=rg_name)
        live_comparable[rg_key] = {
            "type": "microsoft.resources/resourcegroups",
            "name": live_group.get("name"),
            "location": live_group.get("location"),
            "tags": live_group.get("tags") or {},
            "id": live_group.get("id"),
        }

    tf_keys = set(tf_comparable.keys())
    live_keys = set(live_comparable.keys())

    missing_in_tf = sorted(
        [
            {
                "type": key.type,
                "name": key.name,
                "live": live_comparable[key],
            }
            for key in (live_keys - tf_keys)
        ],
        key=lambda x: (x["type"], x["name"]),
    )

    missing_in_azure = sorted(
        [
            {
                "type": key.type,
                "name": key.name,
                "terraform": tf_comparable[key],
            }
            for key in (tf_keys - live_keys)
        ],
        key=lambda x: (x["type"], x["name"]),
    )

    matched = sorted(tf_keys & live_keys, key=lambda x: (x.type, x.name))
    matched_resources = [
        {
            "type": key.type,
            "name": key.name,
            "terraform": tf_comparable[key],
            "live": live_comparable[key],
        }
        for key in matched
    ]

    report = {
        "scope": {
            "resource_group": live_group.get("name"),
            "comparison_mode": "terraform-managed resources only",
            "terraform_source": str(TF_FILE),
            "live_source": str(LIVE_FILE),
        },
        "summary": {
            "live_total_resources": len(live_resources),
            "live_platform_generated_excluded": len(live_platform_generated),
            "terraform_total_managed_resources": len(tf_resources),
            "terraform_non_comparable_excluded": len(tf_non_comparable),
            "comparable_live_resources": len(live_comparable),
            "comparable_terraform_resources": len(tf_comparable),
            "matched": len(matched_resources),
            "missing_in_tf": len(missing_in_tf),
            "missing_in_azure": len(missing_in_azure),
        },
        "excluded": {
            "platform_generated_live_resources": live_platform_generated,
            "non_comparable_terraform_resources": tf_non_comparable,
        },
        "matched": matched_resources,
        "missing_in_tf": missing_in_tf,
        "missing_in_azure": missing_in_azure,
    }

    return report


def render_markdown(report: Dict) -> str:
    summary = report["summary"]
    lines = [
        "# Terraform ↔ Azure RG Parity Report",
        "",
        f"- Resource Group: `{report['scope']['resource_group']}`",
        f"- Comparison mode: `{report['scope']['comparison_mode']}`",
        "",
        "## Summary",
        "",
        f"- Live total resources: **{summary['live_total_resources']}**",
        f"- Terraform managed resources: **{summary['terraform_total_managed_resources']}**",
        f"- Comparable live resources: **{summary['comparable_live_resources']}**",
        f"- Comparable Terraform resources: **{summary['comparable_terraform_resources']}**",
        f"- Matched: **{summary['matched']}**",
        f"- Missing in Terraform: **{summary['missing_in_tf']}**",
        f"- Missing in Azure: **{summary['missing_in_azure']}**",
        "",
        "## Missing in Terraform",
        "",
    ]

    if report["missing_in_tf"]:
        for item in report["missing_in_tf"]:
            lines.append(f"- {item['type']} :: {item['name']}")
    else:
        lines.append("- None")

    lines.extend(["", "## Missing in Azure", ""])

    if report["missing_in_azure"]:
        for item in report["missing_in_azure"]:
            tf = item["terraform"]
            lines.append(f"- {item['type']} :: {item['name']} (from `{tf['address']}`)")
    else:
        lines.append("- None")

    lines.extend(["", "## Exclusions", ""])
    lines.append(
        f"- Platform-generated live resources excluded: {summary['live_platform_generated_excluded']}"
    )
    lines.append(
        f"- Non-comparable Terraform resources excluded: {summary['terraform_non_comparable_excluded']}"
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_parity_report()
    OUT_JSON.write_text(json.dumps(report, indent=2))
    OUT_MD.write_text(render_markdown(report))
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
