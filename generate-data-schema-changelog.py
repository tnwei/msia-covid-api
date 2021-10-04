import tempfile
import git
import pandas as pd
from pathlib import Path
import difflib
from typing import Dict, List, Optional
from tqdm import tqdm
import argparse


def return_moh_schema(filepath: Path) -> Dict:
    schema = {}
    for i in filepath.glob("epidemic/**/*.csv"):
        df = pd.read_csv(i)
        schema[i.name] = list(df.columns)
    for i in filepath.glob("mysejahtera/**/*.csv"):
        df = pd.read_csv(i)
        schema[i.name] = list(df.columns)
    return schema


def return_citf_schema(filepath: Path) -> Dict:
    schema = {}
    for i in filepath.glob("vaccination/**/*.csv"):
        df = pd.read_csv(i)
        schema[i.name] = list(df.columns)

    for i in filepath.glob("registration/**/*.csv"):
        df = pd.read_csv(i)
        schema[i.name] = list(df.columns)

    return schema


def schema2text(schema: Dict) -> List:
    lines = []
    for i, j in schema.items():
        for col in j:
            lines.append(f"{i}: {col}\n")

    lines.sort()

    return lines


def strf_diff_output(diffoutput: List) -> List:
    if len(diffoutput) == 0:
        return []
    else:
        # Skip first two lines in diff
        pretty_output = [i for i in diffoutput[2:]]

        # Skip diff comments
        pretty_output = [i for i in pretty_output if not i.startswith("@")]

    return pretty_output


def main(repo: str, outfile: Optional[str]):
    """
    Output list of changes in data schema from MOH and CITF repo.
    Iterates over all commits in history and finds change in data columns.

    Usage
    -----
    `python generate-data-schema-changelog.py moh` or
    `python generate-data-schema-changelog.py citf`

    Args
    ----
    repo: `moh` or `citf` repo
    outputfp: output filepath, defaults to <repo>-schema-changes.txt

    Return
    ------
    None
    """
    assert repo in ["moh", "citf"], f"{repo} needs to be 'moh' or 'citf'"
    if outfile is None:
        outfile = repo + "-schema-changes.txt"

    if repo == "moh":
        repo_url = "https://github.com/MoH-Malaysia/covid19-public"
        return_schema = return_moh_schema
    elif repo == "citf":
        repo_url = "https://github.com/CITF-Malaysia/citf-public"
        return_schema = return_citf_schema

    # Setup data schema
    dirobj = tempfile.TemporaryDirectory()
    dirfp = Path(dirobj.name)

    # Clone
    repo_obj = git.Repo.clone_from(repo_url, dirfp)

    # Retrieve between two commits
    # commits = [i for i in repo_obj.iter_commits("b70cdc..HEAD")]

    # Retrieve all commits
    commits = [i for i in repo_obj.iter_commits(all=True)]
    commits.reverse()  # Because commits are listed last first

    print(f"Num commits total: {len(commits)}")
    num_schema_changes = 0

    # Setup header block
    title = f"Data schema changes in {repo.upper()} repo"
    underline = "=" * len(title)
    body = (
        "Format is <+ or -><filename>: <columnname>. \n"
        + "'+' means added column, '-' means removed column.\n"
        + f"Data source: {repo_url}\n"
        + "Generated with: https://github.com/tnwei/msia-covid-api/blob/master/generate-data-schema-changelog.py\n"
    )
    header_block = title + "\n" + underline + "\n" + body + "\n\n"

    with open(outfile, "w") as f:
        # Write header block
        f.write(header_block)

        # Loop across the commits
        for i in tqdm(range(len(commits) - 1)):
            repo_obj.git.checkout(commits[i])
            prev_repo_schema = return_schema(dirfp)
            repo_obj.git.checkout(commits[i + 1])
            new_repo_schema = return_schema(dirfp)
            diffs = strf_diff_output(
                list(
                    difflib.unified_diff(
                        schema2text(prev_repo_schema),
                        schema2text(new_repo_schema),
                        n=0,  # remove all context lines
                    )
                )
            )

            if len(diffs) == 0:
                pass
            else:
                num_schema_changes += 1
                negatives = [i for i in diffs if i.startswith("-")]
                positives = [i for i in diffs if i.startswith("+")]

                title_str = f"Changes in commit {commits[i+1].hexsha[:6]} on ({commits[i+1].committed_datetime})"
                f.write(title_str + "\n")
                f.write("-" * len(title_str) + "\n")
                f.write("".join(positives) + "\n")
                f.write("".join(negatives) + "\n")
    print(f"{num_schema_changes} schema changes found, written to {outfile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Output list of changes in data schema from MOH and CITF repo.
    Iterates over all commits in history and finds change in data columns."""
    )
    parser.add_argument(
        "repo",
        type=str,
        help="Repo to check all schema changes to date, `moh` or `citf`",
    )
    parser.add_argument(
        "--outfile",
        type=str,
        help="Output file name, defaults to <repo>-schema-changes.txt",
    )
    args = parser.parse_args()

    main(args.repo, args.outfile)
