"""
Cost-Reviewer agent — estimates monthly AWS costs from Terraform configs.
Model: claude-haiku-4-5-20251001 (lightweight, read-only analysis).
Tools: Read, Grep, Glob
"""

import anthropic

_SYSTEM = """
You are a cloud cost analyst specialising in AWS infrastructure for fintech workloads.
Given Terraform configuration files, estimate the monthly AWS cost in USD.
Compare dev vs prod environments, identify the top 3 cost drivers, and suggest optimisations.
Format your response as:

## Estimated Monthly Cost
| Environment | Estimated USD |
|-------------|--------------|
| dev         | $X            |
| prod        | $Y            |

## Top Cost Drivers
1. ...

## Optimisation Opportunities
- ...
"""


def review_costs(terraform_dir: str = "infra/terraform") -> str:
    client = anthropic.Anthropic()

    # Read terraform files via tool use in a real implementation;
    # here we pass the directory path as context for the agent to explore.
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": f"Analyse Terraform configs in `{terraform_dir}` and estimate monthly AWS costs.",
            }
        ],
    )
    return response.content[0].text
