"""
Crypto Sentiment Dashboard - GitHub Development Tracker

Tracks development activity for cryptocurrency projects.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from app.utils.cache import cached
from app.utils.rate_limiter import get_rate_limiters, setup_default_limiters

logger = logging.getLogger(__name__)

# Ensure rate limiters are set up
setup_default_limiters()


class GitHubTracker:
    """
    Tracks GitHub development activity for crypto projects.

    Development activity is a key indicator of project health.
    Active development often correlates with long-term success.
    """

    BASE_URL = 'https://api.github.com'

    # Major crypto project repositories
    REPOSITORIES = {
        'bitcoin': {
            'owner': 'bitcoin',
            'repo': 'bitcoin',
            'name': 'Bitcoin Core',
            'coin_id': 'bitcoin'
        },
        'ethereum': {
            'owner': 'ethereum',
            'repo': 'go-ethereum',
            'name': 'Go Ethereum (Geth)',
            'coin_id': 'ethereum'
        },
        'solana': {
            'owner': 'solana-labs',
            'repo': 'solana',
            'name': 'Solana',
            'coin_id': 'solana'
        },
        'cardano': {
            'owner': 'input-output-hk',
            'repo': 'cardano-node',
            'name': 'Cardano Node',
            'coin_id': 'cardano'
        },
        'polkadot': {
            'owner': 'paritytech',
            'repo': 'polkadot-sdk',
            'name': 'Polkadot SDK',
            'coin_id': 'polkadot'
        },
        'avalanche': {
            'owner': 'ava-labs',
            'repo': 'avalanchego',
            'name': 'AvalancheGo',
            'coin_id': 'avalanche-2'
        },
        'chainlink': {
            'owner': 'smartcontractkit',
            'repo': 'chainlink',
            'name': 'Chainlink',
            'coin_id': 'chainlink'
        },
        'uniswap': {
            'owner': 'Uniswap',
            'repo': 'v3-core',
            'name': 'Uniswap V3',
            'coin_id': 'uniswap'
        },
        'aave': {
            'owner': 'aave',
            'repo': 'aave-v3-core',
            'name': 'Aave V3',
            'coin_id': 'aave'
        },
        'cosmos': {
            'owner': 'cosmos',
            'repo': 'cosmos-sdk',
            'name': 'Cosmos SDK',
            'coin_id': 'cosmos'
        }
    }

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub tracker.

        Args:
            github_token: GitHub personal access token (optional, increases rate limit)
        """
        self.token = github_token or os.getenv('GITHUB_TOKEN')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'crypto-sentiment-dashboard/1.0'
        })
        if self.token:
            self.session.headers['Authorization'] = f'token {self.token}'

        self._rate_limiters = get_rate_limiters()
        # Add GitHub rate limiter if not exists
        try:
            self._rate_limiters.add('github', rate=60, per=3600)  # 60/hour unauthenticated
        except:
            pass

    def _request(self, endpoint: str) -> Optional[Dict]:
        """Make GitHub API request."""
        self._rate_limiters.acquire('github', blocking=True, timeout=30)

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                logger.warning("GitHub API rate limit exceeded")
            else:
                logger.error(f"GitHub API error: {response.status_code}")

            return None

        except requests.RequestException as e:
            logger.error(f"GitHub request failed: {e}")
            return None

    @cached(ttl=3600, key_prefix='github_repo_stats')
    def get_repo_stats(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Get repository statistics.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository statistics
        """
        # Get repository info
        repo_data = self._request(f"repos/{owner}/{repo}")
        if not repo_data:
            return None

        # Get recent commits
        commits_data = self._request(f"repos/{owner}/{repo}/commits?per_page=100")
        commits = commits_data if isinstance(commits_data, list) else []

        # Get contributors
        contributors_data = self._request(f"repos/{owner}/{repo}/contributors?per_page=30")
        contributors = contributors_data if isinstance(contributors_data, list) else []

        # Calculate commit frequency
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        commits_last_week = 0
        commits_last_month = 0

        for commit in commits:
            commit_date_str = commit.get('commit', {}).get('author', {}).get('date', '')
            if commit_date_str:
                try:
                    commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                    commit_date = commit_date.replace(tzinfo=None)
                    if commit_date >= week_ago:
                        commits_last_week += 1
                    if commit_date >= month_ago:
                        commits_last_month += 1
                except:
                    pass

        # Calculate activity score (0-100)
        activity_score = min(100, (
            (commits_last_week * 3) +
            (commits_last_month / 2) +
            (len(contributors) / 2) +
            (min(repo_data.get('stargazers_count', 0), 10000) / 200)
        ))

        return {
            'owner': owner,
            'repo': repo,
            'name': repo_data.get('name'),
            'description': repo_data.get('description'),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'open_issues': repo_data.get('open_issues_count', 0),
            'watchers': repo_data.get('watchers_count', 0),
            'language': repo_data.get('language'),
            'commits_last_week': commits_last_week,
            'commits_last_month': commits_last_month,
            'contributor_count': len(contributors),
            'top_contributors': [
                {
                    'login': c.get('login'),
                    'contributions': c.get('contributions'),
                    'avatar_url': c.get('avatar_url')
                }
                for c in contributors[:5]
            ],
            'activity_score': round(activity_score, 1),
            'activity_level': self._get_activity_level(activity_score),
            'last_updated': repo_data.get('updated_at'),
            'created_at': repo_data.get('created_at')
        }

    def _get_activity_level(self, score: float) -> str:
        """Classify activity level."""
        if score >= 80:
            return 'VERY_HIGH'
        elif score >= 60:
            return 'HIGH'
        elif score >= 40:
            return 'MODERATE'
        elif score >= 20:
            return 'LOW'
        return 'VERY_LOW'

    @cached(ttl=3600, key_prefix='github_overview')
    def get_development_overview(self) -> Dict:
        """
        Get development activity overview for all tracked projects.

        Returns:
            Development activity comparison
        """
        projects = []

        for project_id, project_info in self.REPOSITORIES.items():
            stats = self.get_repo_stats(project_info['owner'], project_info['repo'])

            if stats:
                projects.append({
                    'project_id': project_id,
                    'coin_id': project_info['coin_id'],
                    'name': project_info['name'],
                    'stars': stats['stars'],
                    'commits_last_week': stats['commits_last_week'],
                    'commits_last_month': stats['commits_last_month'],
                    'contributors': stats['contributor_count'],
                    'activity_score': stats['activity_score'],
                    'activity_level': stats['activity_level']
                })

        # Sort by activity score
        projects.sort(key=lambda x: x['activity_score'], reverse=True)

        # Calculate averages
        if projects:
            avg_activity = sum(p['activity_score'] for p in projects) / len(projects)
            avg_weekly_commits = sum(p['commits_last_week'] for p in projects) / len(projects)
        else:
            avg_activity = 0
            avg_weekly_commits = 0

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_projects': len(projects),
            'projects': projects,
            'summary': {
                'avg_activity_score': round(avg_activity, 1),
                'avg_weekly_commits': round(avg_weekly_commits, 1),
                'most_active': projects[0] if projects else None,
                'least_active': projects[-1] if projects else None
            },
            'note': 'High development activity often indicates strong project fundamentals.'
        }

    def get_project_activity(self, project_id: str) -> Optional[Dict]:
        """
        Get detailed activity for a specific project.

        Args:
            project_id: Project identifier

        Returns:
            Detailed project development stats
        """
        if project_id not in self.REPOSITORIES:
            return None

        project_info = self.REPOSITORIES[project_id]
        return self.get_repo_stats(project_info['owner'], project_info['repo'])

    @cached(ttl=3600, key_prefix='github_comparison')
    def compare_development(self, project_ids: List[str]) -> Dict:
        """
        Compare development activity between projects.

        Args:
            project_ids: List of project IDs to compare

        Returns:
            Comparison data
        """
        comparison = []

        for project_id in project_ids:
            if project_id in self.REPOSITORIES:
                project_info = self.REPOSITORIES[project_id]
                stats = self.get_repo_stats(project_info['owner'], project_info['repo'])

                if stats:
                    comparison.append({
                        'project_id': project_id,
                        'name': project_info['name'],
                        'coin_id': project_info['coin_id'],
                        'stats': {
                            'stars': stats['stars'],
                            'commits_week': stats['commits_last_week'],
                            'commits_month': stats['commits_last_month'],
                            'contributors': stats['contributor_count'],
                            'activity_score': stats['activity_score']
                        }
                    })

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'projects_compared': len(comparison),
            'comparison': comparison
        }


# Global tracker instance
_tracker: Optional[GitHubTracker] = None


def get_tracker(github_token: Optional[str] = None) -> GitHubTracker:
    """Get or create the global GitHub tracker."""
    global _tracker
    if _tracker is None:
        _tracker = GitHubTracker(github_token)
    return _tracker


# Convenience functions
def get_development_overview() -> Dict:
    """Get development activity overview."""
    return get_tracker().get_development_overview()


def get_project_activity(project_id: str) -> Optional[Dict]:
    """Get activity for a specific project."""
    return get_tracker().get_project_activity(project_id)


def compare_development(project_ids: List[str]) -> Dict:
    """Compare development between projects."""
    return get_tracker().compare_development(project_ids)
