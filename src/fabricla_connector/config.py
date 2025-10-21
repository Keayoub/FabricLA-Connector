"""
Configuration management for FabricLA-Connector with environment detection.
Supports both Fabric notebook and local development environments.
"""
import os
from typing import Dict, Optional, Any

def is_running_in_fabric() -> bool:
    """Detect if code is running in Microsoft Fabric environment"""
    try:
        import notebookutils
        return True
    except ImportError:
        return False


def get_fabric_environment_info() -> Dict[str, Any]:
    """Get Fabric environment information if available"""
    if not is_running_in_fabric():
        return {}
    
    try:
        import notebookutils
        
        # Get workspace info if available
        workspace_info = {}
        try:
            # Fabric provides workspace context
            workspace_info = {
                "is_fabric": True,
                "notebook_utils_available": True
            }
        except:
            pass
        
        return workspace_info
    except Exception as e:
        return {"error": str(e)}


def get_config() -> Dict[str, Optional[str]]:
    """
    Load configuration from environment variables with Fabric awareness.
    
    Priority order:
    1. Environment variables (works in both Fabric and local)
    2. Fabric Key Vault (if running in Fabric)
    3. Default values
    """
    config = {
        # Core ingestion configuration
        'DCE_ENDPOINT': os.getenv('AZURE_MONITOR_DCE_ENDPOINT'),
        'DCR_IMMUTABLE_ID': os.getenv('AZURE_MONITOR_DCR_IMMUTABLE_ID'), 
        'STREAM_NAME': os.getenv('AZURE_MONITOR_STREAM_NAME'),
        'TABLE_NAME': os.getenv('LOG_ANALYTICS_TABLE'),
        
        # Authentication configuration
        'FABRIC_TENANT_ID': os.getenv('FABRIC_TENANT_ID'),
        'FABRIC_APP_ID': os.getenv('FABRIC_APP_ID'),
        'FABRIC_APP_SECRET': os.getenv('FABRIC_APP_SECRET'),
        
        # Workspace configuration
        'FABRIC_WORKSPACE_ID': os.getenv('FABRIC_WORKSPACE_ID'),
        'FABRIC_CAPACITY_ID': os.getenv('FABRIC_CAPACITY_ID'),
        
        # Collection settings
        'LOOKBACK_HOURS': os.getenv('LOOKBACK_HOURS', '24'),
        'CHUNK_SIZE': os.getenv('CHUNK_SIZE', '1000'),
        'MAX_RETRIES': os.getenv('MAX_RETRIES', '3'),
        
        # Monitoring strategy settings
        'FABRIC_MONITORING_STRATEGY': os.getenv('FABRIC_MONITORING_STRATEGY', 'auto'),
        'WORKSPACE_MONITORING_CHECK': os.getenv('WORKSPACE_MONITORING_CHECK', 'true'),
        'FORCE_COLLECTION_OVERRIDE': os.getenv('FORCE_COLLECTION_OVERRIDE', 'false'),
        
        # Environment info
        'ENVIRONMENT': 'fabric' if is_running_in_fabric() else 'local'
    }
    
    # Try to get values from Fabric Key Vault if running in Fabric
    if is_running_in_fabric():
        try:
            import notebookutils
            
            # Try to get secrets from Fabric Key Vault
            fabric_secrets = {
                'FABRIC_TENANT_ID': ('Fabric', 'TenantId'),
                'FABRIC_APP_ID': ('Fabric', 'ClientId'),
                'FABRIC_APP_SECRET': ('Fabric', 'ClientSecret'),
                'DCE_ENDPOINT': ('LogAnalytics', 'DceEndpoint'),
                'DCR_IMMUTABLE_ID': ('LogAnalytics', 'DcrImmutableId'),
                'STREAM_NAME': ('LogAnalytics', 'StreamName')
            }
            
            for config_key, (kv_name, secret_name) in fabric_secrets.items():
                if not config[config_key]:  # Only if not already set via env var
                    try:
                        secret_value = notebookutils.credentials.getSecret(kv_name, secret_name)
                        if secret_value:
                            config[config_key] = secret_value
                    except Exception:
                        pass  # Secret not available, continue with env vars
                        
        except ImportError:
            pass  # notebookutils not available
    
    return config


