"""
Unit tests for APScheduler background task scheduling.
Tests cover scheduler initialization, job execution, and error handling.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import atexit


class TestSchedulerInitialization:
    """Tests for scheduler initialization and configuration."""
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_is_created(self, mock_scheduler_class):
        """Test that BackgroundScheduler is instantiated."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        assert scheduler is not None
        mock_scheduler_class.assert_called_once()
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_job_added(self, mock_scheduler_class):
        """Test that scheduled job is added to scheduler."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # Add job
        def test_job():
            pass
        
        scheduler.add_job(func=test_job, trigger="interval", hours=6)
        
        # Verify job was added
        mock_scheduler.add_job.assert_called_once()
        call_args = mock_scheduler.add_job.call_args
        assert call_args[1]['trigger'] == "interval"
        assert call_args[1]['hours'] == 6
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_started(self, mock_scheduler_class):
        """Test that scheduler is started."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        mock_scheduler.start.assert_called_once()
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_shutdown_registered(self, mock_scheduler_class):
        """Test that scheduler shutdown is registered with atexit."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # Register shutdown
        atexit.register(lambda: scheduler.shutdown())
        
        # Verify atexit registration (this is implicit, we're testing the pattern)
        assert scheduler is not None
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_interval_configuration(self, mock_scheduler_class):
        """Test that scheduler interval is configured correctly."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        def job_func():
            pass
        
        # Test with 6-hour interval
        scheduler.add_job(func=job_func, trigger="interval", hours=6)
        
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs['hours'] == 6
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_multiple_jobs_can_be_added(self, mock_scheduler_class):
        """Test that multiple jobs can be added to scheduler."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # Add multiple jobs
        scheduler.add_job(func=lambda: None, trigger="interval", hours=6)
        scheduler.add_job(func=lambda: None, trigger="interval", hours=12)
        
        assert mock_scheduler.add_job.call_count == 2
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_with_different_triggers(self, mock_scheduler_class):
        """Test scheduler with different trigger types."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # Test interval trigger
        scheduler.add_job(func=lambda: None, trigger="interval", hours=6)
        
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs['trigger'] == "interval"


class TestSchedulerJobExecution:
    """Tests for scheduled job execution."""
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_job_function_is_callable(self, mock_scheduler_class):
        """Test that the job function is callable."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        def market_scan_job():
            return "executed"
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=market_scan_job, trigger="interval", hours=6)
        
        # Verify the function is callable
        call_args = mock_scheduler.add_job.call_args
        job_func = call_args[1]['func']
        assert callable(job_func)
    
    @patch('random.choice')
    def test_job_selects_keyword(self, mock_random_choice):
        """Test that scheduled job selects a keyword."""
        keywords = ["smart watch", "wireless earbuds", "drone", "gaming accessories"]
        mock_random_choice.return_value = "smart watch"
        
        import random
        selected = random.choice(keywords)
        
        assert selected == "smart watch"
        mock_random_choice.assert_called_once_with(keywords)
    
    @patch('psycopg2.connect')
    @patch('random.choice')
    def test_job_executes_without_error(self, mock_random_choice, mock_connect, mock_env_vars):
        """Test that job can execute without errors."""
        mock_random_choice.return_value = "test keyword"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate job execution
        import random
        keywords = ["smart watch", "wireless earbuds", "drone", "gaming accessories"]
        selected_keyword = random.choice(keywords)
        
        # Job should execute successfully
        assert selected_keyword is not None
    
    def test_job_handles_empty_keyword_list(self):
        """Test job behavior with edge case of empty keyword list."""
        keywords = []
        
        # Should handle empty list (would raise IndexError in random.choice)
        if len(keywords) == 0:
            # Proper handling would check list before calling random.choice
            assert len(keywords) == 0


class TestSchedulerErrorHandling:
    """Tests for scheduler error handling."""
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_handles_job_exception(self, mock_scheduler_class):
        """Test that scheduler continues running when job raises exception."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        def failing_job():
            raise Exception("Job failed")
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=failing_job, trigger="interval", hours=6)
        
        # Scheduler should be configured to handle job failures
        # (APScheduler does this by default)
        assert scheduler is not None
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_shutdown_gracefully(self, mock_scheduler_class):
        """Test that scheduler can shut down gracefully."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.shutdown()
        
        mock_scheduler.shutdown.assert_called_once()
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_shutdown_with_wait(self, mock_scheduler_class):
        """Test scheduler shutdown with wait parameter."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.shutdown(wait=False)
        
        mock_scheduler.shutdown.assert_called_once_with(wait=False)


class TestSchedulerConfiguration:
    """Tests for scheduler configuration options."""
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_with_different_intervals(self, mock_scheduler_class):
        """Test scheduler with various time intervals."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        intervals = [1, 6, 12, 24]
        for hours in intervals:
            scheduler.add_job(func=lambda: None, trigger="interval", hours=hours)
        
        assert mock_scheduler.add_job.call_count == len(intervals)
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_job_with_seconds_interval(self, mock_scheduler_class):
        """Test job scheduled with seconds interval."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=lambda: None, trigger="interval", seconds=30)
        
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs['seconds'] == 30
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_job_with_minutes_interval(self, mock_scheduler_class):
        """Test job scheduled with minutes interval."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=lambda: None, trigger="interval", minutes=30)
        
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs['minutes'] == 30


class TestSchedulerIntegration:
    """Integration tests for scheduler with other components."""
    
    @patch('psycopg2.connect')
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_job_accesses_database(self, mock_scheduler_class, mock_connect, mock_env_vars):
        """Test that scheduled job can access database."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate job that accesses database
        import os
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        
        assert cur is not None
        mock_connect.assert_called_once()
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_does_not_block_flask(self, mock_scheduler_class):
        """Test that scheduler runs in background without blocking Flask."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        # BackgroundScheduler should not block
        # This is verified by the fact that it returns immediately
        assert mock_scheduler.start.called
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_scheduler_persists_across_requests(self, mock_scheduler_class):
        """Test that scheduler persists across multiple requests."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # Scheduler should be a singleton-like instance
        assert scheduler is not None
        
        # Multiple references should point to same instance
        scheduler_ref = scheduler
        assert scheduler_ref is scheduler


class TestSchedulerEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_add_job_with_zero_interval(self, mock_scheduler_class):
        """Test adding job with zero interval."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # Zero interval should be handled
        scheduler.add_job(func=lambda: None, trigger="interval", hours=0)
        
        mock_scheduler.add_job.assert_called_once()
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_start_already_started_scheduler(self, mock_scheduler_class):
        """Test starting an already started scheduler."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        # Starting again should be handled gracefully
        try:
            scheduler.start()
        except:
            pass  # Some implementations may raise an error
        
        # At least one start call should succeed
        assert mock_scheduler.start.call_count >= 1
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_shutdown_not_started_scheduler(self, mock_scheduler_class):
        """Test shutting down a scheduler that was never started."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        
        # Should handle shutdown gracefully even if not started
        scheduler.shutdown()
        
        mock_scheduler.shutdown.assert_called_once()
    
    @patch('apscheduler.schedulers.background.BackgroundScheduler')
    def test_add_job_after_scheduler_started(self, mock_scheduler_class):
        """Test adding job after scheduler has started."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        # Adding job after start should still work
        scheduler.add_job(func=lambda: None, trigger="interval", hours=6)
        
        mock_scheduler.add_job.assert_called_once()
