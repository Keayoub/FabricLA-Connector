"""
Pipeline and dataflow data collectors.
"""
from typing import Iterator, Dict, Any
from .base import BaseCollector


class PipelineDataCollector(BaseCollector):
    """
    Collector for pipeline and dataflow execution data.
    
    Collects:
    - Pipeline runs
    - Dataflow runs
    - Activity runs within pipelines
    """
    
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect all pipeline and dataflow data.
        
        Yields:
            Pipeline run and dataflow run records
        """
        yield from self.collect_pipeline_runs()
        yield from self.collect_dataflow_runs()
    
    def collect_pipeline_runs(self) -> Iterator[Dict[str, Any]]:
        """
        Collect pipeline run data.
        
        Yields:
            Pipeline run records mapped to Log Analytics schema
        """
        from ..mappers.pipeline import PipelineRunMapper
        
        # Get all pipelines in workspace
        pipelines = self.client.list_workspace_items(
            self.workspace_id, 
            item_type="DataPipeline"
        )
        
        for pipeline in pipelines:
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['displayName']
            
            # Get job instances for this pipeline
            instances = self.client.list_item_job_instances(
                self.workspace_id, 
                pipeline_id, 
                lookback_hours=self.lookback_hours
            )
            
            for instance in instances:
                yield PipelineRunMapper.map(
                    workspace_id=self.workspace_id,
                    pipeline_id=pipeline_id,
                    pipeline_name=pipeline_name,
                    run=instance
                )
    
    def collect_dataflow_runs(self) -> Iterator[Dict[str, Any]]:
        """
        Collect dataflow run data.
        
        Yields:
            Dataflow run records mapped to Log Analytics schema
        """
        from ..mappers.pipeline import DataflowRunMapper
        
        # Get all dataflows in workspace
        dataflows = self.client.list_workspace_items(
            self.workspace_id,
            item_type="Dataflow"
        )
        
        for dataflow in dataflows:
            dataflow_id = dataflow['id']
            dataflow_name = dataflow['displayName']
            
            # Get job instances for this dataflow
            instances = self.client.list_item_job_instances(
                self.workspace_id,
                dataflow_id,
                lookback_hours=self.lookback_hours
            )
            
            for instance in instances:
                yield DataflowRunMapper.map(
                    workspace_id=self.workspace_id,
                    dataflow_id=dataflow_id,
                    dataflow_name=dataflow_name,
                    run=instance
                )
    
    def collect_activity_runs(self, pipeline_id: str, run_id: str) -> Iterator[Dict[str, Any]]:
        """
        Collect activity run data for a specific pipeline run.
        
        Args:
            pipeline_id: Pipeline ID
            run_id: Pipeline run ID
            
        Yields:
            Activity run records mapped to Log Analytics schema
        """
        from ..mappers.pipeline import ActivityRunMapper
        
        activities = self.client.get_activity_runs(
            self.workspace_id,
            pipeline_id,
            run_id
        )
        
        for activity in activities:
            yield ActivityRunMapper.map(
                workspace_id=self.workspace_id,
                pipeline_id=pipeline_id,
                pipeline_run_id=run_id,
                activity=activity
            )
