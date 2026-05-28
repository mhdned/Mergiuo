import requests
from urllib.parse import quote

try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False


class GitLabMRCreator:
    def __init__(self, gitlab_url, token):
        self.gitlab_url = gitlab_url.rstrip('/')
        self.headers = {"PRIVATE-TOKEN": token}
        self.current_user_id = None

    def get_current_user(self):
        """Get current user information"""
        url = f"{self.gitlab_url}/api/v4/user"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        user = r.json()
        self.current_user_id = user['id']
        return user

    def get_all_projects(self):
        """Get all projects the user has access to"""
        projects = []
        page = 1
        per_page = 100

        while True:
            url = f"{self.gitlab_url}/api/v4/projects"
            params = {
                "membership": True,
                "per_page": per_page,
                "page": page,
                "simple": False
            }
            r = requests.get(url, headers=self.headers, params=params)
            r.raise_for_status()
            
            batch = r.json()
            if not batch:
                break
            
            projects.extend(batch)
            page += 1

        return projects

    def filter_projects_by_category(self, projects, category_keyword):
        """Filter projects by category (path contains keyword)"""
        filtered = []
        keyword_lower = category_keyword.lower()
        
        for project in projects:
            path = project.get('path_with_namespace', '').lower()
            name = project.get('name', '').lower()
            
            if keyword_lower in path or keyword_lower in name:
                filtered.append(project)
        
        return filtered

    def get_project_members(self, project_id):
        """Get all members of a project"""
        url = f"{self.gitlab_url}/api/v4/projects/{project_id}/members/all"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def branch_exists(self, project_id, branch):
        """Check if branch exists"""
        url = f"{self.gitlab_url}/api/v4/projects/{project_id}/repository/branches/{branch}"
        r = requests.get(url, headers=self.headers)
        return r.status_code == 200

    def mr_exists(self, project_id, source_branch, target_branch):
        """Check if MR already exists"""
        url = f"{self.gitlab_url}/api/v4/projects/{project_id}/merge_requests"
        params = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "state": "opened"
        }
        r = requests.get(url, headers=self.headers, params=params)
        r.raise_for_status()
        return len(r.json()) > 0

    def create_mr(self, project_id, source_branch, target_branch, title, assignee_ids):
        """Create merge request"""
        url = f"{self.gitlab_url}/api/v4/projects/{project_id}/merge_requests"
        payload = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "assignee_ids": assignee_ids
        }
        r = requests.post(url, headers=self.headers, json=payload)
        r.raise_for_status()
        return r.json()


