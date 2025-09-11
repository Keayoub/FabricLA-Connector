"""
High-level workflow functions for easy Fabric data collection and ingestion.
This module provides the simplified interface from the notebooks.
"""

from typing import List, Dict, Any, Optional
from azure.identity import DefaultAzureCredential
from .collectors import (
    PipelineDataCollector,
    DatasetRefreshCollector,
    CapacityUtilizationCollector,
    UserActivityCollector,
)
from .ingestion import post_rows_to_dcr, FabricIngestion, post_rows_to_dcr_enhanced, create_troubleshooting_report_legacy
from .config import get_config, get_ingestion_config, get_fabric_config, validate_config
from .api import get_fabric_token

# Import enhanced functions from consolidated utils
from .utils import within_lookback_minutes


def collect_and_ingest_pipeline_data(
    workspace_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect pipeline and dataflow run data and ingest to Log Analytics.

    This function replicates the main workflow from fabric_pipeline_dataflow_collector.ipynb
    """
    print(f"🚀 Starting pipeline data collection for workspace {workspace_id}")

    try:
        # Validate configuration
        config_validation = validate_config("all")
        if not config_validation["valid"]:
            return {
                "status": "error",
                "message": f"Configuration invalid: {config_validation['missing_required']}",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Initialize collector
        collector = PipelineDataCollector(workspace_id, lookback_hours)

        # Collect pipeline runs
        print("[Collector] 📊 Collecting pipeline runs...")
        pipeline_runs = list(collector.collect_pipeline_runs())
        print(f"[Collector] Found {len(pipeline_runs)} pipeline runs")

        # Collect dataflow runs
        print("[Collector] 📊 Collecting dataflow runs...")
        dataflow_runs = list(collector.collect_dataflow_runs())
        print(f"[Collector] Found {len(dataflow_runs)} dataflow runs")

        # Combine all records
        all_records = pipeline_runs + dataflow_runs

        if not all_records:
            print("ℹ️  No records found to ingest")
            return {
                "status": "completed",
                "message": "No records found",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if custom_config:
            ingestion_config.update(custom_config)

        # Ingest records
        print(f"[Ingestion] 📤 Ingesting {len(all_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=all_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config["stream_name"],
        )

        return {
            "status": "completed",
            "collected_count": len(all_records),
            "pipeline_runs": len(pipeline_runs),
            "dataflow_runs": len(dataflow_runs),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"❌ Error in pipeline data collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def collect_and_ingest_dataset_refreshes(
    workspace_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect dataset refresh data and ingest to Log Analytics.

    This function replicates the main workflow from fabric_dataset_refresh_monitoring.ipynb
    """
    print(f"🚀 Starting dataset refresh collection for workspace {workspace_id}")

    try:
        # Validate configuration
        config_validation = validate_config("all")
        if not config_validation["valid"]:
            return {
                "status": "error",
                "message": f"Configuration invalid: {config_validation['missing_required']}",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Initialize collector
        collector = DatasetRefreshCollector(workspace_id, lookback_hours)

        # Collect dataset refreshes
        print("[Collector] 📊 Collecting dataset refreshes...")
        refresh_records = list(collector.collect_dataset_refreshes())
        print(f"[Collector] Found {len(refresh_records)} refresh records")

        # Collect dataset metadata
        print("[Collector] 📊 Collecting dataset metadata...")
        metadata_records = list(collector.collect_dataset_metadata())
        print(f"[Collector] Found {len(metadata_records)} metadata records")

        # Combine all records
        all_records = refresh_records + metadata_records

        if not all_records:
            print("ℹ️  No records found to ingest")
            return {
                "status": "completed",
                "message": "No records found",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if custom_config:
            ingestion_config.update(custom_config)

        # Ingest records
        print(f"[Ingestion] 📤 Ingesting {len(all_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=all_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config["stream_name"],
        )

        return {
            "status": "completed",
            "collected_count": len(all_records),
            "refresh_records": len(refresh_records),
            "metadata_records": len(metadata_records),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"❌ Error in dataset refresh collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def collect_and_ingest_capacity_utilization(
    capacity_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect capacity utilization data and ingest to Log Analytics.

    This function replicates the main workflow from fabric_capacity_utilization_monitoring.ipynb
    """
    print(f"🚀 Starting capacity utilization collection for capacity {capacity_id}")

    try:
        # Validate configuration
        config_validation = validate_config("all")
        if not config_validation["valid"]:
            return {
                "status": "error",
                "message": f"Configuration invalid: {config_validation['missing_required']}",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Initialize collector
        collector = CapacityUtilizationCollector(capacity_id, lookback_hours)

        # Collect capacity metrics
        print("[Collector] 📊 Collecting capacity utilization metrics...")
        capacity_records = list(collector.collect_capacity_metrics())
        print(f"[Collector] Found {len(capacity_records)} capacity records")

        if not capacity_records:
            print("ℹ️  No records found to ingest")
            return {
                "status": "completed",
                "message": "No records found",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if custom_config:
            ingestion_config.update(custom_config)

        # Ingest records
        print(f"[Ingestion] 📤 Ingesting {len(capacity_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=capacity_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config["stream_name"],
        )

        return {
            "status": "completed",
            "collected_count": len(capacity_records),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"❌ Error in capacity utilization collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def collect_and_ingest_user_activity(
    workspace_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect user activity data and ingest to Log Analytics.

    This function replicates the main workflow from fabric_user_activity_monitoring.ipynb
    Requires admin permissions.
    """
    print(f"🚀 Starting user activity collection for workspace {workspace_id}")

    try:
        # Validate configuration
        config_validation = validate_config("all")
        if not config_validation["valid"]:
            return {
                "status": "error",
                "message": f"Configuration invalid: {config_validation['missing_required']}",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Initialize collector
        collector = UserActivityCollector(workspace_id, lookback_hours)

        # Collect user activities
        print("[Collector] 📊 Collecting user activities...")
        activity_records = list(collector.collect_user_activities())
        print(f"[Collector] Found {len(activity_records)} activity records")

        if not activity_records:
            print("ℹ️  No records found to ingest (may require admin permissions)")
            return {
                "status": "completed",
                "message": "No records found",
                "collected_count": 0,
                "ingested_count": 0,
            }

        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if custom_config:
            ingestion_config.update(custom_config)

        # Ingest records
        print(f"[Ingestion] 📤 Ingesting {len(activity_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=activity_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config["stream_name"],
        )

        return {
            "status": "completed",
            "collected_count": len(activity_records),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"❌ Error in user activity collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def collect_and_ingest_pipeline_data_enhanced(
    workspace_id: str,
    pipeline_item_ids: Optional[List[str]] = None,
    lookback_hours: int = 24,
    collect_activity_runs: bool = True,
    enable_troubleshooting: bool = True,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Enhanced pipeline data collection with troubleshooting features from notebook.

    Args:
        workspace_id: Fabric workspace ID
        pipeline_item_ids: List of specific pipeline IDs to collect (None for all)
        lookback_hours: Hours to look back for data
        collect_activity_runs: Whether to collect detailed activity runs
        enable_troubleshooting: Whether to generate troubleshooting report
        custom_config: Optional configuration overrides

    Returns:
        Dict with ingestion results and optional troubleshooting report
    """
    try:
        # Import enhanced functions
        from .utils import within_lookback_minutes, iso_now, chunk_records_by_size

        print(
            f"🚀 Starting enhanced pipeline data collection for workspace {workspace_id}"
        )
        print(f"   Lookback: {lookback_hours} hours")
        print(f"   Activity runs: {'Enabled' if collect_activity_runs else 'Disabled'}")

        # Configuration
        config = get_config()
        if custom_config:
            config.update(custom_config)

        ingestion_config = get_ingestion_config()
        fabric_config = get_fabric_config()

        # Get authentication token
        token = get_fabric_token()

        # Initialize collector
        collector = PipelineDataCollector(workspace_id, lookback_hours)

        # Collect data
        pipeline_runs = []
        activity_runs = []

        if pipeline_item_ids:
            # Note: Current collector doesn't support filtering by specific IDs
            # Collecting all and would need to filter post-collection
            print(
                f"   Note: Collecting all pipelines (filtering by specific IDs not yet implemented)"
            )

        # Collect pipeline runs
        runs = list(collector.collect_pipeline_runs())
        pipeline_runs.extend(runs)

        if collect_activity_runs:
            # For now, activity runs require specific pipeline and run IDs
            # This would need enhancement to the collector to support bulk collection
            print("   Note: Bulk activity run collection not yet implemented")
            # activities = list(collector.collect_activity_runs())
            # activity_runs.extend(activities)

        print(f"   Collected {len(pipeline_runs)} pipeline runs")
        print(f"   Collected {len(activity_runs)} activity runs")

        # Ingest data using enhanced method
        ingestion_summary = {}

        if pipeline_runs:
            print("   Ingesting pipeline runs...")
            credential = DefaultAzureCredential()
            result = post_rows_to_dcr_enhanced(
                records=pipeline_runs,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_id=ingestion_config["dcr_immutable_id"],
                stream_name="pipeline_runs",
                credential=credential,
                troubleshoot=enable_troubleshooting
            )
            ingestion_summary["pipeline_runs"] = result

        if activity_runs:
            print("   Ingesting activity runs...")
            credential = DefaultAzureCredential()
            result = post_rows_to_dcr_enhanced(
                records=activity_runs,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_id=ingestion_config["dcr_immutable_id"],
                stream_name="activity_runs",
                credential=credential,
                troubleshoot=enable_troubleshooting
            )
            ingestion_summary["activity_runs"] = result

        # Create result
        result = {
            "success": True,
            "workspace_id": workspace_id,
            "pipeline_runs_collected": len(pipeline_runs),
            "activity_runs_collected": len(activity_runs),
            "ingestion_summary": ingestion_summary,
            "total_records_ingested": sum(
                r.get("sent", 0) for r in ingestion_summary.values()
            ),
        }

        # Add troubleshooting report if enabled
        if enable_troubleshooting:
            try:
                report = create_troubleshooting_report_legacy(
                    workspace_id=workspace_id,
                    pipeline_rows=pipeline_runs,
                    activity_rows=activity_runs,
                    ingestion_summary=ingestion_summary,
                )
                result["troubleshooting_report"] = report
                print("\n" + report)
            except ImportError:
                result["troubleshooting_note"] = (
                    "Enhanced troubleshooting features not available"
                )
            except Exception as e:
                result["troubleshooting_error"] = f"Failed to generate report: {e}"

        print(f"✅ Enhanced pipeline collection completed successfully")
        return result

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "workspace_id": workspace_id,
            "pipeline_runs_collected": 0,
            "activity_runs_collected": 0,
        }

        if enable_troubleshooting:
            report = create_troubleshooting_report_legacy(
                workspace_id=workspace_id, ingestion_summary={"error": str(e)}
            )
            error_result["troubleshooting_report"] = report
            print("\n" + report)

        print(f"❌ Enhanced pipeline collection failed: {e}")
        return error_result


def validate_and_test_configuration() -> Dict[str, Any]:
    """
    Comprehensive configuration validation based on notebook patterns.
    """
    print("🔧 CONFIGURATION VALIDATION")
    print("=" * 50)

    # Basic configuration validation
    validation = validate_config()

    print(f"Environment: {validation['environment']}")
    print(f"Fabric Available: {validation['fabric_available']}")
    print(f"Valid: {'✅' if validation['valid'] else '❌'}")

    if validation["missing_required"]:
        print(f"\n❌ Missing Required:")
        for item in validation["missing_required"]:
            print(f"   - {item}")

    if validation["missing_optional"]:
        print(f"\n⚠️  Missing Optional:")
        for item in validation["missing_optional"]:
            print(f"   - {item}")

    # Test authentication
    auth_test = {"success": False, "error": None}
    try:
        print(f"\n🔐 Testing Authentication...")
        token = get_fabric_token()
        if token:
            print(f"   ✅ Token acquired: {token[:20]}...")
            auth_test["success"] = True
        else:
            auth_test["error"] = "No token returned"
    except Exception as e:
        auth_test["error"] = str(e)
        print(f"   ❌ Authentication failed: {e}")

    return {
        "validation": validation,
        "authentication_test": auth_test,
        "recommendations": _get_configuration_recommendations(validation, auth_test),
    }


def _get_configuration_recommendations(validation: Dict, auth_test: Dict) -> List[str]:
    """Get configuration recommendations based on validation results"""
    recommendations = []

    if not validation["valid"]:
        recommendations.append("Set missing required environment variables")
        recommendations.append("Check .env file configuration")

    if not auth_test["success"]:
        recommendations.append("Verify service principal permissions")
        recommendations.append("Check if Fabric.ReadAll permission is granted")
        recommendations.append("Ensure admin consent is provided")

    if validation["environment"] == "local":
        recommendations.append("Consider using Fabric workspace identity in production")

    return recommendations


def run_full_monitoring_cycle_enhanced(
    workspace_id: str,
    capacity_id: Optional[str] = None,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Run a complete monitoring cycle collecting all available data types.
    This is the equivalent of running all four notebooks in sequence.
    """
    print("🚀 Starting full monitoring cycle...")
    print("=" * 60)

    results = {
        "pipeline_data": None,
        "dataset_refreshes": None,
        "capacity_utilization": None,
        "user_activity": None,
        "overall_status": "completed",
        "total_collected": 0,
        "total_ingested": 0,
    }

    # 1. Pipeline and Dataflow Data
    print("\n1️⃣ Collecting Pipeline & Dataflow Data")
    try:
        pipeline_result = collect_and_ingest_pipeline_data(
            workspace_id, lookback_hours, custom_config
        )
        results["pipeline_data"] = pipeline_result
        results["total_collected"] += pipeline_result.get("collected_count", 0)
        if "ingestion_result" in pipeline_result:
            results["total_ingested"] += pipeline_result["ingestion_result"].get(
                "ingested_count", 0
            )
    except Exception as e:
        results["pipeline_data"] = {"status": "error", "message": str(e)}
        results["overall_status"] = "partial"

    # 2. Dataset Refresh Data
    print("\n2️⃣ Collecting Dataset Refresh Data")
    try:
        dataset_result = collect_and_ingest_dataset_refreshes(
            workspace_id, lookback_hours, custom_config
        )
        results["dataset_refreshes"] = dataset_result
        results["total_collected"] += dataset_result.get("collected_count", 0)
        if "ingestion_result" in dataset_result:
            results["total_ingested"] += dataset_result["ingestion_result"].get(
                "ingested_count", 0
            )
    except Exception as e:
        results["dataset_refreshes"] = {"status": "error", "message": str(e)}
        results["overall_status"] = "partial"

    # 3. Capacity Utilization (if capacity_id provided)
    if capacity_id:
        print("\n3️⃣ Collecting Capacity Utilization Data")
        try:
            capacity_result = collect_and_ingest_capacity_utilization(
                capacity_id, lookback_hours, custom_config
            )
            results["capacity_utilization"] = capacity_result
            results["total_collected"] += capacity_result.get("collected_count", 0)
            if "ingestion_result" in capacity_result:
                results["total_ingested"] += capacity_result["ingestion_result"].get(
                    "ingested_count", 0
                )
        except Exception as e:
            results["capacity_utilization"] = {"status": "error", "message": str(e)}
            results["overall_status"] = "partial"
    else:
        print("\n3️⃣ Skipping Capacity Utilization (no capacity_id provided)")
        results["capacity_utilization"] = {
            "status": "skipped",
            "message": "No capacity_id provided",
        }

    # 4. User Activity Data
    print("\n4️⃣ Collecting User Activity Data")
    try:
        activity_result = collect_and_ingest_user_activity(
            workspace_id, lookback_hours, custom_config
        )
        results["user_activity"] = activity_result
        results["total_collected"] += activity_result.get("collected_count", 0)
        if "ingestion_result" in activity_result:
            results["total_ingested"] += activity_result["ingestion_result"].get(
                "ingested_count", 0
            )
    except Exception as e:
        results["user_activity"] = {"status": "error", "message": str(e)}
        results["overall_status"] = "partial"

    # Summary
    print("\n" + "=" * 60)
    print("📊 MONITORING CYCLE SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Total Collected: {results['total_collected']} records")
    print(f"Total Ingested: {results['total_ingested']} records")

    for component, result in results.items():
        if (
            component not in ["overall_status", "total_collected", "total_ingested"]
            and result
        ):
            status = result.get("status", "unknown")
            collected = result.get("collected_count", 0)
            print(f"  {component}: {status} ({collected} records)")

    return results


# Convenience functions for notebook compatibility
def main_pipeline_workflow(workspace_id: str, lookback_hours: int = 24):
    """Notebook-compatible main function for pipeline data collection"""
    return collect_and_ingest_pipeline_data(workspace_id, lookback_hours)


def main_dataset_workflow(workspace_id: str, lookback_hours: int = 24):
    """Notebook-compatible main function for dataset refresh collection"""
    return collect_and_ingest_dataset_refreshes(workspace_id, lookback_hours)


def main_capacity_workflow(capacity_id: str, lookback_hours: int = 24):
    """Notebook-compatible main function for capacity utilization collection"""
    return collect_and_ingest_capacity_utilization(capacity_id, lookback_hours)


def main_activity_workflow(workspace_id: str, lookback_hours: int = 24):
    """Notebook-compatible main function for user activity collection"""
    return collect_and_ingest_user_activity(workspace_id, lookback_hours)
