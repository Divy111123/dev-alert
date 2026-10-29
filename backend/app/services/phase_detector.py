from typing import Optional, Dict, Any, Tuple

VALID_PHASES = {
    "development": "Development",
    "testing": "Testing",
    "staging": "Staging",
    "build": "Build",
    "deployment": "Deployment",
    "production": "Production",
}


def detect_phase(
    explicit_phase: Optional[str] = None,
    environment: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None
) -> Tuple[str, str]:
    """
    Determines the development phase according to strict priority rules.
    Returns a tuple of (Phase, Reason/Source).
    """
    metadata = metadata or {}
    
    # Priority 1: Explicit, validated phase metadata supplied by the integration
    if explicit_phase:
        normalized = explicit_phase.strip().lower()
        if normalized in VALID_PHASES:
            return VALID_PHASES[normalized], "explicit_integration_metadata"

    # Priority 2: Trusted CI/CD job or deployment metadata
    ci_stage = metadata.get("stage") or metadata.get("job_name") or metadata.get("step") or ""
    ci_stage_lower = str(ci_stage).lower()
    
    if any(keyword in ci_stage_lower for keyword in ["deploy", "release", "cd", "k8s-rollout", "helm"]):
        return "Deployment", "trusted_cicd_metadata"
    elif any(keyword in ci_stage_lower for keyword in ["build", "compile", "docker-build", "package", "bundle"]):
        return "Build", "trusted_cicd_metadata"
    elif any(keyword in ci_stage_lower for keyword in ["test", "pytest", "unit-test", "e2e", "jest", "cypress"]):
        return "Testing", "trusted_cicd_metadata"

    # Check CI branch metadata
    branch = metadata.get("branch") or metadata.get("git_ref") or ""
    branch_lower = str(branch).lower()
    if branch_lower in ["main", "master", "prod", "production"]:
        # If CI/CD triggered on main, usually staging or deployment
        if "staging" in str(environment).lower():
            return "Staging", "trusted_cicd_metadata"
    elif any(feature_prefix in branch_lower for feature_prefix in ["feature/", "feat/", "fix/", "dev", "develop"]):
        return "Development", "trusted_cicd_metadata"

    # Priority 3: Configured project and environment rules
    if environment:
        env_lower = environment.strip().lower()
        if env_lower in ["production", "prod"]:
            return "Production", "environment_mapping"
        elif env_lower in ["staging", "stage", "uat", "preprod"]:
            return "Staging", "environment_mapping"
        elif env_lower in ["testing", "test", "qa"]:
            return "Testing", "environment_mapping"
        elif env_lower in ["development", "dev", "local"]:
            return "Development", "environment_mapping"

    # Priority 4: Clearly marked inferred classification when sufficient evidence exists
    if source == "jenkins" or source == "github-actions":
        return "Build", "inferred_ci_source"

    # Fallback
    return "Unknown", "unclassified"

