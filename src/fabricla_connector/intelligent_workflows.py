"""
This module provides smart workflows that automatically detect Microsoft's workspace
monitoring capabilities and adjust collection strategy to avoid conflicts while
maximizing unique value.
"""

import logging
from typing import Dict, Any, Optional, List
from .api import get_fabric_token
from .config import get_fabric_config, get_monitoring_config
from .monitoring_detection import (
    get_monitoring_detector, 
    get_monitoring_strategy, 
    print_monitoring_status
)
from .collectors import (
    PipelineDataCollector,
    DatasetRefreshCollector,
    CapacityUtilizationCollector,
    UserActivityCollector
)
from .ingestion import post_rows_to_dcr

logger = logging.getLogger(__name__)


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
            ("capacity_utilization", lambda: _collect_capacity_data(capacity_id, monitoring_config) if capacity_id else None)
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
                        
                        print(f"✅ {source_name}: {collection_result.get('total_records', 0)} records")
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
                print(f"⏭️  {source_name}: Skipped - {reason}")
                if alternative:
                    print(f"   💡 Alternative: {alternative}")
        
        # Generate final summary
        collected = results["summary"]["collected_sources"]
        total = results["summary"]["total_sources"]
        records = results["summary"]["total_records"]
        
        print(f"\n🎯 Intelligent Monitoring Summary:")
        print(f"   📊 Data Sources: {collected}/{total} collected")
        print(f"   📝 Total Records: {records:,}")
        print(f"   🧠 Strategy: {monitoring_config['strategy']}")
        
        # Add recommendations for skipped sources
        if results["skipped_collections"]:
            print(f"\n💡 Recommendations for skipped sources:")
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


def _collect_pipeline_data(workspace_id: str, monitoring_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Collect pipeline execution data."""
    try:
        from .workflows import collect_and_ingest_pipeline_data_enhanced
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
        from .workflows import collect_and_ingest_user_activity
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
        from .workflows import collect_and_ingest_dataset_refreshes
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
        from .workflows import collect_and_ingest_capacity_utilization
        return collect_and_ingest_capacity_utilization(
            capacity_id=capacity_id,
            lookback_hours=monitoring_config.get('lookback_hours', 24)
        )
    except Exception as e:
        logger.error(f"Capacity data collection failed: {e}")
        return {"status": "error", "error": str(e)}


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
            "dataset_refresh", "capacity_utilization"
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