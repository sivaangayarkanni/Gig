"""
Supervisor client for managing the openclaw gateway process.

This module provides a clean interface for starting, stopping, and
checking the status of the gateway process managed by supervisord.
"""

import subprocess
import logging
import shutil

logger = logging.getLogger(__name__)

# Check if supervisorctl is available
_SUPERVISOR_AVAILABLE = shutil.which('supervisorctl') is not None
if not _SUPERVISOR_AVAILABLE:
    logger.warning("supervisorctl not found - gateway management disabled")


class SupervisorClient:
    """Client for interacting with supervisord to manage the gateway process."""

    PROGRAM = "openclaw-gateway"

    @classmethod
    def _run(cls, *args, timeout=10):
        """Run a supervisorctl command. Returns subprocess.CompletedProcess or None."""
        if not _SUPERVISOR_AVAILABLE:
            return None
        try:
            return subprocess.run(
                ['supervisorctl'] + list(args),
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except Exception as e:
            logger.debug(f"supervisorctl {args[0]} failed: {e}")
            return None

    @classmethod
    def start(cls) -> bool:
        result = cls._run('start', cls.PROGRAM, timeout=30)
        if result and result.returncode == 0:
            logger.info(f"Started {cls.PROGRAM} via supervisor")
            return True
        return False

    @classmethod
    def stop(cls) -> bool:
        result = cls._run('stop', cls.PROGRAM, timeout=30)
        if result and (result.returncode == 0 or 'NOT RUNNING' in result.stdout):
            logger.info(f"Stopped {cls.PROGRAM} via supervisor")
            return True
        return False

    @classmethod
    def status(cls) -> bool:
        result = cls._run('status', cls.PROGRAM)
        if result:
            return 'RUNNING' in result.stdout
        return False

    @classmethod
    def get_pid(cls) -> int | None:
        result = cls._run('status', cls.PROGRAM)
        if result and 'RUNNING' in result.stdout and 'pid' in result.stdout:
            parts = result.stdout.split('pid')
            if len(parts) > 1:
                try:
                    return int(parts[1].strip().split(',')[0].strip())
                except ValueError:
                    pass
        return None

    @classmethod
    def restart(cls) -> bool:
        result = cls._run('restart', cls.PROGRAM, timeout=30)
        if result and result.returncode == 0:
            logger.info(f"Restarted {cls.PROGRAM} via supervisor")
            return True
        return False

    @classmethod
    def reload_config(cls) -> bool:
        reread = cls._run('reread')
        if not reread or reread.returncode != 0:
            return False
        update = cls._run('update')
        if not update or update.returncode != 0:
            return False
        logger.info("Supervisor configuration reloaded")
        return True
