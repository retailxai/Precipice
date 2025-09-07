import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yaml

from agents import *
from agents.base_agent import AgentConfig, AgentResult, BaseAgent
from entities import Company

logger = logging.getLogger("RetailXAI.AgentManager")


class AgentManager:
    """Central manager for all RetailXAI agents."""

    def __init__(self, config_path: str = "config/agents.yaml", shutdown_event: Optional[threading.Event] = None):
        """Initialize the agent manager.

        Args:
            config_path: Path to agent configuration file.
            shutdown_event: Event for graceful shutdown.
        """
        self.config_path = config_path
        self.shutdown_event = shutdown_event
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.execution_history: List[AgentResult] = []
        self.max_history_size = 1000  # Limit history size to prevent memory leaks
        self.companies: List[Company] = []
        self.db_manager = None  # Will be set by scheduler
        self._load_configuration()
        self._initialize_agents()
        self._load_agent_states()

    def _load_configuration(self) -> None:
        """Load agent configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Load companies (needed for some agents)
            with open('config/companies.yaml', 'r', encoding='utf-8') as f:
                companies_data = yaml.safe_load(f)
                self.companies = [Company(**company) for company in companies_data.get('companies', [])]
            
            # Parse agent configurations
            for agent_name, agent_data in config_data.get('agents', {}).items():
                self.agent_configs[agent_name] = AgentConfig(
                    name=agent_name,
                    enabled=agent_data.get('enabled', True),
                    interval_minutes=agent_data.get('interval_minutes'),
                    max_retries=agent_data.get('max_retries', 3),
                    timeout_seconds=agent_data.get('timeout_seconds', 30),
                    config=agent_data.get('config', {})
                )
                
        except Exception as e:
            logger.error(f"Failed to load agent configuration: {e}")
            # Create default configuration
            self._create_default_configuration()

    def _create_default_configuration(self) -> None:
        """Create default agent configuration."""
        default_agents = {
            'linkedin_collector': AgentConfig('linkedin_collector', enabled=False),
            'news_api_collector': AgentConfig('news_api_collector', enabled=False),
            'reddit_collector': AgentConfig('reddit_collector', enabled=False),
            'earnings_collector': AgentConfig('earnings_collector', enabled=True),
            'sentiment_analyzer': AgentConfig('sentiment_analyzer', enabled=True),
            'competitor_analyzer': AgentConfig('competitor_analyzer', enabled=True),
            'trend_analyzer': AgentConfig('trend_analyzer', enabled=True),
            'linkedin_publisher': AgentConfig('linkedin_publisher', enabled=False),
            'slack_notifier': AgentConfig('slack_notifier', enabled=False)
        }
        self.agent_configs = default_agents

    def _initialize_agents(self) -> None:
        """Initialize all configured agents."""
        for agent_name, config in self.agent_configs.items():
            try:
                agent = self._create_agent(agent_name, config)
                if agent:
                    self.agents[agent_name] = agent
                    logger.info(f"Initialized agent: {agent_name}")
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_name}: {e}")

    def _create_agent(self, agent_name: str, config: AgentConfig) -> Optional[BaseAgent]:
        """Create an agent instance based on its name and configuration."""
        
        # Data collection agents
        if agent_name == 'linkedin_collector':
            return LinkedInAgent(config, self.companies, self.shutdown_event)
        elif agent_name == 'news_api_collector':
            return NewsAPIAgent(config, self.companies, self.shutdown_event)
        elif agent_name == 'reddit_collector':
            return RedditAgent(config, self.companies, self.shutdown_event)
        elif agent_name == 'earnings_collector':
            return EarningsAgent(config, self.companies, self.shutdown_event)
            
        # Processing agents
        elif agent_name == 'sentiment_analyzer':
            return SentimentAgent(config, self.shutdown_event)
        elif agent_name == 'competitor_analyzer':
            company_names = [company.name for company in self.companies]
            return CompetitorAgent(config, company_names, self.shutdown_event)
        elif agent_name == 'trend_analyzer':
            return TrendAgent(config, self.shutdown_event)
            
        # Publishing agents
        elif agent_name == 'linkedin_publisher':
            return LinkedInPublisher(config, self.shutdown_event)
        elif agent_name == 'slack_notifier':
            return SlackAgent(config, self.shutdown_event)
            
        else:
            logger.warning(f"Unknown agent type: {agent_name}")
            return None

    async def execute_agent(self, agent_name: str, data: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Execute a specific agent.

        Args:
            agent_name: Name of the agent to execute.
            data: Optional data to pass to the agent.

        Returns:
            AgentResult from the execution.
        """
        if agent_name not in self.agents:
            return AgentResult(
                agent_name=agent_name,
                success=False,
                error=f"Agent {agent_name} not found"
            )

        agent = self.agents[agent_name]
        
        # Pass data to agent config if provided
        if data:
            agent.config.config.update(data)

        result = await agent.run_with_retry()
        self.execution_history.append(result)
        
        # Save agent state after execution
        self._save_agent_state(agent_name)
        
        # Keep only last max_history_size results to prevent memory leaks
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
            
        return result

    async def execute_data_collection_pipeline(self) -> Dict[str, AgentResult]:
        """Execute all data collection agents."""
        collection_agents = ['linkedin_collector', 'news_api_collector', 'reddit_collector', 'earnings_collector']
        
        # Execute collection agents in parallel
        tasks = []
        for agent_name in collection_agents:
            if agent_name in self.agents and self.agents[agent_name].config.enabled:
                tasks.append(self.execute_agent(agent_name))
        
        if not tasks:
            logger.warning("No data collection agents enabled")
            return {}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        all_transcripts = []
        
        for i, result in enumerate(results):
            agent_name = collection_agents[i] if i < len(collection_agents) else f"unknown_{i}"
            
            if isinstance(result, Exception):
                combined_results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    success=False,
                    error=str(result)
                )
            else:
                combined_results[agent_name] = result
                if result.success and result.data:
                    all_transcripts.extend(result.data)
        
        # Store combined transcripts for processing agents
        self._store_transcripts(all_transcripts)
        
        logger.info(f"Data collection completed. Collected {len(all_transcripts)} total transcripts")
        return combined_results

    async def execute_processing_pipeline(self, transcripts: List[Any]) -> Dict[str, AgentResult]:
        """Execute all processing agents on collected data."""
        processing_agents = ['sentiment_analyzer', 'competitor_analyzer', 'trend_analyzer']
        
        # Execute processing agents in parallel
        tasks = []
        for agent_name in processing_agents:
            if agent_name in self.agents and self.agents[agent_name].config.enabled:
                tasks.append(self.execute_agent(agent_name, {'transcripts': transcripts}))
        
        if not tasks:
            logger.warning("No processing agents enabled")
            return {}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        for i, result in enumerate(results):
            agent_name = processing_agents[i] if i < len(processing_agents) else f"unknown_{i}"
            
            if isinstance(result, Exception):
                combined_results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    success=False,
                    error=str(result)
                )
            else:
                combined_results[agent_name] = result
        
        logger.info(f"Processing pipeline completed for {len(transcripts)} transcripts")
        return combined_results

    async def execute_publishing_pipeline(self, articles: List[Any], summary_data: Dict[str, Any]) -> Dict[str, AgentResult]:
        """Execute all publishing agents."""
        publishing_agents = ['linkedin_publisher', 'slack_notifier']
        
        # Prepare data for each agent
        agent_data = {
            'linkedin_publisher': {'articles': articles},
            'slack_notifier': {
                'notification_type': 'daily_summary',
                'notification_data': summary_data
            }
        }
        
        # Execute publishing agents
        tasks = []
        for agent_name in publishing_agents:
            if agent_name in self.agents and self.agents[agent_name].config.enabled:
                data = agent_data.get(agent_name, {})
                tasks.append(self.execute_agent(agent_name, data))
        
        if not tasks:
            logger.warning("No publishing agents enabled")
            return {}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = {}
        for i, result in enumerate(results):
            agent_name = publishing_agents[i] if i < len(publishing_agents) else f"unknown_{i}"
            
            if isinstance(result, Exception):
                combined_results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    success=False,
                    error=str(result)
                )
            else:
                combined_results[agent_name] = result
        
        logger.info("Publishing pipeline completed")
        return combined_results

    async def execute_full_pipeline(self) -> Dict[str, Any]:
        """Execute the complete agent pipeline."""
        pipeline_start = time.time()
        
        logger.info("Starting full agent pipeline execution")
        
        # Step 1: Data Collection
        collection_results = await self.execute_data_collection_pipeline()
        
        # Get all collected transcripts
        all_transcripts = []
        for result in collection_results.values():
            if result.success and result.data:
                all_transcripts.extend(result.data)
        
        if not all_transcripts:
            logger.warning("No transcripts collected, skipping processing and publishing")
            return {
                'collection_results': collection_results,
                'processing_results': {},
                'publishing_results': {},
                'summary': {'total_transcripts': 0, 'execution_time': time.time() - pipeline_start}
            }
        
        # Step 2: Processing
        processing_results = await self.execute_processing_pipeline(all_transcripts)
        
        # Step 3: Publishing (placeholder - in real implementation, articles would be generated)
        summary_data = {
            'stats': {
                'transcripts_collected': len(all_transcripts),
                'companies_analyzed': len(set(t.company for t in all_transcripts)),
                'sources': list(set(t.source_type for t in all_transcripts))
            },
            'top_trends': ['AI adoption', 'Supply chain optimization', 'Consumer behavior shifts']
        }
        
        publishing_results = await self.execute_publishing_pipeline([], summary_data)
        
        execution_time = time.time() - pipeline_start
        
        logger.info(f"Full pipeline completed in {execution_time:.2f} seconds")
        
        return {
            'collection_results': collection_results,
            'processing_results': processing_results,
            'publishing_results': publishing_results,
            'summary': {
                'total_transcripts': len(all_transcripts),
                'execution_time': execution_time,
                'completed_at': datetime.now().isoformat()
            }
        }

    def _store_transcripts(self, transcripts: List[Any]) -> None:
        """Store transcripts for later use (placeholder for database storage)."""
        # In a real implementation, this would store transcripts in the database
        logger.info(f"Stored {len(transcripts)} transcripts")

    def get_agent_status(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of agents.

        Args:
            agent_name: Specific agent name, or None for all agents.

        Returns:
            Dictionary with agent status information.
        """
        if agent_name:
            if agent_name in self.agents:
                return self.agents[agent_name].get_status()
            else:
                return {'error': f'Agent {agent_name} not found'}
        else:
            return {agent_name: agent.get_status() for agent_name, agent in self.agents.items()}

    def get_execution_history(self, agent_name: Optional[str] = None, limit: int = 100) -> List[AgentResult]:
        """Get execution history for agents.

        Args:
            agent_name: Specific agent name, or None for all agents.
            limit: Maximum number of results to return.

        Returns:
            List of AgentResult objects.
        """
        history = self.execution_history
        
        if agent_name:
            history = [result for result in history if result.agent_name == agent_name]
        
        return history[-limit:] if len(history) > limit else history

    def enable_agent(self, agent_name: str) -> bool:
        """Enable an agent.

        Args:
            agent_name: Name of the agent to enable.

        Returns:
            True if successful, False otherwise.
        """
        if agent_name in self.agents:
            self.agents[agent_name].config.enabled = True
            logger.info(f"Enabled agent: {agent_name}")
            return True
        return False

    def disable_agent(self, agent_name: str) -> bool:
        """Disable an agent.

        Args:
            agent_name: Name of the agent to disable.

        Returns:
            True if successful, False otherwise.
        """
        if agent_name in self.agents:
            self.agents[agent_name].config.enabled = False
            logger.info(f"Disabled agent: {agent_name}")
            return True
        return False

    def cleanup_old_history(self, max_age_hours: int = 24) -> int:
        """Clean up old execution history to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age of history entries in hours.
            
        Returns:
            Number of entries removed.
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        initial_count = len(self.execution_history)
        
        # Remove old entries
        self.execution_history = [
            result for result in self.execution_history 
            if result.timestamp and result.timestamp > cutoff_time
        ]
        
        removed_count = initial_count - len(self.execution_history)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old execution history entries")
        
        return removed_count

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information.
        
        Returns:
            Dictionary with memory usage details.
        """
        import sys
        
        return {
            'execution_history_size': len(self.execution_history),
            'max_history_size': self.max_history_size,
            'agents_count': len(self.agents),
            'agent_configs_count': len(self.agent_configs),
            'companies_count': len(self.companies),
            'estimated_memory_mb': sys.getsizeof(self.execution_history) / (1024 * 1024)
        }

    def shutdown(self) -> None:
        """Shutdown the agent manager and cleanup resources."""
        logger.info("Shutting down agent manager...")
        
        # Clean up old history
        self.cleanup_old_history()
        
        # Clear large data structures
        self.execution_history.clear()
        self.companies.clear()
        
        # Disable all agents
        for agent_name in list(self.agents.keys()):
            self.disable_agent(agent_name)
        
        logger.info("Agent manager shutdown complete")

    def set_database_manager(self, db_manager) -> None:
        """Set the database manager for state persistence.
        
        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    def _load_agent_states(self) -> None:
        """Load agent states from database on startup."""
        if not self.db_manager:
            logger.warning("No database manager available for state loading")
            return
        
        try:
            for agent_name in self.agents.keys():
                state = self.db_manager.get_agent_state(agent_name)
                if state:
                    # Restore agent state
                    if 'last_execution' in state and state['last_execution']:
                        from datetime import datetime
                        self.agents[agent_name].last_execution = datetime.fromisoformat(state['last_execution'])
                    
                    if 'execution_count' in state:
                        self.agents[agent_name].execution_count = state['execution_count']
                    
                    if 'error_count' in state:
                        self.agents[agent_name].error_count = state['error_count']
                    
                    logger.info(f"Restored state for agent: {agent_name}")
        except Exception as e:
            logger.error(f"Failed to load agent states: {e}")

    def _save_agent_state(self, agent_name: str) -> None:
        """Save agent state to database.
        
        Args:
            agent_name: Name of the agent to save state for.
        """
        if not self.db_manager or agent_name not in self.agents:
            return
        
        try:
            agent = self.agents[agent_name]
            state = {
                'last_execution': agent.last_execution.isoformat() if agent.last_execution else None,
                'execution_count': agent.execution_count,
                'error_count': agent.error_count,
                'is_running': agent.is_running,
                'enabled': agent.config.enabled
            }
            self.db_manager.save_agent_state(agent_name, state)
        except Exception as e:
            logger.error(f"Failed to save state for agent {agent_name}: {e}")

    def _save_all_agent_states(self) -> None:
        """Save states for all agents."""
        for agent_name in self.agents.keys():
            self._save_agent_state(agent_name)

    def recover_from_crash(self) -> Dict[str, Any]:
        """Recover from a crash by checking for incomplete operations.
        
        Returns:
            Dictionary with recovery information.
        """
        recovery_info = {
            'incomplete_operations': [],
            'recovered_agents': [],
            'errors': []
        }
        
        if not self.db_manager:
            recovery_info['errors'].append("No database manager available for recovery")
            return recovery_info
        
        try:
            # Check for agents that were running when the crash occurred
            for agent_name, agent in self.agents.items():
                state = self.db_manager.get_agent_state(agent_name)
                if state and state.get('is_running', False):
                    recovery_info['incomplete_operations'].append(agent_name)
                    # Reset running state
                    agent.is_running = False
                    recovery_info['recovered_agents'].append(agent_name)
            
            # Clean up any stale data
            self.cleanup_old_history(max_age_hours=1)  # Clean up very old data
            
            logger.info(f"Recovery completed: {len(recovery_info['recovered_agents'])} agents recovered")
            
        except Exception as e:
            error_msg = f"Recovery failed: {e}"
            logger.error(error_msg)
            recovery_info['errors'].append(error_msg)
        
        return recovery_info

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status.
        
        Returns:
            Dictionary with system status information.
        """
        status = {
            'agents': {},
            'execution_history_size': len(self.execution_history),
            'memory_usage': self.get_memory_usage(),
            'database_connected': self.db_manager is not None and self.db_manager.is_healthy() if self.db_manager else False
        }
        
        for agent_name, agent in self.agents.items():
            status['agents'][agent_name] = {
                'enabled': agent.config.enabled,
                'is_running': agent.is_running,
                'last_execution': agent.last_execution.isoformat() if agent.last_execution else None,
                'execution_count': agent.execution_count,
                'error_count': agent.error_count
            }
        
        return status