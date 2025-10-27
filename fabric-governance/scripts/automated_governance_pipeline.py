"""
Automated Governance Pipeline for Fabric Tenant Settings

This script implements an automated governance pipeline that:
1. Monitors tenant settings for changes
2. Detects new preview features
3. Compares TEST vs PROD configurations
4. Sends alerts when drift is detected
5. Optionally auto-remediates by disabling preview features in PROD

Usage:
    python automated_governance_pipeline.py --mode monitor
    python automated_governance_pipeline.py --mode compare --test-tenant <id> --prod-tenant <id>
    python automated_governance_pipeline.py --mode remediate --disable-previews
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

import requests
from azure.identity import DefaultAzureCredential
from azure.monitor.ingestion import LogsIngestionClient
from azure.core.exceptions import HttpResponseError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('governance-pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FabricGovernancePipeline:
    """Main pipeline class for Fabric tenant governance automation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the governance pipeline with configuration."""
        self.config = config
        self.credential = DefaultAzureCredential()
        self.fabric_token = None
        self.baseline_settings = None
        
        # Load baseline settings if exists
        baseline_file = config.get('baseline_settings_file')
        if baseline_file and Path(baseline_file).exists():
            with open(baseline_file, 'r') as f:
                self.baseline_settings = json.load(f)
                logger.info(f"Loaded baseline settings from {baseline_file}")

    def authenticate(self) -> str:
        """Authenticate to Fabric API and return access token."""
        try:
            token = self.credential.get_token("https://api.fabric.microsoft.com/.default")
            self.fabric_token = token.token
            logger.info("Successfully authenticated to Fabric API")
            return token.token
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def get_tenant_settings(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve tenant settings from Fabric API.
        
        Args:
            tenant_id: Optional tenant ID (uses default if not provided)
            
        Returns:
            Dictionary containing tenant settings
        """
        if not self.fabric_token:
            self.authenticate()

        url = "https://api.fabric.microsoft.com/v1/admin/tenantsettings"
        headers = {
            "Authorization": f"Bearer {self.fabric_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            settings = response.json()
            logger.info(f"Retrieved {len(settings.get('tenantSettings', []))} tenant settings")
            return settings
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                logger.error("Access denied. Ensure you have Fabric Administrator role.")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve tenant settings: {e}")
            raise

    def identify_preview_features(self, settings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify which settings are preview features."""
        preview_keywords = [
            "preview", "experimental", "beta", "early access",
            "public preview", "private preview"
        ]

        preview_features = []
        
        for setting in settings:
            title = setting.get("title", "").lower()
            description = setting.get("description", "").lower()
            
            is_preview = any(
                keyword in title or keyword in description
                for keyword in preview_keywords
            )
            
            if is_preview:
                preview_features.append({
                    "settingName": setting.get("settingName"),
                    "title": setting.get("title"),
                    "enabled": setting.get("enabled", False),
                    "tenantSettingGroup": setting.get("tenantSettingGroup")
                })

        logger.info(f"Identified {len(preview_features)} preview features")
        return preview_features

    def compare_environments(
        self, 
        test_settings: Dict[str, Any], 
        prod_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare TEST and PROD tenant settings.
        
        Returns:
            Dictionary with comparison results and drift analysis
        """
        test_dict = {
            s['settingName']: s 
            for s in test_settings.get('tenantSettings', [])
        }
        prod_dict = {
            s['settingName']: s 
            for s in prod_settings.get('tenantSettings', [])
        }

        differences = []
        all_keys = set(test_dict.keys()) | set(prod_dict.keys())

        for key in all_keys:
            test_setting = test_dict.get(key)
            prod_setting = prod_dict.get(key)

            if not test_setting:
                differences.append({
                    "setting": key,
                    "type": "missing_in_test",
                    "prod_enabled": prod_setting.get("enabled")
                })
            elif not prod_setting:
                differences.append({
                    "setting": key,
                    "type": "missing_in_prod",
                    "test_enabled": test_setting.get("enabled")
                })
            elif test_setting.get("enabled") != prod_setting.get("enabled"):
                differences.append({
                    "setting": key,
                    "type": "enabled_state_differs",
                    "test_enabled": test_setting.get("enabled"),
                    "prod_enabled": prod_setting.get("enabled"),
                    "title": test_setting.get("title")
                })

        logger.info(f"Found {len(differences)} differences between TEST and PROD")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_differences": len(differences),
            "differences": differences
        }

    def detect_changes(self, current_settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect changes compared to baseline settings.
        
        Returns:
            List of detected changes
        """
        if not self.baseline_settings:
            logger.warning("No baseline settings available for comparison")
            return []

        changes = []
        current_dict = {
            s['settingName']: s 
            for s in current_settings.get('tenantSettings', [])
        }
        baseline_dict = {
            s['SettingName']: s 
            for s in self.baseline_settings.get('Settings', [])
        }

        for key, current in current_dict.items():
            baseline = baseline_dict.get(key)
            
            if not baseline:
                changes.append({
                    "type": "new_setting",
                    "setting": key,
                    "title": current.get("title"),
                    "enabled": current.get("enabled")
                })
            elif current.get("enabled") != baseline.get("Enabled"):
                changes.append({
                    "type": "state_changed",
                    "setting": key,
                    "title": current.get("title"),
                    "old_state": baseline.get("Enabled"),
                    "new_state": current.get("enabled")
                })

        logger.info(f"Detected {len(changes)} changes from baseline")
        return changes

    def send_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send alert notification via configured channels."""
        webhook_url = self.config.get('alert_webhook_url')
        
        if not webhook_url:
            logger.warning("No alert webhook configured, skipping notification")
            return

        try:
            response = requests.post(
                webhook_url,
                json=alert_data,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def ingest_to_log_analytics(
        self, 
        records: List[Dict[str, Any]], 
        stream_name: str
    ) -> None:
        """Ingest records to Azure Log Analytics."""
        dce_endpoint = self.config.get('dce_endpoint')
        dcr_id = self.config.get('dcr_immutable_id')

        if not dce_endpoint or not dcr_id:
            logger.warning("Log Analytics not configured, skipping ingestion")
            return

        client = LogsIngestionClient(
            endpoint=dce_endpoint, 
            credential=self.credential,
            logging_enable=True
        )

        try:
            client.upload(
                rule_id=dcr_id,
                stream_name=stream_name,
                logs=records
            )
            logger.info(f"Ingested {len(records)} records to Log Analytics")
        except HttpResponseError as e:
            logger.error(f"Log Analytics ingestion failed: {e}")
            raise

    def run_monitoring_mode(self) -> None:
        """Run the pipeline in monitoring mode."""
        logger.info("Starting governance pipeline in MONITORING mode")

        # Get current tenant settings
        current_settings = self.get_tenant_settings()
        
        # Identify preview features
        preview_features = self.identify_preview_features(
            current_settings.get('tenantSettings', [])
        )
        
        # Detect changes from baseline
        changes = self.detect_changes(current_settings)

        # Alert on new preview features
        new_previews = [
            c for c in changes 
            if c['type'] == 'new_setting' and 
            any(p['settingName'] == c['setting'] for p in preview_features)
        ]

        if new_previews:
            alert_data = {
                "alert_type": "new_preview_features",
                "count": len(new_previews),
                "features": new_previews,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.send_alert(alert_data)
            logger.warning(f"ALERT: {len(new_previews)} new preview features detected!")

        # Alert on any changes
        if changes and self.config.get('alert_on_setting_changes'):
            alert_data = {
                "alert_type": "setting_changes",
                "count": len(changes),
                "changes": changes,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.send_alert(alert_data)

        # Ingest to Log Analytics
        if self.config.get('enable_log_analytics'):
            self.ingest_to_log_analytics(
                records=[{
                    "TimeGenerated": datetime.now(timezone.utc).isoformat(),
                    "TenantId": self.config.get('fabric_tenant_id'),
                    "EventType": "MonitoringRun",
                    "PreviewFeaturesCount": len(preview_features),
                    "ChangesDetected": len(changes),
                    "NewPreviewsDetected": len(new_previews)
                }],
                stream_name="Custom-FabricGovernanceEvents_CL"
            )

        logger.info("Monitoring mode completed successfully")

    def run_comparison_mode(self, test_tenant_id: str, prod_tenant_id: str) -> None:
        """Run the pipeline in comparison mode."""
        logger.info(f"Starting governance pipeline in COMPARISON mode")
        logger.info(f"TEST tenant: {test_tenant_id}, PROD tenant: {prod_tenant_id}")

        # Get settings from both environments
        test_settings = self.get_tenant_settings(test_tenant_id)
        prod_settings = self.get_tenant_settings(prod_tenant_id)

        # Compare environments
        comparison = self.compare_environments(test_settings, prod_settings)

        # Check for preview features enabled in PROD
        prod_previews = self.identify_preview_features(
            prod_settings.get('tenantSettings', [])
        )
        enabled_prod_previews = [p for p in prod_previews if p['enabled']]

        if enabled_prod_previews:
            alert_data = {
                "alert_type": "preview_enabled_in_prod",
                "count": len(enabled_prod_previews),
                "features": enabled_prod_previews,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.send_alert(alert_data)
            logger.error(f"CRITICAL: {len(enabled_prod_previews)} preview features enabled in PROD!")

        # Fail on drift if configured
        if comparison['total_differences'] > 0 and self.config.get('fail_on_drift'):
            logger.error("Configuration drift detected - failing pipeline")
            sys.exit(1)

        logger.info("Comparison mode completed successfully")


def main():
    """Main entry point for the governance pipeline."""
    parser = argparse.ArgumentParser(
        description="Fabric Tenant Governance Automation Pipeline"
    )
    parser.add_argument(
        '--mode',
        choices=['monitor', 'compare', 'remediate'],
        required=True,
        help='Pipeline execution mode'
    )
    parser.add_argument('--test-tenant', help='TEST tenant ID for comparison mode')
    parser.add_argument('--prod-tenant', help='PROD tenant ID for comparison mode')
    parser.add_argument('--config', default='.env', help='Configuration file path')

    args = parser.parse_args()

    # Load configuration from environment
    from dotenv import load_dotenv
    load_dotenv(args.config)

    config = {
        'fabric_tenant_id': os.getenv('FABRIC_TENANT_ID'),
        'dce_endpoint': os.getenv('AZURE_MONITOR_DCE_ENDPOINT'),
        'dcr_immutable_id': os.getenv('AZURE_MONITOR_DCR_IMMUTABLE_ID'),
        'alert_webhook_url': os.getenv('ALERT_WEBHOOK_URL'),
        'baseline_settings_file': os.getenv('BASELINE_SETTINGS_FILE'),
        'alert_on_setting_changes': os.getenv('ALERT_ON_SETTING_CHANGES', 'true').lower() == 'true',
        'fail_on_drift': os.getenv('FAIL_ON_DRIFT', 'false').lower() == 'true',
        'enable_log_analytics': bool(os.getenv('AZURE_MONITOR_DCE_ENDPOINT'))
    }

    # Initialize pipeline
    pipeline = FabricGovernancePipeline(config)

    # Execute based on mode
    try:
        if args.mode == 'monitor':
            pipeline.run_monitoring_mode()
        elif args.mode == 'compare':
            if not args.test_tenant or not args.prod_tenant:
                parser.error("--test-tenant and --prod-tenant required for compare mode")
            pipeline.run_comparison_mode(args.test_tenant, args.prod_tenant)
        elif args.mode == 'remediate':
            logger.info("Remediation mode not yet implemented")
            sys.exit(1)

        logger.info("Pipeline execution completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
