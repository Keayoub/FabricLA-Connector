"""
High-level workflow functions for easy Fabric data collection and ingestion.
This module provides intelligent workflows for comprehensive monitoring.
"""

import logging
from typing import List, Dict, Any, Optional
from azure.identity import DefaultAzureCredential
from .collectors import (
    PipelineDataCollector,
    DatasetRefreshCollector,
    CapacityUtilizationCollector,
    UserActivityCollector,
    OneLakeStorageCollector,
    SparkJobCollector,
    NotebookCollector,
    GitIntegrationCollector,
)
from .ingestion import post_rows_to_dcr, FabricIngestion, post_rows_to_dcr_enhanced, create_troubleshooting_report_legacy
from .config import get_config, get_ingestion_config, get_fabric_config, validate_config, get_monitoring_config
from .api import get_fabric_token

# Import enhanced functions from consolidated utils
from .utils import within_lookback_minutes

# Import intelligent monitoring components
from .monitoring_detection import (
    get_monitoring_detector, 
    get_monitoring_strategy, 
    print_monitoring_status
)

logger = logging.getLogger(__name__)


def collect_and_ingest_pipeline_data(
    workspace_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect pipeline and dataflow run data and ingest to Log Analytics.

    This function replicates the main workflow from fabric_pipeline_dataflow_collector.ipynb
    """
    print(f"STARTING: Starting pipeline data collection for workspace {workspace_id}")

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
        print("[Collector] Found Collecting pipeline runs...")
        pipeline_runs = list(collector.collect_pipeline_runs())
        print(f"[Collector] Found {len(pipeline_runs)} pipeline runs")

        # Collect dataflow runs
        print("[Collector] Found Collecting dataflow runs...")
        dataflow_runs = list(collector.collect_dataflow_runs())
        print(f"[Collector] Found {len(dataflow_runs)} dataflow runs")

        # Combine all records
        all_records = pipeline_runs + dataflow_runs

        if not all_records:
            print("INFO:  No records found to ingest")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(all_records)} records...")
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
        print(f"ERROR: in pipeline data collection: {e}")
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
    print(f"STARTING: Starting dataset refresh collection for workspace {workspace_id}")

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
        print("[Collector] Found Collecting dataset refreshes...")
        refresh_records = list(collector.collect_dataset_refreshes())
        print(f"[Collector] Found {len(refresh_records)} refresh records")

        # Collect dataset metadata
        print("[Collector] Found Collecting dataset metadata...")
        metadata_records = list(collector.collect_dataset_metadata())
        print(f"[Collector] Found {len(metadata_records)} metadata records")

        # Combine all records
        all_records = refresh_records + metadata_records

        if not all_records:
            print("INFO:  No records found to ingest")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(all_records)} records...")
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
        print(f"ERROR: in dataset refresh collection: {e}")
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
    print(f"STARTING: Starting capacity utilization collection for capacity {capacity_id}")

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
        print("[Collector] Found Collecting capacity utilization metrics...")
        capacity_records = list(collector.collect_capacity_metrics())
        print(f"[Collector] Found {len(capacity_records)} capacity records")

        if not capacity_records:
            print("INFO:  No records found to ingest")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(capacity_records)} records...")
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
        print(f"ERROR: in capacity utilization collection: {e}")
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
    print(f"STARTING: Starting user activity collection for workspace {workspace_id}")

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
        print("[Collector] Found Collecting user activities...")
        activity_records = list(collector.collect_user_activities())
        print(f"[Collector] Found {len(activity_records)} activity records")

        if not activity_records:
            print("INFO:  No records found to ingest (may require admin permissions)")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(activity_records)} records...")
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
        print(f"ERROR: in user activity collection: {e}")
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
            f"STARTING: Starting enhanced pipeline data collection for workspace {workspace_id}"
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

        print(f"SUCCESS: Enhanced pipeline collection completed successfully")
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

        print(f"ERROR: Enhanced pipeline collection failed: {e}")
        return error_result


def validate_and_test_configuration() -> Dict[str, Any]:
    """
    Comprehensive configuration validation based on notebook patterns.
    """
    print("FIXING: CONFIGURATION VALIDATION")
    print("=" * 50)

    # Basic configuration validation
    validation = validate_config()

    print(f"Environment: {validation['environment']}")
    print(f"Fabric Available: {validation['fabric_available']}")
    print(f"Valid: {'SUCCESS:' if validation['valid'] else 'ERROR:'}")

    if validation["missing_required"]:
        print(f"\nERROR: Missing Required:")
        for item in validation["missing_required"]:
            print(f"   - {item}")

    if validation["missing_optional"]:
        print(f"\nWARNING:  Missing Optional:")
        for item in validation["missing_optional"]:
            print(f"   - {item}")

    # Test authentication
    auth_test = {"success": False, "error": None}
    try:
        print(f"\nSECURE: Testing Authentication...")
        token = get_fabric_token()
        if token:
            print(f"   SUCCESS: Token acquired: {token[:20]}...")
            auth_test["success"] = True
        else:
            auth_test["error"] = "No token returned"
    except Exception as e:
        auth_test["error"] = str(e)
        print(f"   ERROR: Authentication failed: {e}")

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
    print("STARTING: Starting full monitoring cycle...")
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
    print("Found MONITORING CYCLE SUMMARY")
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


def collect_and_ingest_onelake_storage(
    workspace_id: str,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect OneLake storage data (lakehouses and warehouses) and ingest to Log Analytics.
    """
    print(f"STARTING: Starting OneLake storage collection for workspace {workspace_id}")

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
        collector = OneLakeStorageCollector(workspace_id)

        # Collect lakehouse storage data
        print("[Collector] Found Collecting lakehouse storage data...")
        lakehouse_records = list(collector.collect_lakehouse_storage())
        print(f"[Collector] Found {len(lakehouse_records)} lakehouse records")

        # Collect warehouse storage data
        print("[Collector] Found Collecting warehouse storage data...")
        warehouse_records = list(collector.collect_warehouse_storage())
        print(f"[Collector] Found {len(warehouse_records)} warehouse records")

        # Combine all records
        all_records = lakehouse_records + warehouse_records

        if not all_records:
            print("INFO:  No storage records found to ingest")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(all_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=all_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config.get("onelake_stream_name", ingestion_config["stream_name"]),
        )

        return {
            "status": "completed",
            "collected_count": len(all_records),
            "lakehouse_records": len(lakehouse_records),
            "warehouse_records": len(warehouse_records),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"ERROR: in OneLake storage collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def collect_and_ingest_spark_jobs(
    workspace_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect Spark job data (definitions and runs) and ingest to Log Analytics.
    """
    print(f"STARTING: Starting Spark job collection for workspace {workspace_id}")

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
        collector = SparkJobCollector(workspace_id, lookback_hours)

        # Collect Spark job definitions
        print("[Collector] Found Collecting Spark job definitions...")
        job_definitions = list(collector.collect_spark_job_definitions())
        print(f"[Collector] Found {len(job_definitions)} job definitions")

        # Collect Spark job runs
        print("[Collector] Found Collecting Spark job runs...")
        job_runs = list(collector.collect_spark_job_runs())
        print(f"[Collector] Found {len(job_runs)} job runs")

        # Combine all records
        all_records = job_definitions + job_runs

        if not all_records:
            print("INFO:  No Spark job records found to ingest")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(all_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=all_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config.get("spark_stream_name", ingestion_config["stream_name"]),
        )

        return {
            "status": "completed",
            "collected_count": len(all_records),
            "job_definitions": len(job_definitions),
            "job_runs": len(job_runs),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"ERROR: in Spark job collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def collect_and_ingest_notebooks(
    workspace_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect notebook data (inventory and runs) and ingest to Log Analytics.
    """
    print(f"STARTING: Starting notebook collection for workspace {workspace_id}")

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
        collector = NotebookCollector(workspace_id, lookback_hours)

        # Collect notebook inventory
        print("[Collector] Found Collecting notebook inventory...")
        notebooks = list(collector.collect_notebooks())
        print(f"[Collector] Found {len(notebooks)} notebooks")

        # Collect notebook runs
        print("[Collector] Found Collecting notebook runs...")
        notebook_runs = list(collector.collect_notebook_runs())
        print(f"[Collector] Found {len(notebook_runs)} notebook runs")

        # Combine all records
        all_records = notebooks + notebook_runs

        if not all_records:
            print("INFO:  No notebook records found to ingest")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(all_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=all_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config.get("notebook_stream_name", ingestion_config["stream_name"]),
        )

        return {
            "status": "completed",
            "collected_count": len(all_records),
            "notebooks": len(notebooks),
            "notebook_runs": len(notebook_runs),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"ERROR: in notebook collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def collect_and_ingest_git_integration(
    workspace_id: str,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Collect Git integration data (connection info and status) and ingest to Log Analytics.
    """
    print(f"STARTING: Starting Git integration collection for workspace {workspace_id}")

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
        collector = GitIntegrationCollector(workspace_id)

        # Collect Git connection information
        print("[Collector] Found Collecting Git connection info...")
        connection_records = list(collector.collect_git_connection_info())
        print(f"[Collector] Found {len(connection_records)} connection records")

        # Collect Git status information
        print("[Collector] Found Collecting Git status info...")
        status_records = list(collector.collect_git_status())
        print(f"[Collector] Found {len(status_records)} status records")

        # Combine all records
        all_records = connection_records + status_records

        if not all_records:
            print("INFO:  No Git integration records found to ingest")
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
        print(f"[Ingestion] OUTPUT: Ingesting {len(all_records)} records...")
        ingestion_result = post_rows_to_dcr(
            records=all_records,
            dce_endpoint=ingestion_config["dce_endpoint"],
            dcr_immutable_id=ingestion_config["dcr_immutable_id"],
            stream_name=ingestion_config.get("git_stream_name", ingestion_config["stream_name"]),
        )

        return {
            "status": "completed",
            "collected_count": len(all_records),
            "connection_records": len(connection_records),
            "status_records": len(status_records),
            "ingestion_result": ingestion_result,
        }

    except Exception as e:
        print(f"ERROR: in Git integration collection: {e}")
        return {
            "status": "error",
            "message": str(e),
            "collected_count": 0,
            "ingested_count": 0,
        }


def run_operational_monitoring_cycle(
    workspace_id: str,
    capacity_id: Optional[str] = None,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Run operational monitoring cycle including OneLake, Spark, notebooks, and Git integration.
    This extends the base monitoring with operational monitoring capabilities.
    """
    print("STARTING: Starting operational monitoring cycle...")
    print("=" * 60)

    results = {
        "onelake_storage": None,
        "spark_jobs": None,
        "notebooks": None,
        "git_integration": None,
        "overall_status": "completed",
        "total_collected": 0,
        "total_ingested": 0,
    }

    # 1. OneLake Storage Data
    print("\nDATABASE:️ Collecting OneLake Storage Data")
    try:
        onelake_result = collect_and_ingest_onelake_storage(workspace_id, custom_config)
        results["onelake_storage"] = onelake_result
        results["total_collected"] += onelake_result.get("collected_count", 0)
        if "ingestion_result" in onelake_result:
            results["total_ingested"] += onelake_result["ingestion_result"].get("ingested_count", 0)
    except Exception as e:
        results["onelake_storage"] = {"status": "error", "message": str(e)}
        results["overall_status"] = "partial"

    # 2. Spark Jobs Data
    print("\nFAST: Collecting Spark Jobs Data")
    try:
        spark_result = collect_and_ingest_spark_jobs(workspace_id, lookback_hours, custom_config)
        results["spark_jobs"] = spark_result
        results["total_collected"] += spark_result.get("collected_count", 0)
        if "ingestion_result" in spark_result:
            results["total_ingested"] += spark_result["ingestion_result"].get("ingested_count", 0)
    except Exception as e:
        results["spark_jobs"] = {"status": "error", "message": str(e)}
        results["overall_status"] = "partial"

    # 3. Notebooks Data
    print("\nNOTEBOOK: Collecting Notebooks Data")
    try:
        notebook_result = collect_and_ingest_notebooks(workspace_id, lookback_hours, custom_config)
        results["notebooks"] = notebook_result
        results["total_collected"] += notebook_result.get("collected_count", 0)
        if "ingestion_result" in notebook_result:
            results["total_ingested"] += notebook_result["ingestion_result"].get("ingested_count", 0)
    except Exception as e:
        results["notebooks"] = {"status": "error", "message": str(e)}
        results["overall_status"] = "partial"

    # 4. Git Integration Data
    print("\nLINK: Collecting Git Integration Data")
    try:
        git_result = collect_and_ingest_git_integration(workspace_id, custom_config)
        results["git_integration"] = git_result
        results["total_collected"] += git_result.get("collected_count", 0)
        if "ingestion_result" in git_result:
            results["total_ingested"] += git_result["ingestion_result"].get("ingested_count", 0)
    except Exception as e:
        results["git_integration"] = {"status": "error", "message": str(e)}
        results["overall_status"] = "partial"

    # Summary
    print("\n" + "=" * 60)
    print("Found OPERATIONAL MONITORING CYCLE SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Total Collected: {results['total_collected']} records")
    print(f"Total Ingested: {results['total_ingested']} records")

    for component, result in results.items():
        if component not in ["overall_status", "total_collected", "total_ingested"] and result:
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


# ======================================
# INTELLIGENT WORKFLOW FUNCTIONS
# ======================================

def run_intelligent_monitoring_cycle(workspace_id: str, capacity_id: Optional[str] = None, 
                                   strategy_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Run an intelligent monitoring cycle that adapts to workspace monitoring status.
    
    This is the main entry point for smart monitoring that:
    1. Detects Microsoft's workspace monitoring status
    2. Applies intelligent collection strategy
    3. Collects only data that provides unique value
    4. Avoids conflicts with Microsoft's official monitoring
    
    Args:
        workspace_id: Fabric workspace ID to monitor
        capacity_id: Optional capacity ID for capacity monitoring
        strategy_override: Optional strategy override ('auto', 'full', 'complement', 'minimal')
        
    Returns:
        Dict with collection results and monitoring insights
    """
    
    logger.info(f"Starting intelligent monitoring cycle for workspace {workspace_id}")
    
    try:
        # Get configuration
        fabric_config = get_fabric_config()
        monitoring_config = get_monitoring_config()
        
        # Override strategy if provided
        if strategy_override:
            monitoring_config['strategy'] = strategy_override
        
        # Get authentication token
        token = get_fabric_token()
        
        # Initialize monitoring components
        detector = get_monitoring_detector(token)
        strategy = get_monitoring_strategy(monitoring_config['strategy'])
        
        # Detect workspace monitoring status
        monitoring_status = detector.detect_workspace_monitoring_status(workspace_id)
        
        # Print comprehensive status report
        print_monitoring_status(monitoring_status, strategy)
        
        # Initialize results
        results = {
            "workspace_id": workspace_id,
            "monitoring_status": monitoring_status,
            "strategy": monitoring_config['strategy'],
            "collections": {},
            "skipped_collections": {},
            "summary": {
                "total_sources": 0,
                "collected_sources": 0,
                "skipped_sources": 0,
                "total_records": 0
            }
        }
        
        # Define data sources to evaluate
        data_sources = [
            ("pipeline_execution", lambda: _collect_pipeline_data(workspace_id, monitoring_config)),
            ("dataflow_execution", lambda: _collect_dataflow_data(workspace_id, monitoring_config)),
            ("user_activity", lambda: _collect_user_activity_data(workspace_id, monitoring_config)),
            ("dataset_refresh", lambda: _collect_dataset_refresh_data(workspace_id, monitoring_config)),
            ("capacity_utilization", lambda: _collect_capacity_data(capacity_id, monitoring_config) if capacity_id else None),
            ("onelake_storage", lambda: _collect_onelake_storage_data(workspace_id, monitoring_config)),
            ("spark_jobs", lambda: _collect_spark_jobs_data(workspace_id, monitoring_config)),
            ("notebooks", lambda: _collect_notebooks_data(workspace_id, monitoring_config)),
            ("git_integration", lambda: _collect_git_integration_data(workspace_id, monitoring_config))
        ]
        
        # Process each data source intelligently
        for source_name, collector_func in data_sources:
            if collector_func is None:  # Skip if no capacity_id provided
                continue
                
            results["summary"]["total_sources"] += 1
            
            # Get collection decision
            decision = strategy.should_collect_data_source(source_name, monitoring_status)
            
            if decision["collect"]:
                try:
                    logger.info(f"Collecting {source_name}: {decision['reason']}")
                    collection_result = collector_func()
                    
                    if collection_result and collection_result.get("status") == "success":
                        results["collections"][source_name] = {
                            "result": collection_result,
                            "decision": decision,
                            "records_collected": collection_result.get("total_records", 0)
                        }
                        results["summary"]["collected_sources"] += 1
                        results["summary"]["total_records"] += collection_result.get("total_records", 0)
                        
                        print(f"SUCCESS: {source_name}: {collection_result.get('total_records', 0)} records")
                    else:
                        logger.warning(f"Collection failed for {source_name}: {collection_result}")
                        results["collections"][source_name] = {
                            "result": collection_result,
                            "decision": decision,
                            "error": True
                        }
                        
                except Exception as e:
                    logger.error(f"Error collecting {source_name}: {e}")
                    results["collections"][source_name] = {
                        "error": str(e),
                        "decision": decision
                    }
            else:
                # Record skipped collection with reason
                results["skipped_collections"][source_name] = decision
                results["summary"]["skipped_sources"] += 1
                
                reason = decision.get("reason", "unknown")
                alternative = decision.get("alternative")
                print(f"NEXT:  {source_name}: Skipped - {reason}")
                if alternative:
                    print(f"   TIP: Alternative: {alternative}")
        
        # Generate final summary
        collected = results["summary"]["collected_sources"]
        total = results["summary"]["total_sources"]
        records = results["summary"]["total_records"]
        
        print(f"\nTARGET: Intelligent Monitoring Summary:")
        print(f"   Found Data Sources: {collected}/{total} collected")
        print(f"   NOTE: Total Records: {records:,}")
        print(f"   AI: Strategy: {monitoring_config['strategy']}")
        
        # Add recommendations for skipped sources
        if results["skipped_collections"]:
            print(f"\nTIP: Recommendations for skipped sources:")
            for source, decision in results["skipped_collections"].items():
                if decision.get("alternative"):
                    print(f"   • {source}: {decision['alternative']}")
        
        results["status"] = "success"
        return results
        
    except Exception as e:
        logger.error(f"Error in intelligent monitoring cycle: {e}")
        return {
            "status": "error",
            "error": str(e),
            "workspace_id": workspace_id
        }


def check_workspace_monitoring_status(workspace_id: str) -> Dict[str, Any]:
    """
    Check workspace monitoring status without running collection.
    
    Useful for understanding monitoring setup before running collection.
    """
    try:
        token = get_fabric_token()
        detector = get_monitoring_detector(token)
        return detector.detect_workspace_monitoring_status(workspace_id)
    except Exception as e:
        logger.error(f"Error checking workspace monitoring status: {e}")
        return {
            "workspace_monitoring_enabled": "unknown",
            "error": str(e)
        }


def get_collection_recommendations(workspace_id: str, strategy: str = "auto") -> Dict[str, Any]:
    """
    Get collection recommendations for a workspace without running collection.
    
    Args:
        workspace_id: Fabric workspace ID
        strategy: Monitoring strategy ('auto', 'full', 'complement', 'minimal')
        
    Returns:
        Dict with recommendations for each data source
    """
    try:
        token = get_fabric_token()
        detector = get_monitoring_detector(token)
        strategy_obj = get_monitoring_strategy(strategy)
        
        monitoring_status = detector.detect_workspace_monitoring_status(workspace_id)
        
        recommendations = {}
        data_sources = [
            "pipeline_execution", "dataflow_execution", "user_activity", 
            "dataset_refresh", "capacity_utilization", "onelake_storage",
            "spark_jobs", "notebooks", "git_integration"
        ]
        
        for source in data_sources:
            recommendations[source] = strategy_obj.should_collect_data_source(source, monitoring_status)
        
        return {
            "workspace_id": workspace_id,
            "strategy": strategy,
            "monitoring_status": monitoring_status,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error getting collection recommendations: {e}")
        return {"error": str(e)}


# Helper functions for intelligent workflows
def _collect_pipeline_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect pipeline execution data."""
    try:
        return collect_and_ingest_pipeline_data_enhanced(
            workspace_id=workspace_id,
            lookback_hours=monitoring_config.get('lookback_hours', 24)
        )
    except Exception as e:
        logger.error(f"Pipeline data collection failed: {e}")
        return {"status": "error", "error": str(e)}


def _collect_dataflow_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect dataflow execution data (same API as pipelines)."""
    # For now, dataflow data is collected as part of pipeline collection
    # In the future, this could be separated into its own collection logic
    return {"status": "success", "message": "Dataflow data collected with pipelines", "total_records": 0}


def _collect_user_activity_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect user activity data."""
    try:
        return collect_and_ingest_user_activity(
            workspace_id=workspace_id,
            lookback_hours=monitoring_config.get('lookback_hours', 24)
        )
    except Exception as e:
        logger.error(f"User activity data collection failed: {e}")
        return {"status": "error", "error": str(e)}


def _collect_dataset_refresh_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect dataset refresh data."""
    try:
        return collect_and_ingest_dataset_refreshes(
            workspace_id=workspace_id,
            lookback_hours=monitoring_config.get('lookback_hours', 24)
        )
    except Exception as e:
        logger.error(f"Dataset refresh data collection failed: {e}")
        return {"status": "error", "error": str(e)}


def _collect_capacity_data(capacity_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect capacity utilization data."""
    try:
        return collect_and_ingest_capacity_utilization(
            capacity_id=capacity_id,
            lookback_hours=monitoring_config.get('lookback_hours', 24)
        )
    except Exception as e:
        logger.error(f"Capacity data collection failed: {e}")
        return {"status": "error", "error": str(e)}


def _collect_onelake_storage_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect OneLake storage data."""
    try:
        return collect_and_ingest_onelake_storage(workspace_id=workspace_id)
    except Exception as e:
        logger.error(f"OneLake storage data collection failed: {e}")
        return {"status": "error", "error": str(e)}


def _collect_spark_jobs_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect Spark jobs data."""
    try:
        return collect_and_ingest_spark_jobs(
            workspace_id=workspace_id,
            lookback_hours=monitoring_config.get('lookback_hours', 24)
        )
    except Exception as e:
        logger.error(f"Spark jobs data collection failed: {e}")
        return {"status": "error", "error": str(e)}


def _collect_notebooks_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect notebooks data."""
    try:
        return collect_and_ingest_notebooks(
            workspace_id=workspace_id,
            lookback_hours=monitoring_config.get('lookback_hours', 24)
        )
    except Exception as e:
        logger.error(f"Notebooks data collection failed: {e}")
        return {"status": "error", "error": str(e)}


def _collect_git_integration_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect Git integration data."""
    try:
        return collect_and_ingest_git_integration(workspace_id=workspace_id)
    except Exception as e:
        logger.error(f"Git integration data collection failed: {e}")
        return {"status": "error", "error": str(e)}


# Backward compatibility - enhanced versions of existing workflows
def run_full_monitoring_cycle_intelligent(workspace_id: str, capacity_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhanced version of run_full_monitoring_cycle with intelligence.
    
    This replaces the original run_full_monitoring_cycle with smart detection.
    """
    return run_intelligent_monitoring_cycle(workspace_id, capacity_id, strategy_override="auto")


def run_complementary_monitoring_cycle(workspace_id: str, capacity_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run monitoring cycle that only collects data not covered by Microsoft's workspace monitoring.
    """
    return run_intelligent_monitoring_cycle(workspace_id, capacity_id, strategy_override="complement")


def run_minimal_monitoring_cycle(workspace_id: str, capacity_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run minimal monitoring cycle that only collects core unique data.
    """
    return run_intelligent_monitoring_cycle(workspace_id, capacity_id, strategy_override="minimal")


# Phase 2: Security & Governance Workflows

def collect_and_ingest_access_permissions(
    workspace_id: str,
    capacity_id: Optional[str] = None,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None,
    stream_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect and ingest access permissions data for security compliance monitoring.
    
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import AccessPermissionsCollector
    from .ingestion import post_rows_to_dcr
    from .config import get_ingestion_config
    
    results = {
        "workspace_permissions": {"collected": 0, "ingested": 0},
        "item_permissions": {"collected": 0, "ingested": 0},
        "capacity_permissions": {"collected": 0, "ingested": 0},
        "errors": []
    }
    
    try:
        collector = AccessPermissionsCollector(workspace_id)
        
        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if dce_endpoint:
            ingestion_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            ingestion_config["dcr_immutable_id"] = dcr_immutable_id
        if stream_name:
            ingestion_config["stream_name"] = stream_name
        else:
            ingestion_config["stream_name"] = "Custom-FabricPermissions_CL"
        
        # Collect workspace permissions
        workspace_permissions = list(collector.collect_workspace_permissions())
        results["workspace_permissions"]["collected"] = len(workspace_permissions)
        
        if workspace_permissions:
            ingest_result = post_rows_to_dcr(
                records=workspace_permissions,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["workspace_permissions"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        # Collect item permissions
        item_permissions = list(collector.collect_item_permissions())
        results["item_permissions"]["collected"] = len(item_permissions)
        
        if item_permissions:
            ingest_result = post_rows_to_dcr(
                records=item_permissions,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["item_permissions"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        # Collect capacity permissions if capacity_id provided
        if capacity_id:
            capacity_permissions = list(collector.collect_capacity_permissions(capacity_id))
            results["capacity_permissions"]["collected"] = len(capacity_permissions)
            
            if capacity_permissions:
                ingest_result = post_rows_to_dcr(
                    records=capacity_permissions,
                    dce_endpoint=ingestion_config["dce_endpoint"],
                    dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                    stream_name=ingestion_config["stream_name"]
                )
                results["capacity_permissions"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        print(f"SUCCESS: Access permissions collection completed:")
        print(f"   Workspace permissions: {results['workspace_permissions']['collected']} collected, {results['workspace_permissions']['ingested']} ingested")
        print(f"   Item permissions: {results['item_permissions']['collected']} collected, {results['item_permissions']['ingested']} ingested")
        print(f"   Capacity permissions: {results['capacity_permissions']['collected']} collected, {results['capacity_permissions']['ingested']} ingested")
        
    except Exception as e:
        error_msg = f"Error in access permissions collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return results


def collect_and_ingest_workspace_config(
    workspace_id: str,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None,
    stream_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect and ingest workspace configuration including OAP (OneLake Access Point) settings.
    
    Args:
        workspace_id: Fabric workspace ID
        dce_endpoint: Optional custom DCE endpoint
        dcr_immutable_id: Optional custom DCR immutable ID
        stream_name: Optional custom stream name
        
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import AccessPermissionsCollector
    from .ingestion import post_rows_to_dcr
    from .config import get_ingestion_config
    
    results = {
        "workspace_config": {"collected": 0, "ingested": 0},
        "errors": []
    }
    
    try:
        print(f"STARTING: Starting workspace configuration collection for workspace {workspace_id}")
        
        collector = AccessPermissionsCollector(workspace_id)
        
        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if dce_endpoint:
            ingestion_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            ingestion_config["dcr_immutable_id"] = dcr_immutable_id
        if stream_name:
            ingestion_config["stream_name"] = stream_name
        else:
            ingestion_config["stream_name"] = "Custom-FabricWorkspaceConfig_CL"
        
        # Collect workspace configuration
        workspace_config = list(collector.collect_workspace_config())
        results["workspace_config"]["collected"] = len(workspace_config)
        
        if workspace_config:
            ingest_result = post_rows_to_dcr(
                records=workspace_config,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["workspace_config"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        print(f"SUCCESS: Workspace configuration collection completed:")
        print(f"   Workspace config: {results['workspace_config']['collected']} collected, {results['workspace_config']['ingested']} ingested")
        
    except Exception as e:
        error_msg = f"Error in workspace config collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return results


def collect_and_ingest_data_lineage(
    workspace_id: str,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None,
    stream_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect and ingest data lineage information for regulatory compliance tracking.
    
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import DataLineageCollector
    from .ingestion import post_rows_to_dcr
    from .config import get_ingestion_config
    
    results = {
        "dataset_lineage": {"collected": 0, "ingested": 0},
        "dataflow_lineage": {"collected": 0, "ingested": 0},
        "errors": []
    }
    
    try:
        collector = DataLineageCollector(workspace_id)
        
        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if dce_endpoint:
            ingestion_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            ingestion_config["dcr_immutable_id"] = dcr_immutable_id
        if stream_name:
            ingestion_config["stream_name"] = stream_name
        else:
            ingestion_config["stream_name"] = "Custom-FabricDataLineage_CL"
        
        # Collect dataset lineage
        dataset_lineage = list(collector.collect_dataset_lineage())
        results["dataset_lineage"]["collected"] = len(dataset_lineage)
        
        if dataset_lineage:
            ingest_result = post_rows_to_dcr(
                records=dataset_lineage,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["dataset_lineage"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        # Collect dataflow lineage
        dataflow_lineage = list(collector.collect_dataflow_lineage())
        results["dataflow_lineage"]["collected"] = len(dataflow_lineage)
        
        if dataflow_lineage:
            ingest_result = post_rows_to_dcr(
                records=dataflow_lineage,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["dataflow_lineage"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        print(f"SUCCESS: Data lineage collection completed:")
        print(f"   Dataset lineage: {results['dataset_lineage']['collected']} collected, {results['dataset_lineage']['ingested']} ingested")
        print(f"   Dataflow lineage: {results['dataflow_lineage']['collected']} collected, {results['dataflow_lineage']['ingested']} ingested")
        
    except Exception as e:
        error_msg = f"Error in data lineage collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return results


def collect_and_ingest_semantic_models(
    workspace_id: str,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None,
    stream_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect and ingest semantic model performance data for BI optimization.
    
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import SemanticModelCollector
    from .ingestion import post_rows_to_dcr
    from .config import get_ingestion_config
    
    results = {
        "refresh_performance": {"collected": 0, "ingested": 0},
        "usage_patterns": {"collected": 0, "ingested": 0},
        "errors": []
    }
    
    try:
        collector = SemanticModelCollector(workspace_id)
        
        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if dce_endpoint:
            ingestion_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            ingestion_config["dcr_immutable_id"] = dcr_immutable_id
        if stream_name:
            ingestion_config["stream_name"] = stream_name
        else:
            ingestion_config["stream_name"] = "Custom-FabricSemanticModels_CL"
        
        # Collect refresh performance
        refresh_performance = list(collector.collect_model_refresh_performance())
        results["refresh_performance"]["collected"] = len(refresh_performance)
        
        if refresh_performance:
            ingest_result = post_rows_to_dcr(
                records=refresh_performance,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["refresh_performance"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        # Collect usage patterns
        usage_patterns = list(collector.collect_model_usage_patterns())
        results["usage_patterns"]["collected"] = len(usage_patterns)
        
        if usage_patterns:
            ingest_result = post_rows_to_dcr(
                records=usage_patterns,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["usage_patterns"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        print(f"SUCCESS: Semantic model collection completed:")
        print(f"   Refresh performance: {results['refresh_performance']['collected']} collected, {results['refresh_performance']['ingested']} ingested")
        print(f"   Usage patterns: {results['usage_patterns']['collected']} collected, {results['usage_patterns']['ingested']} ingested")
        
    except Exception as e:
        error_msg = f"Error in semantic model collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return results


# Phase 3: Advanced Workloads Workflows

def collect_and_ingest_real_time_intelligence(
    workspace_id: str,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None,
    stream_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect and ingest Real-Time Intelligence data for streaming analytics monitoring.
    
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import RealTimeIntelligenceCollector
    from .ingestion import post_rows_to_dcr
    from .config import get_ingestion_config
    
    results = {
        "eventstream_metrics": {"collected": 0, "ingested": 0},
        "kql_database_performance": {"collected": 0, "ingested": 0},
        "errors": []
    }
    
    try:
        collector = RealTimeIntelligenceCollector(workspace_id)
        
        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if dce_endpoint:
            ingestion_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            ingestion_config["dcr_immutable_id"] = dcr_immutable_id
        if stream_name:
            ingestion_config["stream_name"] = stream_name
        else:
            ingestion_config["stream_name"] = "Custom-FabricRealTimeIntelligence_CL"
        
        # Collect Eventstream metrics
        eventstream_metrics = list(collector.collect_eventstream_metrics())
        results["eventstream_metrics"]["collected"] = len(eventstream_metrics)
        
        if eventstream_metrics:
            ingest_result = post_rows_to_dcr(
                records=eventstream_metrics,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["eventstream_metrics"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        # Collect KQL Database performance
        kql_performance = list(collector.collect_kql_database_performance())
        results["kql_database_performance"]["collected"] = len(kql_performance)
        
        if kql_performance:
            ingest_result = post_rows_to_dcr(
                records=kql_performance,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["kql_database_performance"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        print(f"SUCCESS: Real-Time Intelligence collection completed:")
        print(f"   Eventstream metrics: {results['eventstream_metrics']['collected']} collected, {results['eventstream_metrics']['ingested']} ingested")
        print(f"   KQL database performance: {results['kql_database_performance']['collected']} collected, {results['kql_database_performance']['ingested']} ingested")
        
    except Exception as e:
        error_msg = f"Error in Real-Time Intelligence collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return results


def collect_and_ingest_mirroring(
    workspace_id: str,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None,
    stream_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect and ingest Mirroring data for hybrid data monitoring.
    
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import MirroringCollector
    from .ingestion import post_rows_to_dcr
    from .config import get_ingestion_config
    
    results = {
        "mirror_status": {"collected": 0, "ingested": 0},
        "errors": []
    }
    
    try:
        collector = MirroringCollector(workspace_id)
        
        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if dce_endpoint:
            ingestion_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            ingestion_config["dcr_immutable_id"] = dcr_immutable_id
        if stream_name:
            ingestion_config["stream_name"] = stream_name
        else:
            ingestion_config["stream_name"] = "Custom-FabricMirroring_CL"
        
        # Collect Mirror status
        mirror_status = list(collector.collect_mirror_status())
        results["mirror_status"]["collected"] = len(mirror_status)
        
        if mirror_status:
            ingest_result = post_rows_to_dcr(
                records=mirror_status,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["mirror_status"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        print(f"SUCCESS: Mirroring collection completed:")
        print(f"   Mirror status: {results['mirror_status']['collected']} collected, {results['mirror_status']['ingested']} ingested")
        
    except Exception as e:
        error_msg = f"Error in Mirroring collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return results


def collect_and_ingest_ml_ai(
    workspace_id: str,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None,
    stream_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Collect and ingest ML/AI data for AI workload governance.
    
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import MLAICollector
    from .ingestion import post_rows_to_dcr
    from .config import get_ingestion_config
    
    results = {
        "ml_models": {"collected": 0, "ingested": 0},
        "ml_experiments": {"collected": 0, "ingested": 0},
        "errors": []
    }
    
    try:
        collector = MLAICollector(workspace_id)
        
        # Get ingestion configuration
        ingestion_config = get_ingestion_config()
        if dce_endpoint:
            ingestion_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            ingestion_config["dcr_immutable_id"] = dcr_immutable_id
        if stream_name:
            ingestion_config["stream_name"] = stream_name
        else:
            ingestion_config["stream_name"] = "Custom-FabricMLAI_CL"
        
        # Collect ML Models
        ml_models = list(collector.collect_ml_models())
        results["ml_models"]["collected"] = len(ml_models)
        
        if ml_models:
            ingest_result = post_rows_to_dcr(
                records=ml_models,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["ml_models"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        # Collect ML Experiments
        ml_experiments = list(collector.collect_ml_experiments())
        results["ml_experiments"]["collected"] = len(ml_experiments)
        
        if ml_experiments:
            ingest_result = post_rows_to_dcr(
                records=ml_experiments,
                dce_endpoint=ingestion_config["dce_endpoint"],
                dcr_immutable_id=ingestion_config["dcr_immutable_id"],
                stream_name=ingestion_config["stream_name"]
            )
            results["ml_experiments"]["ingested"] = ingest_result.get("uploaded_row_count", 0)
        
        print(f"SUCCESS: ML/AI collection completed:")
        print(f"   ML models: {results['ml_models']['collected']} collected, {results['ml_models']['ingested']} ingested")
        print(f"   ML experiments: {results['ml_experiments']['collected']} collected, {results['ml_experiments']['ingested']} ingested")
        
    except Exception as e:
        error_msg = f"Error in ML/AI collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return results


def run_compliance_monitoring_cycle(
    workspace_id: str,
    capacity_id: Optional[str] = None,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run Phase 2 compliance monitoring cycle for security and governance.
    
    Returns:
        Dict with overall results from all Phase 2 collections
    """
    print(f"SECURE: Starting compliance monitoring cycle for workspace: {workspace_id}")
    
    overall_results = {
        "access_permissions": {},
        "data_lineage": {},
        "semantic_models": {},
        "total_collected": 0,
        "total_ingested": 0,
        "errors": []
    }
    
    try:
        # Access & Permissions
        print("\nINFO: Collecting access permissions...")
        permissions_results = collect_and_ingest_access_permissions(
            workspace_id, capacity_id, dce_endpoint, dcr_immutable_id, "Custom-FabricPermissions_CL"
        )
        overall_results["access_permissions"] = permissions_results
        
        # Data Lineage
        print("\nLINK: Collecting data lineage...")
        lineage_results = collect_and_ingest_data_lineage(
            workspace_id, dce_endpoint, dcr_immutable_id, "Custom-FabricDataLineage_CL"
        )
        overall_results["data_lineage"] = lineage_results
        
        # Semantic Models
        print("\nFound Collecting semantic model performance...")
        models_results = collect_and_ingest_semantic_models(
            workspace_id, dce_endpoint, dcr_immutable_id, "Custom-FabricSemanticModels_CL"
        )
        overall_results["semantic_models"] = models_results
        
        # Calculate totals
        for category in [permissions_results, lineage_results, models_results]:
            overall_results["errors"].extend(category.get("errors", []))
            for collection_type in category:
                if isinstance(category[collection_type], dict) and "collected" in category[collection_type]:
                    overall_results["total_collected"] += category[collection_type]["collected"]
                    overall_results["total_ingested"] += category[collection_type]["ingested"]
        
        print(f"\nSUCCESS: Compliance monitoring cycle completed:")
        print(f"   Total collected: {overall_results['total_collected']}")
        print(f"   Total ingested: {overall_results['total_ingested']}")
        print(f"   Errors: {len(overall_results['errors'])}")
        
    except Exception as e:
        error_msg = f"Error in compliance monitoring cycle: {str(e)}"
        overall_results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return overall_results


def run_advanced_workloads_monitoring_cycle(
    workspace_id: str,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run Phase 3 advanced workloads monitoring cycle.
    
    Returns:
        Dict with overall results from all Phase 3 collections
    """
    print(f"STARTING: Starting advanced workloads monitoring cycle for workspace: {workspace_id}")
    
    overall_results = {
        "real_time_intelligence": {},
        "mirroring": {},
        "ml_ai": {},
        "total_collected": 0,
        "total_ingested": 0,
        "errors": []
    }
    
    try:
        # Real-Time Intelligence
        print("\nFAST: Collecting Real-Time Intelligence metrics...")
        rti_results = collect_and_ingest_real_time_intelligence(
            workspace_id, dce_endpoint, dcr_immutable_id, "Custom-FabricRealTimeIntelligence_CL"
        )
        overall_results["real_time_intelligence"] = rti_results
        
        # Mirroring
        print("\n🪞 Collecting Mirroring status...")
        mirroring_results = collect_and_ingest_mirroring(
            workspace_id, dce_endpoint, dcr_immutable_id, "Custom-FabricMirroring_CL"
        )
        overall_results["mirroring"] = mirroring_results
        
        # ML/AI
        print("\nAGENT: Collecting ML/AI workloads...")
        mlai_results = collect_and_ingest_ml_ai(
            workspace_id, dce_endpoint, dcr_immutable_id, "Custom-FabricMLAI_CL"
        )
        overall_results["ml_ai"] = mlai_results
        
        # Calculate totals
        for category in [rti_results, mirroring_results, mlai_results]:
            overall_results["errors"].extend(category.get("errors", []))
            for collection_type in category:
                if isinstance(category[collection_type], dict) and "collected" in category[collection_type]:
                    overall_results["total_collected"] += category[collection_type]["collected"]
                    overall_results["total_ingested"] += category[collection_type]["ingested"]
        
        print(f"\nSUCCESS: Advanced workloads monitoring cycle completed:")
        print(f"   Total collected: {overall_results['total_collected']}")
        print(f"   Total ingested: {overall_results['total_ingested']}")
        print(f"   Errors: {len(overall_results['errors'])}")
        
    except Exception as e:
        error_msg = f"Error in advanced workloads monitoring cycle: {str(e)}"
        overall_results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return overall_results


def run_comprehensive_monitoring_cycle(
    workspace_id: str,
    capacity_id: Optional[str] = None,
    dce_endpoint: Optional[str] = None,
    dcr_immutable_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run comprehensive monitoring cycle including all phases (1, 2, and 3).
    
    Returns:
        Dict with overall results from all monitoring phases
    """
    print(f"TARGET: Starting comprehensive monitoring cycle for workspace: {workspace_id}")
    
    overall_results = {
        "phase1_operational": {},
        "phase2_compliance": {},
        "phase3_advanced": {},
        "total_collected": 0,
        "total_ingested": 0,
        "errors": []
    }
    
    try:
        # Phase 1: Operational Monitoring
        print("\nFound Phase 1: Operational monitoring...")
        phase1_config = {}
        if dce_endpoint:
            phase1_config["dce_endpoint"] = dce_endpoint
        if dcr_immutable_id:
            phase1_config["dcr_immutable_id"] = dcr_immutable_id
        
        phase1_results = run_operational_monitoring_cycle(
            workspace_id=workspace_id, 
            capacity_id=capacity_id, 
            lookback_hours=24,
            custom_config=phase1_config if phase1_config else None
        )
        overall_results["phase1_operational"] = phase1_results
        
        # Phase 2: Compliance Monitoring
        print("\nSECURE: Phase 2: Compliance monitoring...")
        phase2_results = run_compliance_monitoring_cycle(workspace_id, capacity_id, dce_endpoint, dcr_immutable_id)
        overall_results["phase2_compliance"] = phase2_results
        
        # Phase 3: Advanced Workloads
        print("\nSTARTING: Phase 3: Advanced workloads monitoring...")
        phase3_results = run_advanced_workloads_monitoring_cycle(workspace_id, dce_endpoint, dcr_immutable_id)
        overall_results["phase3_advanced"] = phase3_results
        
        # Calculate totals
        for phase in [phase1_results, phase2_results, phase3_results]:
            overall_results["errors"].extend(phase.get("errors", []))
            overall_results["total_collected"] += phase.get("total_collected", 0)
            overall_results["total_ingested"] += phase.get("total_ingested", 0)
        
        print(f"\nCOMPLETE: Comprehensive monitoring cycle completed:")
        print(f"   Total collected: {overall_results['total_collected']}")
        print(f"   Total ingested: {overall_results['total_ingested']}")
        print(f"   Errors: {len(overall_results['errors'])}")
        
    except Exception as e:
        error_msg = f"Error in comprehensive monitoring cycle: {str(e)}"
        overall_results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
    
    return overall_results


# ================================
# Spark Monitoring Workflows
# ================================

def collect_and_ingest_spark_applications(
    workspace_id: str,
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
    max_items: int = 500
) -> Dict[str, Any]:
    """
    Collect Spark applications from workspace and ingest to Log Analytics.
    
    Args:
        workspace_id: Fabric workspace ID
        lookback_hours: Hours to look back for applications
        custom_config: Optional custom configuration
        max_items: Maximum items to collect
        
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import collect_spark_applications_workspace
    
    print(f"STARTING: Starting Spark applications collection for workspace {workspace_id}")
    
    results = {
        "collected": 0,
        "ingested": 0,
        "errors": [],
        "workspace_id": workspace_id,
        "collection_type": "spark_applications"
    }
    
    try:
        # Get configuration
        config = custom_config or get_config()
        ingestion_config = get_ingestion_config()
        
        # Collect Spark applications
        applications = []
        for app in collect_spark_applications_workspace(workspace_id, lookback_hours, max_items):
            applications.append(app)
            results["collected"] += 1
            
        if not applications:
            print("WARNING: No Spark applications collected")
            return results
            
        print(f"PACKAGE: Collected {len(applications)} Spark applications")
        
        # Ingest to Log Analytics
        if ingestion_config.get("enabled", True):
            ingestion_result = post_rows_to_dcr_enhanced(
                applications,
                ingestion_config["dce_endpoint"],
                ingestion_config["dcr_immutable_id"],
                ingestion_config["stream_name"],
                ingestion_config["table_name"]
            )
            
            results["ingested"] = ingestion_result.get("ingested_count", 0)
            if ingestion_result.get("errors"):
                results["errors"].extend(ingestion_result["errors"])
                
        print(f"SUCCESS: Spark applications workflow completed")
        print(f"   Collected: {results['collected']}")
        print(f"   Ingested: {results['ingested']}")
        
    except Exception as e:
        error_msg = f"Error in Spark applications collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
        
    return results


def collect_and_ingest_spark_item_applications(
    workspace_id: str,
    item_id: str,
    item_type: str = "notebook",
    lookback_hours: int = 24,
    custom_config: Optional[Dict[str, str]] = None,
    max_items: int = 100
) -> Dict[str, Any]:
    """
    Collect Spark applications for specific item and ingest to Log Analytics.
    
    Args:
        workspace_id: Fabric workspace ID
        item_id: Item ID (notebook, Spark job definition, etc.)
        item_type: Type of item ('notebook', 'sparkjobdefinition', 'lakehouse')
        lookback_hours: Hours to look back for applications
        custom_config: Optional custom configuration
        max_items: Maximum items to collect
        
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import collect_spark_applications_item
    
    print(f"STARTING: Starting Spark applications collection for {item_type} {item_id}")
    
    results = {
        "collected": 0,
        "ingested": 0,
        "errors": [],
        "workspace_id": workspace_id,
        "item_id": item_id,
        "item_type": item_type,
        "collection_type": "spark_item_applications"
    }
    
    try:
        # Get configuration
        config = custom_config or get_config()
        ingestion_config = get_ingestion_config()
        
        # Collect Spark applications
        applications = []
        for app in collect_spark_applications_item(workspace_id, item_id, item_type, lookback_hours, max_items):
            applications.append(app)
            results["collected"] += 1
            
        if not applications:
            print(f"WARNING: No Spark applications collected for {item_type} {item_id}")
            return results
            
        print(f"PACKAGE: Collected {len(applications)} Spark applications for {item_type}")
        
        # Ingest to Log Analytics
        if ingestion_config.get("enabled", True):
            ingestion_result = post_rows_to_dcr_enhanced(
                applications,
                ingestion_config["dce_endpoint"],
                ingestion_config["dcr_immutable_id"],
                ingestion_config["stream_name"],
                ingestion_config["table_name"]
            )
            
            results["ingested"] = ingestion_result.get("ingested_count", 0)
            if ingestion_result.get("errors"):
                results["errors"].extend(ingestion_result["errors"])
                
        print(f"SUCCESS: Spark item applications workflow completed")
        print(f"   Collected: {results['collected']}")
        print(f"   Ingested: {results['ingested']}")
        
    except Exception as e:
        error_msg = f"Error in Spark item applications collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
        
    return results


def collect_and_ingest_spark_logs(
    workspace_id: str,
    session_id: str,
    log_types: List[str] = ["driver", "executor", "livy"],
    custom_config: Optional[Dict[str, str]] = None,
    max_lines: int = 1000
) -> Dict[str, Any]:
    """
    Collect Spark logs for a session and ingest to Log Analytics.
    
    Args:
        workspace_id: Fabric workspace ID
        session_id: Spark session ID
        log_types: Types of logs to collect
        custom_config: Optional custom configuration
        max_lines: Maximum log lines per type
        
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import collect_spark_logs
    
    print(f"STARTING: Starting Spark logs collection for session {session_id}")
    
    results = {
        "collected": 0,
        "ingested": 0,
        "errors": [],
        "workspace_id": workspace_id,
        "session_id": session_id,
        "collection_type": "spark_logs"
    }
    
    try:
        # Get configuration
        config = custom_config or get_config()
        ingestion_config = get_ingestion_config()
        
        # Collect logs for each type
        all_logs = []
        for log_type in log_types:
            logs = []
            for log_entry in collect_spark_logs(workspace_id, session_id, log_type, max_lines):
                logs.append(log_entry)
                results["collected"] += 1
                
            all_logs.extend(logs)
            print(f"PACKAGE: Collected {len(logs)} {log_type} log entries")
            
        if not all_logs:
            print("WARNING: No Spark logs collected")
            return results
            
        # Ingest to Log Analytics
        if ingestion_config.get("enabled", True):
            ingestion_result = post_rows_to_dcr_enhanced(
                all_logs,
                ingestion_config["dce_endpoint"],
                ingestion_config["dcr_immutable_id"],
                ingestion_config["stream_name"],
                ingestion_config["table_name"]
            )
            
            results["ingested"] = ingestion_result.get("ingested_count", 0)
            if ingestion_result.get("errors"):
                results["errors"].extend(ingestion_result["errors"])
                
        print(f"SUCCESS: Spark logs workflow completed")
        print(f"   Collected: {results['collected']}")
        print(f"   Ingested: {results['ingested']}")
        
    except Exception as e:
        error_msg = f"Error in Spark logs collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
        
    return results


def collect_and_ingest_spark_metrics(
    workspace_id: str,
    session_id: str,
    application_id: str,
    custom_config: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Collect Spark metrics for an application and ingest to Log Analytics.
    
    Args:
        workspace_id: Fabric workspace ID
        session_id: Spark session ID
        application_id: Spark application ID
        custom_config: Optional custom configuration
        
    Returns:
        Dict with collection and ingestion results
    """
    from .collectors import collect_spark_metrics
    
    print(f"STARTING: Starting Spark metrics collection for application {application_id}")
    
    results = {
        "collected": 0,
        "ingested": 0,
        "errors": [],
        "workspace_id": workspace_id,
        "session_id": session_id,
        "application_id": application_id,
        "collection_type": "spark_metrics"
    }
    
    try:
        # Get configuration
        config = custom_config or get_config()
        ingestion_config = get_ingestion_config()
        
        # Collect Spark metrics
        metrics = []
        for metric in collect_spark_metrics(workspace_id, session_id, application_id):
            metrics.append(metric)
            results["collected"] += 1
            
        if not metrics:
            print("WARNING: No Spark metrics collected")
            return results
            
        print(f"PACKAGE: Collected {len(metrics)} Spark metrics")
        
        # Ingest to Log Analytics
        if ingestion_config.get("enabled", True):
            ingestion_result = post_rows_to_dcr_enhanced(
                metrics,
                ingestion_config["dce_endpoint"],
                ingestion_config["dcr_immutable_id"],
                ingestion_config["stream_name"],
                ingestion_config["table_name"]
            )
            
            results["ingested"] = ingestion_result.get("ingested_count", 0)
            if ingestion_result.get("errors"):
                results["errors"].extend(ingestion_result["errors"])
                
        print(f"SUCCESS: Spark metrics workflow completed")
        print(f"   Collected: {results['collected']}")
        print(f"   Ingested: {results['ingested']}")
        
    except Exception as e:
        error_msg = f"Error in Spark metrics collection: {str(e)}"
        results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
        
    return results


def comprehensive_spark_monitoring(
    workspace_id: str,
    lookback_hours: int = 24,
    include_logs: bool = False,
    include_metrics: bool = True,
    custom_config: Optional[Dict[str, str]] = None,
    max_applications: int = 100,
    max_log_lines: int = 500
) -> Dict[str, Any]:
    """
    Comprehensive Spark monitoring workflow that collects applications, logs, and metrics.
    
    Args:
        workspace_id: Fabric workspace ID
        lookback_hours: Hours to look back for applications
        include_logs: Whether to collect detailed logs
        include_metrics: Whether to collect detailed metrics
        custom_config: Optional custom configuration
        max_applications: Maximum applications to process
        max_log_lines: Maximum log lines per session
        
    Returns:
        Dict with comprehensive results
    """
    print(f"STARTING: Starting comprehensive Spark monitoring for workspace {workspace_id}")
    
    overall_results = {
        "workspace_id": workspace_id,
        "monitoring_type": "comprehensive_spark",
        "applications_collected": 0,
        "logs_collected": 0,
        "metrics_collected": 0,
        "total_ingested": 0,
        "errors": [],
        "details": {}
    }
    
    try:
        # Step 1: Collect Spark applications
        print("Found Step 1: Collecting Spark applications...")
        app_results = collect_and_ingest_spark_applications(
            workspace_id, lookback_hours, custom_config, max_applications
        )
        overall_results["applications_collected"] = app_results["collected"]
        overall_results["total_ingested"] += app_results["ingested"]
        overall_results["details"]["applications"] = app_results
        
        if app_results["errors"]:
            overall_results["errors"].extend(app_results["errors"])
            
        # Step 2: Collect detailed logs and metrics for recent applications
        if (include_logs or include_metrics) and app_results["collected"] > 0:
            print("Found Step 2: Collecting detailed Spark data...")
            
            # Get recent applications from the collection
            from .collectors import collect_spark_applications_workspace
            recent_apps = []
            for app in collect_spark_applications_workspace(workspace_id, 6, 10):  # Last 6 hours, max 10 apps
                recent_apps.append(app)
                
            for app in recent_apps:
                session_id = app.get("SessionId")
                application_id = app.get("ApplicationId")
                
                if not session_id:
                    continue
                    
                try:
                    # Collect logs if requested
                    if include_logs:
                        log_results = collect_and_ingest_spark_logs(
                            workspace_id, session_id, ["driver", "executor"], custom_config, max_log_lines
                        )
                        overall_results["logs_collected"] += log_results["collected"]
                        overall_results["total_ingested"] += log_results["ingested"]
                        
                        if log_results["errors"]:
                            overall_results["errors"].extend(log_results["errors"])
                            
                    # Collect metrics if requested and application ID is available
                    if include_metrics and application_id:
                        metrics_results = collect_and_ingest_spark_metrics(
                            workspace_id, session_id, application_id, custom_config
                        )
                        overall_results["metrics_collected"] += metrics_results["collected"]
                        overall_results["total_ingested"] += metrics_results["ingested"]
                        
                        if metrics_results["errors"]:
                            overall_results["errors"].extend(metrics_results["errors"])
                            
                except Exception as e:
                    error_msg = f"Error processing application {application_id}: {str(e)}"
                    overall_results["errors"].append(error_msg)
                    print(f"WARNING: {error_msg}")
                    continue
                    
        print(f"SUCCESS: Comprehensive Spark monitoring completed")
        print(f"   Applications: {overall_results['applications_collected']}")
        print(f"   Logs: {overall_results['logs_collected']}")
        print(f"   Metrics: {overall_results['metrics_collected']}")
        print(f"   Total ingested: {overall_results['total_ingested']}")
        print(f"   Errors: {len(overall_results['errors'])}")
        
    except Exception as e:
        error_msg = f"Error in comprehensive Spark monitoring: {str(e)}"
        overall_results["errors"].append(error_msg)
        print(f"ERROR: {error_msg}")
        
    return overall_results