def get_ingestion_config() -> Dict[str, Any]:
    """Get configuration specific to ingestion operations"""
    config = get_config()
    return {
        'dce_endpoint': config.get('DCE_ENDPOINT'),
        'dcr_immutable_id': config.get('DCR_IMMUTABLE_ID'),
        'stream_name': config.get('STREAM_NAME'),
        'table_name': config.get('TABLE_NAME'),
        'chunk_size': int(config.get('CHUNK_SIZE') or '1000'),
        'max_retries': int(config.get('MAX_RETRIES') or '3')
    }


def get_fabric_config() -> Dict[str, Any]:
    """Get configuration specific to Fabric API operations"""
    config = get_config()
    return {
        'tenant_id': config.get('FABRIC_TENANT_ID'),
        'client_id': config.get('FABRIC_APP_ID'), 
        'client_secret': config.get('FABRIC_APP_SECRET'),
        'workspace_id': config.get('FABRIC_WORKSPACE_ID'),
        'capacity_id': config.get('FABRIC_CAPACITY_ID'),
        'lookback_hours': int(config.get('LOOKBACK_HOURS') or '24'),
        'environment': config.get('ENVIRONMENT')
    }


def get_monitoring_config() -> Dict[str, Any]:
    """Get configuration specific to intelligent monitoring operations"""
    config = get_config()
    return {
        'strategy': config.get('FABRIC_MONITORING_STRATEGY', 'auto'),
        'workspace_monitoring_check': (config.get('WORKSPACE_MONITORING_CHECK', 'true') or 'true').lower() == 'true',
        'force_collection_override': (config.get('FORCE_COLLECTION_OVERRIDE', 'false') or 'false').lower() == 'true',
        'lookback_hours': int(config.get('LOOKBACK_HOURS') or '24'),
        'chunk_size': int(config.get('CHUNK_SIZE') or '1000'),
        'max_retries': int(config.get('MAX_RETRIES') or '3')
    }


def validate_config(config_type: str = 'all') -> Dict[str, Any]:
    """
    Validate configuration and return status report.
    
    Args:
        config_type: 'all', 'ingestion', or 'fabric'
    
    Returns:
        Dict with validation results
    """
    validation_result = {
        'valid': True,
        'missing_required': [],
        'missing_optional': [],
        'environment': get_config().get('ENVIRONMENT'),
        'fabric_available': is_running_in_fabric()
    }
    
    if config_type in ['all', 'ingestion']:
        ingestion_config = get_ingestion_config()
        required_ingestion = ['dce_endpoint', 'dcr_immutable_id', 'stream_name']
        
        for key in required_ingestion:
            if not ingestion_config.get(key):
                validation_result['missing_required'].append(f'ingestion.{key}')
                validation_result['valid'] = False
    
    if config_type in ['all', 'fabric']:
        fabric_config = get_fabric_config()
        required_fabric = ['tenant_id', 'client_id', 'client_secret']
        optional_fabric = ['workspace_id', 'capacity_id']
        
        for key in required_fabric:
            if not fabric_config.get(key):
                validation_result['missing_required'].append(f'fabric.{key}')
                validation_result['valid'] = False
        
        for key in optional_fabric:
            if not fabric_config.get(key):
                validation_result['missing_optional'].append(f'fabric.{key}')
    
    return validation_result


def print_config_status():
    """Print current configuration status for debugging"""
    config = get_config()
    validation = validate_config()
    
    print("FIXING: Configuration Status")
    print("=" * 50)
    print(f"Environment: {validation['environment']}")
    print(f"Fabric Available: {validation['fabric_available']}")
    print(f"Valid: {'SUCCESS:' if validation['valid'] else 'ERROR:'}")
    
    if validation['missing_required']:
        print(f"\nERROR: Missing Required:")
        for item in validation['missing_required']:
            print(f"   - {item}")
    
    if validation['missing_optional']:
        print(f"\nWARNING:  Missing Optional:")
        for item in validation['missing_optional']:
            print(f"   - {item}")
    
    print(f"\nFound Configuration Summary:")
    for key, value in config.items():
        if 'secret' in key.lower() or 'password' in key.lower():
            display_value = f"{'*' * len(value) if value else 'Not Set'}"
        else:
            display_value = value or "Not Set"
        print(f"   {key}: {display_value}")


# Backward compatibility
def get_fabric_workspace_id() -> Optional[str]:
    """Get Fabric workspace ID from configuration"""
    return get_fabric_config().get('workspace_id')


def get_lookback_hours() -> int:
    """Get lookback hours from configuration"""
    return int(get_config().get('LOOKBACK_HOURS') or '24')
