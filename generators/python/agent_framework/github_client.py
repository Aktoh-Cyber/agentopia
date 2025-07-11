"""
GitHub MCP Client for committing generated agents
"""

import base64
import json
from datetime import datetime
from typing import Any, Optional

from js import Object
from js import fetch as js_fetch
from pyodide.ffi import to_js


class GitHubMCPClient:
    """Client for interacting with GitHub via MCP server"""

    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"

    def _to_js(self, obj):
        """Convert Python object to JavaScript object"""
        return to_js(obj, dict_converter=Object.fromEntries)

    async def _github_request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> dict:
        """Make authenticated request to GitHub API"""
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

        request_options = {"method": method, "headers": self._to_js(headers)}

        if data:
            request_options["body"] = json.dumps(data)

        response = await js_fetch(url, self._to_js(request_options))

        if not response.ok:
            error_text = await response.text()
            raise Exception(f"GitHub API request failed: {response.status} - {error_text}")

        response_data = await response.json()
        return response_data

    async def get_default_branch(self) -> str:
        """Get the default branch of the repository"""
        repo_data = await self._github_request("GET", f"/repos/{self.repo_owner}/{self.repo_name}")
        return repo_data["default_branch"]

    async def get_branch_sha(self, branch: str) -> str:
        """Get the SHA of a branch"""
        ref_data = await self._github_request(
            "GET", f"/repos/{self.repo_owner}/{self.repo_name}/git/refs/heads/{branch}"
        )
        return ref_data["object"]["sha"]

    async def create_branch(self, branch_name: str, base_branch: str = None) -> str:
        """Create a new branch"""
        if base_branch is None:
            base_branch = await self.get_default_branch()

        base_sha = await self.get_branch_sha(base_branch)

        branch_data = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}

        try:
            await self._github_request(
                "POST", f"/repos/{self.repo_owner}/{self.repo_name}/git/refs", branch_data
            )
            return branch_name
        except Exception as e:
            if "already exists" in str(e):
                # Branch already exists, continue
                return branch_name
            raise

    async def get_file_content(self, file_path: str, branch: str = None) -> Optional[dict]:
        """Get existing file content and SHA"""
        if branch is None:
            branch = await self.get_default_branch()

        try:
            file_data = await self._github_request(
                "GET",
                f"/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}?ref={branch}",
            )
            return {
                "content": base64.b64decode(file_data["content"]).decode("utf-8"),
                "sha": file_data["sha"],
            }
        except Exception:
            return None  # File doesn't exist

    async def commit_files(
        self, files: list[dict[str, str]], branch: str, commit_message: str
    ) -> str:
        """Commit multiple files to a branch

        Args:
            files: List of dicts with 'path' and 'content' keys
            branch: Target branch name
            commit_message: Commit message

        Returns:
            Commit SHA
        """
        # Get current commit SHA for the branch
        branch_sha = await self.get_branch_sha(branch)

        # Get the current tree
        commit_data = await self._github_request(
            "GET", f"/repos/{self.repo_owner}/{self.repo_name}/git/commits/{branch_sha}"
        )
        base_tree_sha = commit_data["tree"]["sha"]

        # Create tree entries for all files
        tree_entries = []

        for file_info in files:
            file_path = file_info["path"]
            file_content = file_info["content"]

            # Create blob for file content
            blob_data = {
                "content": base64.b64encode(file_content.encode("utf-8")).decode("utf-8"),
                "encoding": "base64",
            }

            blob_response = await self._github_request(
                "POST", f"/repos/{self.repo_owner}/{self.repo_name}/git/blobs", blob_data
            )
            blob_sha = blob_response["sha"]

            tree_entries.append(
                {"path": file_path, "mode": "100644", "type": "blob", "sha": blob_sha}
            )

        # Create new tree
        tree_data = {"base_tree": base_tree_sha, "tree": tree_entries}

        tree_response = await self._github_request(
            "POST", f"/repos/{self.repo_owner}/{self.repo_name}/git/trees", tree_data
        )
        tree_sha = tree_response["sha"]

        # Create commit
        commit_data = {"message": commit_message, "tree": tree_sha, "parents": [branch_sha]}

        commit_response = await self._github_request(
            "POST", f"/repos/{self.repo_owner}/{self.repo_name}/git/commits", commit_data
        )
        commit_sha = commit_response["sha"]

        # Update branch to point to new commit
        update_data = {"sha": commit_sha, "force": False}

        await self._github_request(
            "PATCH",
            f"/repos/{self.repo_owner}/{self.repo_name}/git/refs/heads/{branch}",
            update_data,
        )

        return commit_sha

    async def create_pull_request(
        self, branch: str, title: str, body: str, base_branch: str = None
    ) -> str:
        """Create a pull request

        Returns:
            Pull request URL
        """
        if base_branch is None:
            base_branch = await self.get_default_branch()

        pr_data = {"title": title, "body": body, "head": branch, "base": base_branch}

        pr_response = await self._github_request(
            "POST", f"/repos/{self.repo_owner}/{self.repo_name}/pulls", pr_data
        )
        return pr_response["html_url"]

    async def generate_agent_branch_name(self, agent_name: str) -> str:
        """Generate a unique branch name for an agent"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in agent_name.lower())
        return f"agent/{safe_name}-{timestamp}"

    async def commit_agent(
        self,
        agent_config: dict[str, Any],
        generated_files: dict[str, str],
        language: str = "python",
    ) -> dict[str, str]:
        """Complete workflow to commit a generated agent

        Args:
            agent_config: Agent configuration dict
            generated_files: Dict mapping file paths to content
            language: "python" or "javascript"

        Returns:
            Dict with branch_name, commit_sha, and pr_url
        """
        agent_name = agent_config["name"]
        agent_type = agent_config["type"]

        # Generate branch name
        branch_name = await self.generate_agent_branch_name(agent_name)

        # Create branch
        await self.create_branch(branch_name)

        # Determine agent directory
        agent_dir_name = agent_config.get("domain", agent_name).split(".")[0].lower()
        agent_type_dir = f"{agent_type}-agents"
        agent_path = f"generated-agents/{agent_type_dir}/{agent_dir_name}"

        # Prepare files with full paths
        files_to_commit = []
        for relative_path, content in generated_files.items():
            full_path = f"{agent_path}/{relative_path}"
            files_to_commit.append({"path": full_path, "content": content})

        # Create commit message
        commit_message = f"Generate {language.title()} {agent_type} agent: {agent_name}\n\nAuto-generated agent with the following features:\n- Domain: {agent_config.get('domain', 'N/A')}\n- Language: {language.title()}\n- Type: {agent_type.title()}\n- Generated at: {datetime.now().isoformat()}"

        # Commit files
        commit_sha = await self.commit_files(files_to_commit, branch_name, commit_message)

        # Create pull request
        pr_title = f"🤖 Add {language.title()} {agent_type} agent: {agent_name}"
        pr_body = f"""## 🚀 New Agent Generated

**Agent Details:**
- **Name:** {agent_name}
- **Type:** {agent_type.title()} Agent
- **Language:** {language.title()}
- **Domain:** {agent_config.get('domain', 'N/A')}
- **Description:** {agent_config.get('description', 'N/A')}

**Generated Files:**
{chr(10).join(f'- `{path}`' for path in generated_files.keys())}

**Deployment:**
This PR will automatically trigger validation and deployment workflows when merged.

**Review Checklist:**
- [ ] Agent configuration is correct
- [ ] Domain settings are appropriate
- [ ] Generated code follows framework patterns
- [ ] Deployment settings are valid

---
*Auto-generated by Agent Generator 🏭*"""

        pr_url = await self.create_pull_request(branch_name, pr_title, pr_body)

        return {
            "branch_name": branch_name,
            "commit_sha": commit_sha,
            "pr_url": pr_url,
            "agent_path": agent_path,
        }
