"""TrajectoryStore - SQLite storage for execution trajectories.

Stores complete execution logs for analysis and self-improvement.
"""

import json
import sqlite3
import time
from typing import Any, Dict, List, Optional


class TrajectoryStore:
    """Stores full execution trajectories for analysis.

    This store captures complete execution logs including:
    - Every prompt sent to the LLM
    - Every response received
    - Every tool call and result
    - Every extracted answer
    - Human follow-up actions
    """

    def __init__(self, db_path: str = "semar_trajectories.db"):
        """Initialize the trajectory store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trajectories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    pr_url TEXT NOT NULL,
                    language TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    plan JSON,
                    action_result JSON,
                    review JSON,
                    metrics JSON,
                    full_trajectory JSON,
                    created_at FLOAT DEFAULT (strftime('%s','now'))
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_id ON trajectories(agent_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pr_url ON trajectories(pr_url)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON trajectories(timestamp)
            """)

            conn.commit()

    async def store(
        self,
        agent_id: str,
        pr_url: str,
        language: str,
        plan: Dict,
        action_result: Any,
        review: Dict,
        metrics: Dict,
        full_trajectory: Dict,
    ) -> int:
        """Store a complete execution trajectory.

        Args:
            agent_id: Identifier of the agent
            pr_url: URL of the PR being reviewed
            language: Programming language of the PR
            plan: Execution plan from plan() step
            action_result: Result from action() step
            review: Review result from review() step
            metrics: Performance metrics
            full_trajectory: Complete execution trajectory

        Returns:
            ID of the stored trajectory
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO trajectories 
                (agent_id, pr_url, language, plan, action_result, review, metrics, full_trajectory)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    agent_id,
                    pr_url,
                    language,
                    json.dumps(plan),
                    json.dumps(action_result) if action_result else None,
                    json.dumps(review),
                    json.dumps(metrics),
                    json.dumps(full_trajectory),
                ),
            )
            conn.commit()
            row_id = cursor.lastrowid
            if row_id is None:
                raise RuntimeError("Failed to store trajectory: no row ID returned")
            return row_id

    async def get_trajectories(
        self,
        agent_id: Optional[str] = None,
        pr_url: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """Retrieve trajectories with optional filters.

        Args:
            agent_id: Filter by agent ID
            pr_url: Filter by PR URL
            language: Filter by language
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of trajectory dictionaries
        """
        query = "SELECT * FROM trajectories WHERE 1=1"
        params = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        if pr_url:
            query += " AND pr_url = ?"
            params.append(pr_url)
        if language:
            query += " AND language = ?"
            params.append(language)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    async def get_trajectory_by_id(self, trajectory_id: int) -> Optional[Dict]:
        """Get a specific trajectory by ID.

        Args:
            trajectory_id: ID of the trajectory

        Returns:
            Trajectory dictionary or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM trajectories WHERE id = ?", (trajectory_id,)).fetchone()
            return dict(row) if row else None

    async def delete_trajectory(self, trajectory_id: int) -> bool:
        """Delete a specific trajectory.

        Args:
            trajectory_id: ID of the trajectory to delete

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM trajectories WHERE id = ?", (trajectory_id,))
            conn.commit()
            return cursor.rowcount > 0

    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for a specific agent.

        Args:
            agent_id: Agent to get stats for

        Returns:
            Statistics dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Total reviews
            total = conn.execute(
                "SELECT COUNT(*) as count FROM trajectories WHERE agent_id = ?", (agent_id,)
            ).fetchone()["count"]

            # Reviews by language
            by_language = conn.execute(
                "SELECT language, COUNT(*) as count FROM trajectories WHERE agent_id = ? GROUP BY language", (agent_id,)
            ).fetchall()

            # Recent activity
            recent = conn.execute(
                "SELECT * FROM trajectories WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 10", (agent_id,)
            ).fetchall()

            return {
                "agent_id": agent_id,
                "total_reviews": total,
                "by_language": {row["language"]: row["count"] for row in by_language},
                "recent_reviews": [dict(row) for row in recent],
            }

    async def get_recent_trajectories(self, limit: int = 10) -> List[Dict]:
        """Get most recent trajectories across all agents.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent trajectory dictionaries
        """
        return await self.get_trajectories(limit=limit)

    async def clear_old_trajectories(self, days: int = 30) -> int:
        """Clear trajectories older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted trajectories
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM trajectories WHERE created_at < ?", (cutoff_time,))
            conn.commit()
            return cursor.rowcount

    def close(self):
        """Close database connection."""
        # SQLite connections are closed automatically in context managers
        pass