def main():
    print("=" * 60)
    print("GitLab Merge Request Creator")
    print("=" * 60)

    if not HAS_QUESTIONARY:
        print("\n💡 Tip: Install 'questionary' for arrow‑key navigation (pip install questionary)")
    
    # SECTION - Get GitLab credentials
    gitlab_url = input("\nEnter GitLab URL (e.g., https://gitlab.com): ").strip()
    token = input("Enter your Private Token: ").strip()
    
    try:
        creator = GitLabMRCreator(gitlab_url, token)
        
        # SECTION - Verify credentials
        print("\nVerifying credentials...")
        user = creator.get_current_user()
        print(f"✓ Logged in as: {user['name']} (@{user['username']})")
        
        # SECTION - Get all projects (needed for both category filtering and selection)
        print("\nFetching all accessible projects...")
        all_projects = creator.get_all_projects()
        if not all_projects:
            print("No projects found.")
            return

        # SECTION - Category selection
        common_categories = [
            "backend", "frontend", "mobile", "devops", "data",
            "infra", "docs", "testing", "security", "other"
        ]
        # SECTION - Extract all distinct root namespaces (first part of path) as suggestions
        path_categories = set()
        for p in all_projects:
            parts = p.get('path_with_namespace', '').split('/')
            if parts:
                path_categories.add(parts[0].lower())
        # SECTION - Merge and sort, keeping common ones first
        all_categories = common_categories + sorted(path_categories - set(common_categories))
        all_categories.append("Custom keyword...")   # fallback to manual typing

        if HAS_QUESTIONARY:
            category = questionary.select(
                "Choose a project category (use arrow keys):",
                choices=all_categories
            ).ask()
            if category == "Custom keyword...":
                category = questionary.text("Enter custom category keyword:").ask()
        else:
            print("\nAvailable categories (choose one number or type a custom keyword):")
            for i, cat in enumerate(all_categories, 1):
                print(f"  {i}. {cat}")
            choice = input("Enter number or custom keyword: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(all_categories):
                selected = all_categories[int(choice)-1]
                if selected == "Custom keyword...":
                    category = input("Enter custom category keyword: ").strip()
                else:
                    category = selected
            else:
                category = choice   # treat as custom keyword
        
        # SECTION - Filter projects by category
        print(f"\nFiltering projects for category '{category}'...")
        filtered_projects = creator.filter_projects_by_category(all_projects, category)
        if not filtered_projects:
            print(f"No projects found matching '{category}'")
            return

        # SECTION - Project selection
        choices = [
            questionary.Choice(
                title=f"{p['path_with_namespace']} (ID: {p['id']})",
                value=p
            )
            for p in filtered_projects
        ] if HAS_QUESTIONARY else None

        if HAS_QUESTIONARY:
            selected = questionary.checkbox(
                "Select projects (use arrow keys & space, then Enter):",
                choices=choices
            ).ask()
            if not selected:
                print("No projects selected.")
                return
            selected_projects = selected
        else:
            print(f"\nFound {len(filtered_projects)} project(s):")
            for idx, project in enumerate(filtered_projects, 1):
                print(f"  {idx}. {project['path_with_namespace']}")
            selection = input(
                "\nEnter project numbers (comma‑separated) or 'all': "
            ).strip().lower()
            if selection == 'all':
                selected_projects = filtered_projects
            else:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                selected_projects = [
                    filtered_projects[i]
                    for i in indices if 0 <= i < len(filtered_projects)
                ]
            if not selected_projects:
                print("No valid projects selected.")
                return

        # SECTION - Get branch names (plain input – typically no list)
        source_branch = input("\nEnter source branch name: ").strip()
        target_branch = input("Enter target branch name: ").strip()

        # SECTION - Assign selection
        assignee_ids = []
        if HAS_QUESTIONARY:
            assignee_choice = questionary.select(
                "Who should be assigned to the MRs?",
                choices=[
                    "Myself",
                    "Select from project members",
                    "No assignee"
                ]
            ).ask()
        else:
            print("\nWho should be assigned to the MRs?")
            print("1. Myself")
            print("2. Select from project members")
            print("3. No assignee")
            choice = input("Choice (1-3): ").strip()
            assignee_choice = {
                '1': 'Myself', '2': 'Select from project members', '3': 'No assignee'
            }.get(choice, 'No assignee')

        if assignee_choice == "Myself":
            assignee_ids = [creator.current_user_id]
        elif assignee_choice == "Select from project members":
            # SECTION -Fetch members from the first selected project (typical use case)
            members = creator.get_project_members(selected_projects[0]['id'])
            if not members:
                print("No members found in the first project. Skipping assignee.")
            else:
                if HAS_QUESTIONARY:
                    member_choices = [
                        questionary.Choice(
                            title=f"{m['name']} (@{m['username']})",
                            value=m['id']
                        )
                        for m in members
                    ]
                    selected_id = questionary.select(
                        "Select member to assign:",
                        choices=member_choices
                    ).ask()
                    assignee_ids = [selected_id]
                else:
                    print("\nProject members:")
                    for idx, member in enumerate(members, 1):
                        print(f"  {idx}. {member['name']} (@{member['username']})")
                    member_selection = input("Select member number: ").strip()
                    if member_selection.isdigit():
                        member_idx = int(member_selection) - 1
                        if 0 <= member_idx < len(members):
                            assignee_ids = [members[member_idx]['id']]
        else:
            assignee_ids = []

        # SECTION - Create MRs
        mr_title = f"Merge {source_branch} into {target_branch}"
        print(f"\n{'=' * 60}")
        print("Creating Merge Requests...")
        print(f"{'=' * 60}")
        
        success_count = 0
        for project in selected_projects:
            project_path = project['path_with_namespace']
            project_id = project['id']
            
            print(f"\n[{project_path}]")
            
            try:
                if not creator.branch_exists(project_id, source_branch):
                    print(f"  ✗ Source branch '{source_branch}' not found")
                    continue
                
                if not creator.branch_exists(project_id, target_branch):
                    print(f"  ✗ Target branch '{target_branch}' not found")
                    continue
                
                if creator.mr_exists(project_id, source_branch, target_branch):
                    print("  ⚠ MR already exists")
                    continue
                
                mr = creator.create_mr(project_id, source_branch, target_branch, mr_title, assignee_ids)
                print(f"  ✓ MR created: {mr['web_url']}")
                success_count += 1
                
            except requests.exceptions.HTTPError as e:
                print(f"  ✗ Failed: {e.response.status_code} - {e.response.text[:100]}")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
        
        print(f"\n{'=' * 60}")
        print(f"Summary: {success_count}/{len(selected_projects)} MRs created successfully")
        print(f"{'=' * 60}")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ API Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    main()