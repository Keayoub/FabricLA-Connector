"""
This module implements intelligent detection of Microsoft's official workspace monitoring
capabilities and provides smart fallback logic to avoid conflicts while maximizing value.
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class WorkspaceMonitoringDetector:
    """Detects Microsoft's workspace monitoring status and provides collection recommendations."""
    
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def detect_workspace_monitoring_status(self, workspace_id: str) -> Dict[str, Any]:
        """
        Detect if Microsoft's workspace monitoring is enabled and what's covered.
        
        Returns:
            Dict containing monitoring status, capabilities, and recommendations
        """
        try:
            logger.info(f"Detecting workspace monitoring status for workspace {workspace_id}")
            
            # Try to detect workspace monitoring via multiple methods
            status = self._check_workspace_monitoring_api(workspace_id)
            
            if status.get("workspace_monitoring_enabled") is None:
                # Fallback: Try to detect via workspace items
                status = self._check_workspace_monitoring_items(workspace_id)
            
            # Add collection recommendations
            status["collection_recommendations"] = self._generate_collection_recommendations(status)
            status["detection_timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(f"Workspace monitoring detection completed: {status.get('workspace_monitoring_enabled', 'unknown')}")
            return status
            
        except Exception as e:
            logger.error(f"Error detecting workspace monitoring: {e}")
            return {
                "workspace_monitoring_enabled": "unknown",
                "error": str(e),
                "collection_recommendations": self._get_default_recommendations()
            }
    
    def _check_workspace_monitoring_api(self, workspace_id: str) -> Dict[str, Any]:
        """Check workspace monitoring via direct API (if available)."""
        try:
            # Try the potential workspace monitoring API endpoint
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/monitoring"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                monitoring_info = response.json()
                return {
                    "workspace_monitoring_enabled": True,
                    "detection_method": "direct_api",
                    "eventhouse_id": monitoring_info.get("eventhouseId"),
                    "retention_days": monitoring_info.get("retentionDays", 30),
                    "covered_workloads": monitoring_info.get("workloads", []),
                    "monitoring_info": monitoring_info
                }
            elif response.status_code == 404:
                return {
                    "workspace_monitoring_enabled": False,
                    "detection_method": "direct_api",
                    "reason": "monitoring_endpoint_not_found"
                }
            else:
                logger.warning(f"Workspace monitoring API returned {response.status_code}")
                return {"workspace_monitoring_enabled": None}
                
        except Exception as e:
            logger.debug(f"Direct API check failed: {e}")
            return {"workspace_monitoring_enabled": None}
    
    def _check_workspace_monitoring_items(self, workspace_id: str) -> Dict[str, Any]:
        """Check for workspace monitoring by looking for monitoring Eventhouse items."""
        try:
            # Get workspace items and look for monitoring Eventhouse
            url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                items = response.json().get("value", [])
                
                # Look for monitoring Eventhouse (typically named with "monitoring" or "Monitoring")
                monitoring_items = []
                for item in items:
                    item_type = item.get("type", "").lower()
                    item_name = item.get("displayName", "").lower()
                    
                    if (item_type == "eventhouse" and 
                        ("monitoring" in item_name or "monitor" in item_name)):
                        monitoring_items.append(item)
                
                if monitoring_items:
                    return {
                        "workspace_monitoring_enabled": True,
                        "detection_method": "items_scan",
                        "monitoring_items": monitoring_items,
                        "eventhouse_id": monitoring_items[0].get("id"),
                        "reason": "monitoring_eventhouse_found"
                    }
                else:
                    return {
                        "workspace_monitoring_enabled": False,
                        "detection_method": "items_scan",
                        "reason": "no_monitoring_eventhouse_found",
                        "total_items_checked": len(items)
                    }
            else:
                logger.warning(f"Items API returned {response.status_code}")
                return {"workspace_monitoring_enabled": None}
                
        except Exception as e:
            logger.debug(f"Items scan check failed: {e}")
            return {"workspace_monitoring_enabled": None}
    
    def _generate_collection_recommendations(self, status: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate intelligent collection recommendations based on monitoring status."""
        
        monitoring_enabled = status.get("workspace_monitoring_enabled")
        
        if monitoring_enabled is True:
            # Workspace monitoring is enabled - avoid conflicts
            return {
                "user_activity": {
                    "collect": False,
                    "reason": "covered_by_workspace_monitoring",
                    "alternative": "query_workspace_monitoring_eventhouse",
                    "conflict_level": "high"
                },
                "dataset_refresh": {
                    "collect": False,
                    "reason": "covered_by_semantic_model_operations",
                    "alternative": "query_workspace_monitoring_eventhouse",
                    "conflict_level": "high"
                },
                "dataset_metadata": {
                    "collect": False,
                    "reason": "covered_by_semantic_model_operations",
                    "alternative": "query_workspace_monitoring_eventhouse",
                    "conflict_level": "high"
                },
                "pipeline_execution": {
                    "collect": True,
                    "reason": "unique_value_not_covered_by_microsoft",
                    "strategy": "continue_collection",
                    "conflict_level": "none"
                },
                "dataflow_execution": {
                    "collect": True,
                    "reason": "unique_value_not_covered_by_microsoft", 
                    "strategy": "continue_collection",
                    "conflict_level": "none"
                },
                "capacity_utilization": {
                    "collect": True,
                    "reason": "unique_value_not_covered_by_microsoft",
                    "strategy": "continue_collection",
                    "conflict_level": "none"
                },
                "eventhouse_operations": {
                    "collect": True,
                    "reason": "complementary_to_workspace_monitoring",
                    "strategy": "enhanced_collection",
                    "conflict_level": "none"
                },
                "lakehouse_operations": {
                    "collect": True,
                    "reason": "unique_operational_insights",
                    "strategy": "enhanced_collection", 
                    "conflict_level": "none"
                },
                "gateway_health": {
                    "collect": True,
                    "reason": "critical_infrastructure_not_covered",
                    "strategy": "enhanced_collection",
                    "conflict_level": "none"
                }
            }
        elif monitoring_enabled is False:
            # No workspace monitoring - collect everything
            return {
                "user_activity": {
                    "collect": True,
                    "reason": "workspace_monitoring_disabled",
                    "strategy": "full_collection",
                    "conflict_level": "none"
                },
                "dataset_refresh": {
                    "collect": True,
                    "reason": "workspace_monitoring_disabled",
                    "strategy": "full_collection",
                    "conflict_level": "none"
                },
                "dataset_metadata": {
                    "collect": True,
                    "reason": "workspace_monitoring_disabled",
                    "strategy": "full_collection",
                    "conflict_level": "none"
                },
                "pipeline_execution": {
                    "collect": True,
                    "reason": "comprehensive_monitoring",
                    "strategy": "full_collection",
                    "conflict_level": "none"
                },
                "dataflow_execution": {
                    "collect": True,
                    "reason": "comprehensive_monitoring",
                    "strategy": "full_collection",
                    "conflict_level": "none"
                },
                "capacity_utilization": {
                    "collect": True,
                    "reason": "comprehensive_monitoring",
                    "strategy": "full_collection",
                    "conflict_level": "none"
                }
            }
        else:
            # Unknown status - conservative approach
            return self._get_default_recommendations()
    
    def _get_default_recommendations(self) -> Dict[str, Dict[str, Any]]:
        """Get conservative default recommendations when status is unknown."""
        return {
            "user_activity": {
                "collect": False,
                "reason": "unknown_monitoring_status_conservative_approach",
                "strategy": "skip_potentially_conflicting",
                "conflict_level": "unknown"
            },
            "dataset_refresh": {
                "collect": False,
                "reason": "unknown_monitoring_status_conservative_approach", 
                "strategy": "skip_potentially_conflicting",
                "conflict_level": "unknown"
            },
            "dataset_metadata": {
                "collect": False,
                "reason": "unknown_monitoring_status_conservative_approach",
                "strategy": "skip_potentially_conflicting", 
                "conflict_level": "unknown"
            },
            "pipeline_execution": {
                "collect": True,
                "reason": "unique_value_always_safe",
                "strategy": "safe_collection",
                "conflict_level": "none"
            },
            "dataflow_execution": {
                "collect": True,
                "reason": "unique_value_always_safe",
                "strategy": "safe_collection",
                "conflict_level": "none"
            },
            "capacity_utilization": {
                "collect": True,
                "reason": "unique_value_always_safe",
                "strategy": "safe_collection",
                "conflict_level": "none"
            }
        }


class MonitoringStrategy:
    """Manages monitoring strategy and provides collection decisions."""
    
    def __init__(self, strategy: str = "auto"):
        """
        Initialize monitoring strategy.
        
        Args:
            strategy: One of 'auto', 'full', 'complement', 'minimal'
        """
        self.strategy = self._validate_strategy(strategy)
        
    def _validate_strategy(self, strategy: str) -> str:
        """Validate and return monitoring strategy."""
        valid_strategies = ["auto", "full", "complement", "minimal"]
        
        # Check environment variable override
        env_strategy = os.getenv("FABRIC_MONITORING_STRATEGY", strategy).lower()
        
        if env_strategy in valid_strategies:
            return env_strategy
        else:
            logger.warning(f"Invalid strategy '{env_strategy}', falling back to 'auto'")
            return "auto"
    
    def should_collect_data_source(self, data_source: str, 
                                 workspace_monitoring_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if a data source should be collected based on strategy and monitoring status.
        
        Args:
            data_source: Name of the data source (e.g., 'user_activity', 'pipeline_execution')
            workspace_monitoring_status: Result from WorkspaceMonitoringDetector
            
        Returns:
            Dict with collection decision and reasoning
        """
        recommendations = workspace_monitoring_status.get("collection_recommendations", {})
        data_recommendation = recommendations.get(data_source, {})
        
        if self.strategy == "full":
            # Always collect everything regardless of conflicts
            return {
                "collect": True,
                "reason": f"full_strategy_override",
                "strategy": "force_collection",
                "original_recommendation": data_recommendation
            }
        
        elif self.strategy == "complement":
            # Only collect if no conflicts
            should_collect = data_recommendation.get("conflict_level", "unknown") == "none"
            return {
                "collect": should_collect,
                "reason": "complement_strategy_avoid_conflicts",
                "strategy": "complement_only",
                "original_recommendation": data_recommendation
            }
        
        elif self.strategy == "minimal":
            # Only collect unique high-value data
            minimal_sources = ["pipeline_execution", "dataflow_execution", "capacity_utilization"]
            should_collect = data_source in minimal_sources
            return {
                "collect": should_collect,
                "reason": "minimal_strategy_core_only",
                "strategy": "minimal_collection",
                "original_recommendation": data_recommendation
            }
        
        else:  # auto strategy
            # Use intelligent recommendations
            should_collect = data_recommendation.get("collect", True)
            return {
                "collect": should_collect,
                "reason": data_recommendation.get("reason", "auto_strategy_intelligent"),
                "strategy": data_recommendation.get("strategy", "auto_collection"),
                "alternative": data_recommendation.get("alternative"),
                "conflict_level": data_recommendation.get("conflict_level", "unknown"),
                "original_recommendation": data_recommendation
            }


def get_monitoring_detector(token: str) -> WorkspaceMonitoringDetector:
    """Factory function to create monitoring detector."""
    return WorkspaceMonitoringDetector(token)


def get_monitoring_strategy(strategy: str = None) -> MonitoringStrategy:
    """Factory function to create monitoring strategy."""
    if strategy is None:
        strategy = os.getenv("FABRIC_MONITORING_STRATEGY", "auto")
    return MonitoringStrategy(strategy)


def print_monitoring_status(workspace_monitoring_status: Dict[str, Any], 
                          strategy: MonitoringStrategy) -> None:
    """Print a comprehensive monitoring status report."""
    
    print("\n" + "="*80)
    print("🔍 FABRIC MONITORING INTELLIGENCE REPORT")
    print("="*80)
    
    # Workspace monitoring status
    monitoring_enabled = workspace_monitoring_status.get("workspace_monitoring_enabled")
    detection_method = workspace_monitoring_status.get("detection_method", "unknown")
    
    print(f"\n📊 Workspace Monitoring Status:")
    if monitoring_enabled is True:
        print(f"   ✅ ENABLED (detected via {detection_method})")
        eventhouse_id = workspace_monitoring_status.get("eventhouse_id")
        if eventhouse_id:
            print(f"   🏠 Eventhouse ID: {eventhouse_id}")
    elif monitoring_enabled is False:
        print(f"   ❌ DISABLED (detected via {detection_method})")
    else:
        print(f"   ⚠️  UNKNOWN (detection method: {detection_method})")
    
    # Strategy
    print(f"\n⚙️  Collection Strategy: {strategy.strategy.upper()}")
    
    # Collection recommendations
    recommendations = workspace_monitoring_status.get("collection_recommendations", {})
    print(f"\n📋 Collection Decisions:")
    
    for data_source, recommendation in recommendations.items():
        decision = strategy.should_collect_data_source(data_source, workspace_monitoring_status)
        status_icon = "✅" if decision["collect"] else "❌"
        conflict_level = recommendation.get("conflict_level", "unknown")
        conflict_icon = {"none": "🟢", "high": "🔴", "unknown": "🟡"}.get(conflict_level, "⚪")
        
        print(f"   {status_icon} {data_source.replace('_', ' ').title()}")
        print(f"      └─ Reason: {decision['reason']}")
        print(f"      └─ Conflict Level: {conflict_icon} {conflict_level}")
        
        if not decision["collect"] and decision.get("alternative"):
            print(f"      └─ Alternative: {decision['alternative']}")
    
    print("\n" + "="*80)